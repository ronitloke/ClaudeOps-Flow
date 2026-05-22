from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.models.benchmark_run import BenchmarkRun
from app.models.triage_log import TriageLog


def _pct(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 2)

def _feedback_correction_summary(rows: list[TriageLog]) -> dict[str, Any]:
    feedback_rows = [row for row in rows if row.feedback_at is not None]

    queue_feedback_rows = [row for row in feedback_rows if row.user_queue_correct is not None]
    priority_feedback_rows = [row for row in feedback_rows if row.user_priority_correct is not None]
    intent_feedback_rows = [row for row in feedback_rows if row.user_intent_correct is not None]
    action_feedback_rows = [
        row for row in feedback_rows
        if row.user_recommended_action_correct is not None
    ]

    queue_correct = sum(1 for row in queue_feedback_rows if row.user_queue_correct is True)
    priority_correct = sum(1 for row in priority_feedback_rows if row.user_priority_correct is True)
    intent_correct = sum(1 for row in intent_feedback_rows if row.user_intent_correct is True)
    action_correct = sum(
        1 for row in action_feedback_rows
        if row.user_recommended_action_correct is True
    )

    queue_corrected = sum(
        1 for row in queue_feedback_rows
        if row.user_queue_correct is False and bool(row.corrected_queue)
    )
    priority_corrected = sum(
        1 for row in priority_feedback_rows
        if row.user_priority_correct is False and bool(row.corrected_priority)
    )
    intent_corrected = sum(
        1 for row in intent_feedback_rows
        if row.user_intent_correct is False and bool(row.corrected_intent)
    )
    action_corrected = sum(
        1 for row in action_feedback_rows
        if row.user_recommended_action_correct is False and bool(row.corrected_recommended_action)
    )

    correction_rate_by_queue: dict[str, dict[str, Any]] = {}

    for row in queue_feedback_rows:
        queue = row.predicted_queue or "Unknown"

        if queue not in correction_rate_by_queue:
            correction_rate_by_queue[queue] = {
                "predicted_queue": queue,
                "feedback_count": 0,
                "queue_correction_count": 0,
                "queue_correction_rate_pct": 0.0,
            }

        correction_rate_by_queue[queue]["feedback_count"] += 1

        if row.user_queue_correct is False:
            correction_rate_by_queue[queue]["queue_correction_count"] += 1

    for item in correction_rate_by_queue.values():
        item["queue_correction_rate_pct"] = _pct(
            item["queue_correction_count"],
            item["feedback_count"],
        )

    return {
        "feedback_count": len(feedback_rows),

        "queue_feedback_count": len(queue_feedback_rows),
        "priority_feedback_count": len(priority_feedback_rows),
        "intent_feedback_count": len(intent_feedback_rows),
        "recommended_action_feedback_count": len(action_feedback_rows),

        "raw_queue_accuracy_pct": _pct(queue_correct, len(queue_feedback_rows)),
        "raw_priority_accuracy_pct": _pct(priority_correct, len(priority_feedback_rows)),
        "raw_intent_accuracy_pct": _pct(intent_correct, len(intent_feedback_rows)),
        "raw_recommended_action_accuracy_pct": _pct(action_correct, len(action_feedback_rows)),

        "queue_correction_count": len(queue_feedback_rows) - queue_correct,
        "priority_correction_count": len(priority_feedback_rows) - priority_correct,
        "intent_correction_count": len(intent_feedback_rows) - intent_correct,
        "recommended_action_correction_count": len(action_feedback_rows) - action_correct,

        "correction_rate_by_queue": list(correction_rate_by_queue.values()),

        "benchmark_without_corrections": {
            "queue_accuracy_pct": _pct(queue_correct, len(queue_feedback_rows)),
            "priority_accuracy_pct": _pct(priority_correct, len(priority_feedback_rows)),
            "intent_accuracy_pct": _pct(intent_correct, len(intent_feedback_rows)),
            "recommended_action_accuracy_pct": _pct(action_correct, len(action_feedback_rows)),
        },

        "benchmark_with_corrections": {
            "queue_accuracy_pct": _pct(queue_correct + queue_corrected, len(queue_feedback_rows)),
            "priority_accuracy_pct": _pct(priority_correct + priority_corrected, len(priority_feedback_rows)),
            "intent_accuracy_pct": _pct(intent_correct + intent_corrected, len(intent_feedback_rows)),
            "recommended_action_accuracy_pct": _pct(
                action_correct + action_corrected,
                len(action_feedback_rows),
            ),
        },
    }

