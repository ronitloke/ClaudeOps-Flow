from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class OutboundActionAudit(Base):
    __tablename__ = "outbound_action_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    request_id: Mapped[str] = mapped_column(String(36), index=True)
    log_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    actor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    action_key: Mapped[str] = mapped_column(String(100), index=True)
    channel: Mapped[str | None] = mapped_column(String(100), nullable=True)

    decision: Mapped[str] = mapped_column(String(30))
    policy_rule: Mapped[str | None] = mapped_column(String(150), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    queue: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True)

    delivery_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )