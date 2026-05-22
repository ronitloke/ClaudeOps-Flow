from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.db.database import create_tables, get_db
from app.repositories.approval_repository import (
    get_pending_approval_logs,
    serialize_pending_approval,
)
from app.repositories.benchmark_repository import save_benchmark_run
from app.repositories.triage_log_repository import (
    get_log_detail_by_request_id,
    get_recent_logs,
    save_error_log,
    save_success_log,
    save_triage_feedback,
    update_automation_result,
)
from app.repositories.policy_audit_repository import get_recent_outbound_action_audits
from app.schemas.approval import ApprovalActionRequest
from app.schemas.benchmark import BenchmarkRunRequest
from app.services.benchmark_accuracy_service import get_correction_aware_benchmark_summary
from app.schemas.triage import TicketTriageRequest, TriageFeedbackRequest
from app.services.approval_service import (approve_pending_request,reject_pending_request)
from app.services.automation_dispatcher import run_post_triage_automation
from app.services.benchmark_service import run_ticket_benchmark
from app.services.observability_service import get_observability_summary
from app.services.automation_contract import build_sample_outbound_contract
from app.services.triage_service import (TriageExecutionError,get_active_model_name,get_triage_catalog,run_triage)
from app.db.schema_guard import ensure_runtime_schema

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def startup_event():
    create_tables()
    ensure_runtime_schema()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "provider": settings.llm_provider,
    }


@app.get("/config")
def config_preview():
    return {
        "raw_data_dir": settings.raw_data_dir,
        "processed_data_dir": settings.processed_data_dir,
        "provider": settings.llm_provider,
        "groq_model": settings.groq_model,
        "gemini_model": settings.gemini_model,
        "claude_model": settings.claude_model,
        "database_url": settings.database_url,
        "llm_max_retries": settings.llm_max_retries,
        "llm_retry_delay_seconds": settings.llm_retry_delay_seconds,
        "enable_automation_hooks": settings.enable_automation_hooks,
        "slack_webhook_configured": bool(settings.slack_webhook_url.strip()),
        "generic_webhook_configured": bool(settings.generic_webhook_url.strip()),
        "zapier_hook_enabled": settings.enable_zapier_hook,
        "zapier_webhook_configured": bool(settings.zapier_webhook_url.strip()),
        "make_hook_enabled": settings.enable_make_hook,
        "make_webhook_configured": bool(settings.make_webhook_url.strip()),
    }


@app.get("/triage/catalog")
def triage_catalog():
    try:
        return get_triage_catalog()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/triage/ticket")
def triage_ticket_endpoint(
    payload: TicketTriageRequest,
    db: Session = Depends(get_db),
):
    try:
        result = run_triage(payload)

        approval = result.get("approval") or {}
        automation_decision = result.get("automation_decision") or {}

        log = save_success_log(
            db=db,
            payload=payload,
            triage_response=result["triage_response"],
            raw_llm_output=result["raw_llm_output"],
            provider=result["provider"],
            model_name=result["model_name"],
            latency_ms=result["latency_ms"],
            retry_count=result["retry_count"],
            automation_decision=automation_decision,
            approval=approval,
            automation_enabled=settings.enable_automation_hooks,
            observability=result.get("observability"),
        )

        if approval.get("required"):
            automation_result = {
                "enabled": settings.enable_automation_hooks,
                "automation_ready": False,
                "decision": automation_decision,
                "approval_required": True,
                "approval_status": approval.get("status", "pending"),
                "approval_reason": approval.get("reason"),
                "automation_executed": False,
                "note": "Awaiting human approval before downstream automation.",
                "slack_delivery": None,
                "webhook_delivery": None,
                "zapier_delivery": None,
                "make_delivery": None,
            }
        else:
            automation_result = run_post_triage_automation(
                payload=payload,
                triage_response=result["triage_response"],
                request_id=log.request_id,
                log_id=log.id,
            )
            automation_result["approval_required"] = False
            automation_result["approval_status"] = approval.get("status", "not_required")
            automation_result["approval_reason"] = approval.get("reason")
            automation_result["automation_executed"] = True

        update_automation_result(
            db=db,
            log_id=log.id,
            automation_result=automation_result,
        )

        response_body = result["triage_response"].model_dump()
        response_body["log_id"] = log.id
        response_body["request_id"] = log.request_id
        response_body["latency_ms"] = result["latency_ms"]
        response_body["retry_count"] = result["retry_count"]
        response_body["had_retry"] = result["had_retry"]
        response_body["automation"] = automation_result
        response_body["approval"] = approval
        response_body["automation_decision"] = automation_decision
        response_body["deterministic_route"] = result.get("deterministic_route")
        response_body["observability"] = result.get("observability")
        return response_body

    except TriageExecutionError as exc:
        try:
            log = save_error_log(
                db=db,
                payload=payload,
                error_message=str(exc),
                provider=settings.llm_provider,
                model_name=get_active_model_name(),
                latency_ms=exc.latency_ms,
                retry_count=exc.retry_count,
                error_type=exc.error_type,
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "message": str(exc),
                    "request_id": log.request_id,
                    "latency_ms": exc.latency_ms,
                    "retry_count": exc.retry_count,
                    "error_type": exc.error_type,
                },
            )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail=str(exc))

    except Exception as exc:
        try:
            save_error_log(
                db=db,
                payload=payload,
                error_message=str(exc),
                provider=settings.llm_provider,
                model_name=get_active_model_name(),
                latency_ms=None,
                retry_count=0,
                error_type=exc.__class__.__name__,
            )
        except Exception:
            pass

        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/benchmark/run")
def benchmark_run(
    payload: BenchmarkRunRequest,
    db: Session = Depends(get_db),
):
    try:
        result = run_ticket_benchmark(payload)
        saved = save_benchmark_run(
            db=db,
            result=result,
            run_config=payload.model_dump(),
        )
        result["benchmark_run_id"] = saved.id
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/observability/summary")
def observability_summary(
    hours: int = Query(default=24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    try:
        return get_observability_summary(db=db, hours=hours)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/benchmark/correction-aware-summary")
def benchmark_correction_aware_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    try:
        return get_correction_aware_benchmark_summary(
            db=db,
            days=days,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/contracts/outbound-automation/v1")
def get_outbound_automation_contract_v1():
    return {
        "contract_name": "ClaudeOps Flow Outbound Automation Contract",
        "contract_version": "v1",
        "schema_name": "claudeops.outbound_automation",
        "description": (
            "Stable JSON contract for Zapier, Make, Slack, webhooks, "
            "and future workflow integrations."
        ),
        "recommended_mapping": {
            "gmail_subject": "automation_contract.downstream_actions.send_email.subject",
            "gmail_body": "automation_contract.downstream_actions.send_email.body",
            "trello_card_name": "automation_contract.downstream_actions.create_trello_card.card_name",
            "trello_card_description": "automation_contract.downstream_actions.create_trello_card.card_description",
            "sheet_row": "automation_contract.downstream_actions.append_google_sheet_row",
            "slack_text": "automation_contract.downstream_actions.send_slack_alert.text",
            "policy_flags": "automation_contract.policy_flags",
        },
        "sample_contract": build_sample_outbound_contract(),
    }

@app.get("/policy/audit/recent")
def policy_audit_recent(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    try:
        return {
            "items": get_recent_outbound_action_audits(
                db=db,
                limit=limit,
            )
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/triage/logs/recent")
def recent_triage_logs(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        return {"items": get_recent_logs(db, limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/triage/logs/{request_id}")
def triage_log_detail(
    request_id: str,
    db: Session = Depends(get_db),
):
    try:
        detail = get_log_detail_by_request_id(db, request_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Log not found")
        return detail
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/triage/logs/{request_id}/feedback")
def triage_feedback(
    request_id: str,
    payload: TriageFeedbackRequest,
    db: Session = Depends(get_db),
):
    try:
        result = save_triage_feedback(
            db=db,
            request_id=request_id,
            queue_correct=payload.queue_correct,
            corrected_queue=payload.corrected_queue,
            priority_correct=payload.priority_correct,
            corrected_priority=payload.corrected_priority,
            intent_correct=payload.intent_correct,
            corrected_intent=payload.corrected_intent,
            recommended_action_correct=payload.recommended_action_correct,
            corrected_recommended_action=payload.corrected_recommended_action,
            corrected_by=payload.corrected_by,
            correction_source=payload.correction_source,
            notes=payload.notes,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Log not found")

        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/approvals/pending")
def approvals_pending(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    try:
        logs = get_pending_approval_logs(db, limit=limit)
        return {"items": [serialize_pending_approval(item) for item in logs]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/approvals/{request_id}/approve")
def approve_request(
    request_id: str,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    try:
        return approve_pending_request(
            db=db,
            request_id=request_id,
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/approvals/{request_id}/reject")
def reject_request(
    request_id: str,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
):
    try:
        return reject_pending_request(
            db=db,
            request_id=request_id,
            actor=payload.actor,
            actor_role=payload.actor_role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))