def get_observability_summary(db: Session, hours: int = 24) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    rows = (
        db.execute(
            select(TriageLog).where(TriageLog.created_at >= start_time)
        )
        .scalars()
        .all()
    )

    total = len(rows)
    error_count = sum(1 for row in rows if row.status == "error")
    success_count = sum(1 for row in rows if row.status == "success")
    low_confidence_count = sum(
        1 for row in rows
        if row.confidence is not None and row.confidence < 0.70
    )

    latencies = [
        float(row.latency_ms)
        for row in rows
        if row.latency_ms is not None
    ]

    avg_latency_ms = round(sum(latencies) / len(latencies), 2) if latencies else None
    max_latency_ms = round(max(latencies), 2) if latencies else None

    total_input_tokens = sum(row.input_tokens or 0 for row in rows)
    total_output_tokens = sum(row.output_tokens or 0 for row in rows)
    total_tokens = sum(row.total_tokens or 0 for row in rows)

    settings = get_settings()

    stored_estimated_cost = round(
        sum(row.estimated_cost_usd or 0 for row in rows),
        8,
    )

    recalculated_estimated_cost = round(
        ((total_input_tokens / 1_000_000) * settings.llm_input_cost_per_1m_tokens)
        + ((total_output_tokens / 1_000_000) * settings.llm_output_cost_per_1m_tokens),
        8,
    )

    if settings.llm_input_cost_per_1m_tokens > 0 or settings.llm_output_cost_per_1m_tokens > 0:
        total_estimated_cost = recalculated_estimated_cost
        cost_source = "recalculated_from_current_env_rates"
    else:
        total_estimated_cost = stored_estimated_cost
        cost_source = "stored_log_cost"

    feedback_rows = [row for row in rows if row.user_queue_correct is not None]
    queue_correct_count = sum(1 for row in feedback_rows if row.user_queue_correct is True)
    feedback_correction_summary = _feedback_correction_summary(rows)

    alerts: list[dict[str, Any]] = []

    error_rate = _pct(error_count, total)
    low_confidence_rate = _pct(low_confidence_count, total)

    if error_rate >= 20 and total >= 5:
        alerts.append(
            {
                "type": "error_spike",
                "severity": "high",
                "message": f"Error rate is {error_rate}% over the last {hours} hours.",
            }
        )

    if low_confidence_rate >= 30 and total >= 5:
        alerts.append(
            {
                "type": "low_confidence_spike",
                "severity": "medium",
                "message": f"Low-confidence rate is {low_confidence_rate}% over the last {hours} hours.",
            }
        )

    if avg_latency_ms is not None and avg_latency_ms >= 5000:
        alerts.append(
            {
                "type": "latency_spike",
                "severity": "medium",
                "message": f"Average latency is {avg_latency_ms} ms over the last {hours} hours.",
            }
        )

    benchmark_rows = (
        db.execute(
            select(BenchmarkRun)
            .order_by(BenchmarkRun.created_at.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )

    benchmark_history = [
        {
            "id": row.id,
            "provider": row.provider,
            "model_name": row.model_name,
            "sample_size": row.sample_size,
            "queue_prediction_consistency_pct": row.queue_prediction_consistency_pct,
            "average_latency_ms": row.average_latency_ms,
            "success_count": row.success_count,
            "failure_count": row.failure_count,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in benchmark_rows
    ]

    return {
        "window_hours": hours,
        "total_runs": total,
        "success_count": success_count,
        "error_count": error_count,
        "error_rate_pct": error_rate,
        "low_confidence_count": low_confidence_count,
        "low_confidence_rate_pct": low_confidence_rate,
        "average_latency_ms": avg_latency_ms,
        "max_latency_ms": max_latency_ms,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": total_estimated_cost,
        "stored_estimated_cost_usd": stored_estimated_cost,
        "recalculated_estimated_cost_usd": recalculated_estimated_cost,
        "cost_source": cost_source,
        "feedback_count": len(feedback_rows),
        "queue_feedback_accuracy_pct": _pct(queue_correct_count, len(feedback_rows)),
        "feedback_correction_summary": feedback_correction_summary,
        "benchmark_without_corrections": feedback_correction_summary["benchmark_without_corrections"],
        "benchmark_with_corrections": feedback_correction_summary["benchmark_with_corrections"],
        "correction_rate_by_queue": feedback_correction_summary["correction_rate_by_queue"],

        "alerts": alerts,
        "recent_benchmark_history": benchmark_history,
    }