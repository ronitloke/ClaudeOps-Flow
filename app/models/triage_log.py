from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class TriageLog(Base):
    __tablename__ = "triage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)

    status: Mapped[str] = mapped_column(String(20), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    model_name: Mapped[str] = mapped_column(String(100))

    subject: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    language_hint: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_type_hint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    include_draft_response: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    predicted_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    predicted_queue: Mapped[str | None] = mapped_column(String(100), nullable=True)
    predicted_priority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    predicted_business_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    likely_intent: Mapped[str | None] = mapped_column(String(100), nullable=True)

    urgency_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    sla_risk: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    needs_human_review: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    had_retry: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    automation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    automation_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    automation_should_escalate: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    automation_target_team: Mapped[str | None] = mapped_column(String(100), nullable=True)
    automation_urgency_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    automation_decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    automation_slack_delivery: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    automation_webhook_delivery: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    automation_zapier_delivery: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    automation_make_delivery: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    automation_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    approval_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="not_required",
        server_default=text("'not_required'"),
    )
    approval_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    approved_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rejected_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    automation_executed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    automation_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    structured_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_request: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_llm_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    prompt_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)

    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    trace_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user_queue_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corrected_queue: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user_priority_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corrected_priority: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user_intent_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corrected_intent: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user_recommended_action_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    corrected_recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_feedback_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    correction_applied_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    correction_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correction_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    feedback_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )