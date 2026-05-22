from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.approval_repository import get_log_by_request_id
from app.services.automation_service import execute_automation_hooks


def _ticket_from_log(log) -> dict[str, Any]:
    if isinstance(log.raw_request, dict) and log.raw_request:
        return log.raw_request

    return {
        "subject": log.subject,
        "body": log.body,
        "language_hint": log.language_hint,
        "business_type_hint": log.business_type_hint,
        "include_draft_response": log.include_draft_response,
    }


def _triage_from_log(log) -> dict[str, Any]:
    if isinstance(log.raw_llm_output, dict) and log.raw_llm_output:
        return log.raw_llm_output

    return {
        "summary": log.summary,
        "detected_language": log.detected_language,
        "predicted_type": log.predicted_type,
        "predicted_queue": log.predicted_queue,
        "predicted_priority": log.predicted_priority,
        "predicted_business_type": log.predicted_business_type,
        "likely_intent": log.likely_intent,
        "urgency_reason": log.urgency_reason,
        "sla_risk": log.sla_risk,
        "needs_human_review": log.needs_human_review,
        "recommended_action": log.recommended_action,
        "draft_response": log.draft_response,
        "structured_fields": log.structured_fields or {},
        "confidence": log.confidence,
    }


def approve_pending_request(
    db: Session,
    request_id: str,
    actor: str,
    actor_role: str = "admin",
) -> dict:
    log = get_log_by_request_id(db, request_id)

    if not log:
        raise ValueError("Request not found.")

    if not log.approval_required:
        raise ValueError("This request does not require approval.")

    if log.approval_status != "pending":
        raise ValueError(f"Approval is already in '{log.approval_status}' state.")

    ticket = _ticket_from_log(log)
    triage_result = _triage_from_log(log)
    automation_decision = log.automation_decision or {}

    now = datetime.now(timezone.utc)

    automation_result = execute_automation_hooks(
        request_id=log.request_id,
        log_id=log.id,
        ticket=ticket,
        triage_result=triage_result,
        automation_decision=automation_decision,
        approved_at=now.isoformat(),
        approved_by=actor,
        approval_status="approved",
        actor_role=actor_role,
    )

    log.approval_status = "approved"
    log.approved_by = actor
    log.approved_at = now

    log.automation_enabled = True
    log.automation_ready = True
    log.automation_executed = True
    log.automation_executed_at = now

    log.automation_slack_delivery = automation_result.get("slack_delivery")
    log.automation_webhook_delivery = automation_result.get("webhook_delivery")
    log.automation_zapier_delivery = automation_result.get("zapier_delivery")
    log.automation_make_delivery = automation_result.get("make_delivery")
    log.automation_error = automation_result.get("error") or automation_result.get("note")

    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "request_id": log.request_id,
        "approval_status": log.approval_status,
        "automation_executed": log.automation_executed,
        "policy_decisions": automation_result.get("policy_decisions"),
        "message": "Approval completed and downstream automation evaluated by policy engine.",
    }


def reject_pending_request(
    db: Session,
    request_id: str,
    actor: str,
    actor_role: str = "admin",
) -> dict:
    log = get_log_by_request_id(db, request_id)

    if not log:
        raise ValueError("Request not found.")

    if not log.approval_required:
        raise ValueError("This request does not require approval.")

    if log.approval_status != "pending":
        raise ValueError(f"Approval is already in '{log.approval_status}' state.")

    now = datetime.now(timezone.utc)

    log.approval_status = "rejected"
    log.rejected_by = actor
    log.rejected_at = now

    log.automation_enabled = True
    log.automation_ready = False
    log.automation_executed = False
    log.automation_executed_at = None
    log.automation_error = (
        f"Rejected by human approver before downstream automation. "
        f"Actor role: {actor_role}"
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "request_id": log.request_id,
        "approval_status": log.approval_status,
        "automation_executed": False,
        "message": "Approval rejected. No downstream automation was executed.",
    }