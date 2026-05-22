from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outbound_action_audit import OutboundActionAudit


def save_outbound_action_audit(
    db: Session,
    request_id: str,
    log_id: int | None,
    actor: str | None,
    actor_role: str | None,
    action_key: str,
    channel: str | None,
    decision: str,
    policy_rule: str | None,
    reason: str | None,
    queue: str | None,
    priority: str | None,
    delivery_json: dict[str, Any] | None,
) -> OutboundActionAudit:
    row = OutboundActionAudit(
        request_id=request_id,
        log_id=log_id,
        actor=actor,
        actor_role=actor_role,
        action_key=action_key,
        channel=channel,
        decision=decision,
        policy_rule=policy_rule,
        reason=reason,
        queue=queue,
        priority=priority,
        delivery_json=delivery_json,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return row


def get_recent_outbound_action_audits(
    db: Session,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = (
        db.execute(
            select(OutboundActionAudit)
            .order_by(OutboundActionAudit.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": row.id,
            "request_id": row.request_id,
            "log_id": row.log_id,
            "actor": row.actor,
            "actor_role": row.actor_role,
            "action_key": row.action_key,
            "channel": row.channel,
            "decision": row.decision,
            "policy_rule": row.policy_rule,
            "reason": row.reason,
            "queue": row.queue,
            "priority": row.priority,
            "delivery_json": row.delivery_json,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]