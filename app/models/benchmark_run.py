from sqlalchemy import JSON, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50))
    model_name: Mapped[str] = mapped_column(String(100))

    sample_size: Mapped[int] = mapped_column(Integer)
    success_count: Mapped[int] = mapped_column(Integer)
    failure_count: Mapped[int] = mapped_column(Integer)
    queue_match_count: Mapped[int] = mapped_column(Integer)
    queue_prediction_consistency_pct: Mapped[float] = mapped_column(Float)
    average_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    escalated_count: Mapped[int] = mapped_column(Integer)
    successful_automation_ready_outputs: Mapped[int] = mapped_column(Integer)

    run_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    results_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )