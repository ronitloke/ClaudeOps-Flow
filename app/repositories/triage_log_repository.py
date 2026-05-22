from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.triage_log import TriageLog
from app.schemas.triage import TicketTriageRequest, TicketTriageResponse


def _safe_model_dump(value: Any) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {"value": str(value)}


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def save_success_log(
    db: Session,
    payload: TicketTriageRequest,
    triage_response: TicketTriageResponse,
    raw_llm_output: dict | str | None,
    provider: str,
    model_name: str,
    latency_ms: float | None = None,
    retry_count: int = 0,
    automation_decision: dict | None = None,
    approval: dict | None = None,
    automation_enabled: bool = False,
    observability: dict | None = None,
) -> TriageLog:
    automation_decision = automation_decision or {}
    approval = approval or {}

    observability = observability or {}
    trace = observability.get("trace") or {}

    structured_fields = _safe_model_dump(triage_response.structured_fields)
    raw_request = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)

    raw_llm_output_dict: dict | None
    if isinstance(raw_llm_output, dict):
        raw_llm_output_dict = raw_llm_output
    elif raw_llm_output is None:
        raw_llm_output_dict = None
    else:
        raw_llm_output_dict = {"raw_text": str(raw_llm_output)}

    log = TriageLog(
        request_id=str(uuid4()),
        status="success",
        provider=provider,
        model_name=model_name,
        subject=payload.subject,
        body=payload.body,
        language_hint=payload.language_hint,
        business_type_hint=payload.business_type_hint,
        include_draft_response=payload.include_draft_response,
        summary=triage_response.summary,
        detected_language=triage_response.detected_language,
        predicted_type=triage_response.predicted_type,
        predicted_queue=triage_response.predicted_queue,
        predicted_priority=triage_response.predicted_priority,
        predicted_business_type=triage_response.predicted_business_type,
        likely_intent=triage_response.likely_intent,
        urgency_reason=triage_response.urgency_reason,
        sla_risk=triage_response.sla_risk,
        needs_human_review=triage_response.needs_human_review,
        recommended_action=triage_response.recommended_action,
        draft_response=triage_response.draft_response,
        confidence=triage_response.confidence,
        latency_ms=latency_ms,
        retry_count=retry_count,
        had_retry=retry_count > 0,
        error_type=None,
        automation_enabled=automation_enabled,
        automation_ready=False,
        automation_should_escalate=automation_decision.get("should_escalate"),
        automation_target_team=automation_decision.get("target_team"),
        automation_urgency_level=automation_decision.get("urgency_level"),
        automation_decision=automation_decision,
        automation_slack_delivery=None,
        automation_webhook_delivery=None,
        automation_zapier_delivery=None,
        automation_make_delivery=None,
        automation_error=None,
        approval_required=bool(approval.get("required", False)),
        approval_status=approval.get("status", "not_required"),
        approval_reason=approval.get("reason"),
        approved_by=None,
        approved_at=None,
        rejected_by=None,
        rejected_at=None,
        automation_executed=bool(approval.get("automation_executed", False)),
        automation_executed_at=None,
        structured_fields=structured_fields,
        raw_request=raw_request,
        raw_llm_output=raw_llm_output_dict,

        prompt_version=observability.get("prompt_version"),
        model_version=observability.get("model_version"),
        input_tokens=observability.get("input_tokens"),
        output_tokens=observability.get("output_tokens"),
        total_tokens=observability.get("total_tokens"),
        estimated_cost_usd=observability.get("estimated_cost_usd"),
        trace_json=trace,

        user_queue_correct=None,
        corrected_queue=None,
        user_feedback_notes=None,
        feedback_at=None,

        error_message=None,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def save_error_log(
    db: Session,
    payload: TicketTriageRequest,
    error_message: str,
    provider: str,
    model_name: str,
    latency_ms: float | None = None,
    retry_count: int = 0,
    error_type: str | None = None,
) -> TriageLog:
    raw_request = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)

    log = TriageLog(
        request_id=str(uuid4()),
        status="error",
        provider=provider,
        model_name=model_name,
        subject=payload.subject,
        body=payload.body,
        language_hint=payload.language_hint,
        business_type_hint=payload.business_type_hint,
        include_draft_response=payload.include_draft_response,
        summary=None,
        detected_language=None,
        predicted_type=None,
        predicted_queue=None,
        predicted_priority=None,
        predicted_business_type=None,
        likely_intent=None,
        urgency_reason=None,
        sla_risk=None,
        needs_human_review=None,
        recommended_action=None,
        draft_response=None,
        confidence=None,
        latency_ms=latency_ms,
        retry_count=retry_count,
        had_retry=retry_count > 0,
        error_type=error_type,
        automation_enabled=False,
        automation_ready=False,
        automation_should_escalate=None,
        automation_target_team=None,
        automation_urgency_level=None,
        automation_decision=None,
        automation_slack_delivery=None,
        automation_webhook_delivery=None,
        automation_zapier_delivery=None,
        automation_make_delivery=None,
        automation_error=None,
        approval_required=False,
        approval_status="not_required",
        approval_reason=None,
        approved_by=None,
        approved_at=None,
        rejected_by=None,
        rejected_at=None,
        automation_executed=False,
        automation_executed_at=None,
        structured_fields=None,
        raw_request=raw_request,
        raw_llm_output=None,
        error_message=error_message,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_automation_result(
    db: Session,
    log_id: int,
    automation_result: dict,
) -> TriageLog | None:
    stmt = select(TriageLog).where(TriageLog.id == log_id)
    row = db.execute(stmt).scalar_one_or_none()

    if not row:
        return None

    decision = automation_result.get("decision") or {}

    row.automation_enabled = bool(automation_result.get("enabled", False))
    row.automation_ready = bool(automation_result.get("automation_ready", False))
    row.automation_should_escalate = decision.get("should_escalate")
    row.automation_target_team = decision.get("target_team")
    row.automation_urgency_level = decision.get("urgency_level")
    row.automation_decision = decision
    row.automation_slack_delivery = automation_result.get("slack_delivery")
    row.automation_webhook_delivery = automation_result.get("webhook_delivery")
    row.automation_zapier_delivery = automation_result.get("zapier_delivery")
    row.automation_make_delivery = automation_result.get("make_delivery")
    row.automation_error = automation_result.get("error") or automation_result.get("note")

    if "approval_required" in automation_result:
        row.approval_required = bool(automation_result.get("approval_required"))
    if "approval_status" in automation_result:
        row.approval_status = automation_result.get("approval_status") or row.approval_status
    if "approval_reason" in automation_result:
        row.approval_reason = automation_result.get("approval_reason")

    if "automation_executed" in automation_result:
        row.automation_executed = bool(automation_result.get("automation_executed"))

    db.commit()
    db.refresh(row)
    return row


def get_recent_logs(db: Session, limit: int = 10) -> list[dict]:
    stmt = select(TriageLog).order_by(desc(TriageLog.created_at)).limit(limit)
    rows = db.execute(stmt).scalars().all()

    return [
        {
            "id": row.id,
            "request_id": row.request_id,
            "status": row.status,
            "provider": row.provider,
            "model_name": row.model_name,
            "subject": row.subject,
            "predicted_queue": row.predicted_queue,
            "predicted_priority": row.predicted_priority,
            "predicted_type": row.predicted_type,
            "likely_intent": row.likely_intent,
            "confidence": row.confidence,
            "sla_risk": row.sla_risk,
            "latency_ms": row.latency_ms,
            "retry_count": row.retry_count,
            "had_retry": row.had_retry,
            "error_type": row.error_type,
            "automation_ready": row.automation_ready,
            "automation_should_escalate": row.automation_should_escalate,
            "automation_target_team": row.automation_target_team,
            "automation_urgency_level": row.automation_urgency_level,
            "approval_required": row.approval_required,
            "approval_status": row.approval_status,
            "automation_executed": row.automation_executed,
            "created_at": _iso(row.created_at),
        }
        for row in rows
    ]


def get_log_detail_by_request_id(db: Session, request_id: str) -> dict | None:
    stmt = select(TriageLog).where(TriageLog.request_id == request_id)
    row = db.execute(stmt).scalar_one_or_none()

    if not row:
        return None

    return {
        "id": row.id,
        "request_id": row.request_id,
        "status": row.status,
        "provider": row.provider,
        "model_name": row.model_name,
        "subject": row.subject,
        "body": row.body,
        "language_hint": row.language_hint,
        "business_type_hint": row.business_type_hint,
        "include_draft_response": row.include_draft_response,
        "summary": row.summary,
        "detected_language": row.detected_language,
        "predicted_type": row.predicted_type,
        "predicted_queue": row.predicted_queue,
        "predicted_priority": row.predicted_priority,
        "predicted_business_type": row.predicted_business_type,
        "likely_intent": row.likely_intent,
        "urgency_reason": row.urgency_reason,
        "sla_risk": row.sla_risk,
        "needs_human_review": row.needs_human_review,
        "recommended_action": row.recommended_action,
        "draft_response": row.draft_response,
        "confidence": row.confidence,
        "latency_ms": row.latency_ms,
        "retry_count": row.retry_count,
        "had_retry": row.had_retry,
        "error_type": row.error_type,
        "automation_enabled": row.automation_enabled,
        "automation_ready": row.automation_ready,
        "automation_should_escalate": row.automation_should_escalate,
        "automation_target_team": row.automation_target_team,
        "automation_urgency_level": row.automation_urgency_level,
        "automation_decision": row.automation_decision,
        "automation_slack_delivery": row.automation_slack_delivery,
        "automation_webhook_delivery": row.automation_webhook_delivery,
        "automation_zapier_delivery": row.automation_zapier_delivery,
        "automation_make_delivery": row.automation_make_delivery,
        "automation_error": row.automation_error,
        "approval_required": row.approval_required,
        "approval_status": row.approval_status,
        "approval_reason": row.approval_reason,
        "approved_by": row.approved_by,
        "approved_at": _iso(row.approved_at),
        "rejected_by": row.rejected_by,
        "rejected_at": _iso(row.rejected_at),
        "automation_executed": row.automation_executed,
        "automation_executed_at": _iso(row.automation_executed_at),
        "structured_fields": row.structured_fields,
        "raw_request": row.raw_request,
        "raw_llm_output": row.raw_llm_output,
        "error_message": row.error_message,
        "created_at": _iso(row.created_at),
    }

def save_triage_feedback(
    db: Session,
    request_id: str,
    queue_correct: bool,
    corrected_queue: str | None = None,
    priority_correct: bool = True,
    corrected_priority: str | None = None,
    intent_correct: bool = True,
    corrected_intent: str | None = None,
    recommended_action_correct: bool = True,
    corrected_recommended_action: str | None = None,
    corrected_by: str | None = None,
    correction_source: str | None = "human_review",
    notes: str | None = None,
) -> dict | None:
    stmt = select(TriageLog).where(TriageLog.request_id == request_id)
    row = db.execute(stmt).scalar_one_or_none()

    if not row:
        return None

    correction_json = {
        "raw_prediction": {
            "queue": row.predicted_queue,
            "priority": row.predicted_priority,
            "intent": row.likely_intent,
            "recommended_action": row.recommended_action,
        },
        "corrected_prediction": {
            "queue": corrected_queue if not queue_correct else row.predicted_queue,
            "priority": corrected_priority if not priority_correct else row.predicted_priority,
            "intent": corrected_intent if not intent_correct else row.likely_intent,
            "recommended_action": (
                corrected_recommended_action
                if not recommended_action_correct
                else row.recommended_action
            ),
        },
        "correctness": {
            "queue_correct": queue_correct,
            "priority_correct": priority_correct,
            "intent_correct": intent_correct,
            "recommended_action_correct": recommended_action_correct,
        },
        "notes": notes,
    }

    row.user_queue_correct = queue_correct
    row.corrected_queue = corrected_queue if not queue_correct else None

    row.user_priority_correct = priority_correct
    row.corrected_priority = corrected_priority if not priority_correct else None

    row.user_intent_correct = intent_correct
    row.corrected_intent = corrected_intent if not intent_correct else None

    row.user_recommended_action_correct = recommended_action_correct
    row.corrected_recommended_action = (
        corrected_recommended_action if not recommended_action_correct else None
    )

    row.user_feedback_notes = notes
    row.correction_applied_by = corrected_by
    row.correction_source = correction_source or "human_review"
    row.correction_json = correction_json
    row.feedback_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(row)

    return {
        "request_id": row.request_id,
        "feedback_at": _iso(row.feedback_at),
        "correction_applied_by": row.correction_applied_by,
        "correction_source": row.correction_source,
        "raw_prediction": correction_json["raw_prediction"],
        "corrected_prediction": correction_json["corrected_prediction"],
        "correctness": correction_json["correctness"],
        "notes": row.user_feedback_notes,
    }