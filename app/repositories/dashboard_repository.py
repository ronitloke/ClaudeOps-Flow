from datetime import date, datetime, time, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.triage_log import TriageLog


def get_filter_options(db: Session) -> dict:
    rows = db.execute(
        select(
            TriageLog.status,
            TriageLog.predicted_queue,
            TriageLog.predicted_priority,
        )
    ).all()

    min_max = db.execute(
        select(
            func.min(TriageLog.created_at),
            func.max(TriageLog.created_at),
        )
    ).one()

    min_created_at = min_max[0].date() if min_max[0] else None
    max_created_at = min_max[1].date() if min_max[1] else None

    statuses = sorted({row[0] for row in rows if row[0]})
    queues = sorted({row[1] for row in rows if row[1]})
    priorities = sorted({row[2] for row in rows if row[2]})

    return {
        "statuses": statuses,
        "queues": queues,
        "priorities": priorities,
        "min_created_at": min_created_at,
        "max_created_at": max_created_at,
    }


def get_filtered_logs(
    db: Session,
    status: str | None = None,
    queue: str | None = None,
    priority: str | None = None,
    search_text: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    stmt = select(TriageLog)

    if status and status != "All":
        stmt = stmt.where(TriageLog.status == status)

    if queue and queue != "All":
        stmt = stmt.where(TriageLog.predicted_queue == queue)

    if priority and priority != "All":
        stmt = stmt.where(TriageLog.predicted_priority == priority)

    if search_text and search_text.strip():
        pattern = f"%{search_text.strip()}%"
        stmt = stmt.where(
            or_(
                TriageLog.request_id.ilike(pattern),
                TriageLog.subject.ilike(pattern),
            )
        )

    if start_date:
        start_dt = datetime.combine(start_date, time.min)
        stmt = stmt.where(TriageLog.created_at >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min)
        stmt = stmt.where(TriageLog.created_at < end_dt)

    stmt = (
        stmt
        .order_by(TriageLog.created_at.desc())
        .offset(max(offset, 0))
        .limit(limit)
    )
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
            "sla_risk": row.sla_risk,
            "confidence": row.confidence,
            "latency_ms": row.latency_ms,
            "retry_count": row.retry_count,
            "had_retry": row.had_retry,
            "error_type": row.error_type,
            "automation_ready": row.automation_ready,
            "automation_should_escalate": row.automation_should_escalate,
            "automation_target_team": row.automation_target_team,
            "automation_urgency_level": row.automation_urgency_level,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


def get_log_detail(db: Session, request_id: str) -> dict | None:
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
        "created_at": row.created_at.isoformat() if row.created_at else None,
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
        "structured_fields": row.structured_fields,
        "raw_request": row.raw_request,
        "raw_llm_output": row.raw_llm_output,
        "error_message": row.error_message,
    }