from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark_run import BenchmarkRun


def save_benchmark_run(
    db: Session,
    result: dict,
    run_config: dict,
) -> BenchmarkRun:
    row = BenchmarkRun(
        provider=result.get("provider", "unknown"),
        model_name=result.get("model_name", "unknown"),
        sample_size=result.get("sample_size_used", 0),
        success_count=result.get("success_count", 0),
        failure_count=result.get("failure_count", 0),
        queue_match_count=result.get("queue_match_count", 0),
        queue_prediction_consistency_pct=result.get("queue_prediction_consistency_pct", 0.0),
        average_latency_ms=result.get("average_latency_ms"),
        escalated_count=result.get("escalated_count", 0),
        successful_automation_ready_outputs=result.get("successful_automation_ready_outputs", 0),
        run_config=run_config,
        results_json=result,
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_recent_benchmark_runs(db: Session, limit: int = 20) -> list[dict]:
    stmt = (
        select(BenchmarkRun)
        .order_by(BenchmarkRun.created_at.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).scalars().all()

    return [
        {
            "id": row.id,
            "provider": row.provider,
            "model_name": row.model_name,
            "sample_size": row.sample_size,
            "success_count": row.success_count,
            "failure_count": row.failure_count,
            "queue_match_count": row.queue_match_count,
            "queue_prediction_consistency_pct": row.queue_prediction_consistency_pct,
            "average_latency_ms": row.average_latency_ms,
            "escalated_count": row.escalated_count,
            "successful_automation_ready_outputs": row.successful_automation_ready_outputs,
            "run_config": row.run_config,
            "results_json": row.results_json,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]