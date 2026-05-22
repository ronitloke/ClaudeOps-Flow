from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.triage_log import TriageLog


def get_pending_approval_logs(db: Session, limit: int = 50) -> list[TriageLog]:
    return (
        db.query(TriageLog)
        .filter(
            TriageLog.approval_required.is_(True),
            TriageLog.approval_status == "pending",
        )
        .order_by(desc(TriageLog.created_at))
        .limit(limit)
        .all()
    )


def get_log_by_request_id(db: Session, request_id: str) -> TriageLog | None:
    return db.query(TriageLog).filter(TriageLog.request_id == request_id).first()


def serialize_pending_approval(log: TriageLog) -> dict:
    return {
        "request_id": log.request_id,
        "subject": log.subject,
        "summary": log.summary,
        "predicted_queue": log.predicted_queue,
        "predicted_priority": log.predicted_priority,
        "likely_intent": log.likely_intent,
        "sla_risk": log.sla_risk,
        "needs_human_review": log.needs_human_review,
        "approval_reason": log.approval_reason,
        "automation_target_team": log.automation_target_team,
        "automation_urgency_level": log.automation_urgency_level,
        "created_at": log.created_at,
    }