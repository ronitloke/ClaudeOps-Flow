from datetime import datetime

from pydantic import BaseModel


class ApprovalActionRequest(BaseModel):
    actor: str = "admin"
    actor_role: str = "admin"


class ApprovalActionResponse(BaseModel):
    request_id: str
    approval_status: str
    automation_executed: bool
    message: str


class PendingApprovalsResponse(BaseModel):
    items: list[dict]


class PendingApprovalItem(BaseModel):
    request_id: str
    subject: str
    summary: str | None = None
    predicted_queue: str | None = None
    predicted_priority: str | None = None
    likely_intent: str | None = None
    sla_risk: bool = False
    needs_human_review: bool = False
    approval_reason: str | None = None
    automation_target_team: str | None = None
    automation_urgency_level: str | None = None
    created_at: datetime