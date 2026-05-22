from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.triage_log import TriageLog


def _pct(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _safe_text(value: Any, fallback: str = "Unknown") -> str:
    if value is None:
        return fallback

    text = str(value).strip()
    return text if text else fallback


def _final_value(raw_value: Any, is_correct: bool | None, corrected_value: Any) -> str:
    if is_correct is False and corrected_value:
        return _safe_text(corrected_value)
    return _safe_text(raw_value)


def _is_accepted_after_feedback(is_correct: bool | None, corrected_value: Any) -> bool:
    """
    Correction-aware benchmark meaning:
    - If human said correct -> accepted
    - If human said wrong but provided corrected value -> accepted after correction
    - If human said wrong and no correction exists -> not accepted
    """
    if is_correct is True:
        return True

    if is_correct is False and corrected_value:
        return True

    return False


def _accuracy_block(rows: list[TriageLog], field_name: str) -> dict[str, Any]:
    if field_name == "queue":
        feedback_rows = [row for row in rows if row.user_queue_correct is not None]
        correct_count = sum(1 for row in feedback_rows if row.user_queue_correct is True)
        accepted_after_correction = sum(
            1
            for row in feedback_rows
            if _is_accepted_after_feedback(row.user_queue_correct, row.corrected_queue)
        )

    elif field_name == "priority":
        feedback_rows = [row for row in rows if row.user_priority_correct is not None]
        correct_count = sum(1 for row in feedback_rows if row.user_priority_correct is True)
        accepted_after_correction = sum(
            1
            for row in feedback_rows
            if _is_accepted_after_feedback(row.user_priority_correct, row.corrected_priority)
        )

    elif field_name == "intent":
        feedback_rows = [row for row in rows if row.user_intent_correct is not None]
        correct_count = sum(1 for row in feedback_rows if row.user_intent_correct is True)
        accepted_after_correction = sum(
            1
            for row in feedback_rows
            if _is_accepted_after_feedback(row.user_intent_correct, row.corrected_intent)
        )

    elif field_name == "recommended_action":
        feedback_rows = [
            row for row in rows
            if row.user_recommended_action_correct is not None
        ]
        correct_count = sum(
            1
            for row in feedback_rows
            if row.user_recommended_action_correct is True
        )
        accepted_after_correction = sum(
            1
            for row in feedback_rows
            if _is_accepted_after_feedback(
                row.user_recommended_action_correct,
                row.corrected_recommended_action,
            )
        )

    else:
        feedback_rows = []
        correct_count = 0
        accepted_after_correction = 0

    total = len(feedback_rows)

    return {
        "field": field_name,
        "feedback_count": total,
        "raw_correct_count": correct_count,
        "raw_accuracy_pct": _pct(correct_count, total),
        "accepted_after_correction_count": accepted_after_correction,
        "correction_aware_accuracy_pct": _pct(accepted_after_correction, total),
        "correction_count": total - correct_count,
        "correction_rate_pct": _pct(total - correct_count, total),
    }


def _accuracy_by_predicted_queue(rows: list[TriageLog]) -> list[dict[str, Any]]:
    queue_rows = [row for row in rows if row.user_queue_correct is not None]

    grouped: dict[str, dict[str, Any]] = {}

    for row in queue_rows:
        predicted_queue = _safe_text(row.predicted_queue)

        if predicted_queue not in grouped:
            grouped[predicted_queue] = {
                "predicted_queue": predicted_queue,
                "feedback_count": 0,
                "raw_correct_count": 0,
                "corrected_count": 0,
                "correction_aware_accepted_count": 0,
            }

        grouped[predicted_queue]["feedback_count"] += 1

        if row.user_queue_correct is True:
            grouped[predicted_queue]["raw_correct_count"] += 1

        if row.user_queue_correct is False:
            grouped[predicted_queue]["corrected_count"] += 1

        if _is_accepted_after_feedback(row.user_queue_correct, row.corrected_queue):
            grouped[predicted_queue]["correction_aware_accepted_count"] += 1

    result = []

    for item in grouped.values():
        feedback_count = item["feedback_count"]
        item["raw_accuracy_pct"] = _pct(item["raw_correct_count"], feedback_count)
        item["correction_rate_pct"] = _pct(item["corrected_count"], feedback_count)
        item["correction_aware_accuracy_pct"] = _pct(
            item["correction_aware_accepted_count"],
            feedback_count,
        )
        result.append(item)

    return sorted(
        result,
        key=lambda item: (item["correction_rate_pct"], item["feedback_count"]),
        reverse=True,
    )


def _accuracy_by_predicted_priority(rows: list[TriageLog]) -> list[dict[str, Any]]:
    priority_rows = [row for row in rows if row.user_priority_correct is not None]

    grouped: dict[str, dict[str, Any]] = {}

    for row in priority_rows:
        predicted_priority = _safe_text(row.predicted_priority)

        if predicted_priority not in grouped:
            grouped[predicted_priority] = {
                "predicted_priority": predicted_priority,
                "feedback_count": 0,
                "raw_correct_count": 0,
                "corrected_count": 0,
                "correction_aware_accepted_count": 0,
            }

        grouped[predicted_priority]["feedback_count"] += 1

        if row.user_priority_correct is True:
            grouped[predicted_priority]["raw_correct_count"] += 1

        if row.user_priority_correct is False:
            grouped[predicted_priority]["corrected_count"] += 1

        if _is_accepted_after_feedback(row.user_priority_correct, row.corrected_priority):
            grouped[predicted_priority]["correction_aware_accepted_count"] += 1

    result = []

    for item in grouped.values():
        feedback_count = item["feedback_count"]
        item["raw_accuracy_pct"] = _pct(item["raw_correct_count"], feedback_count)
        item["correction_rate_pct"] = _pct(item["corrected_count"], feedback_count)
        item["correction_aware_accuracy_pct"] = _pct(
            item["correction_aware_accepted_count"],
            feedback_count,
        )
        result.append(item)

    return sorted(
        result,
        key=lambda item: (item["correction_rate_pct"], item["feedback_count"]),
        reverse=True,
    )


def _queue_confusion_matrix(rows: list[TriageLog]) -> list[dict[str, Any]]:
    queue_rows = [row for row in rows if row.user_queue_correct is not None]

    matrix: dict[tuple[str, str], int] = {}

    for row in queue_rows:
        predicted_queue = _safe_text(row.predicted_queue)
        final_queue = _final_value(
            row.predicted_queue,
            row.user_queue_correct,
            row.corrected_queue,
        )

        key = (predicted_queue, final_queue)
        matrix[key] = matrix.get(key, 0) + 1

    return [
        {
            "predicted_queue": predicted_queue,
            "final_or_corrected_queue": final_queue,
            "count": count,
            "changed": predicted_queue != final_queue,
        }
        for (predicted_queue, final_queue), count in sorted(
            matrix.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]


def _router_family_accuracy(rows: list[TriageLog]) -> list[dict[str, Any]]:
    feedback_rows = [row for row in rows if row.user_queue_correct is not None]

    grouped: dict[str, dict[str, Any]] = {}

    for row in feedback_rows:
        trace = row.trace_json or {}
        router_family = _safe_text(
            trace.get("deterministic_route_family")
            or trace.get("route_family")
            or trace.get("specialist_profile"),
            "Unknown",
        )

        if router_family not in grouped:
            grouped[router_family] = {
                "router_family": router_family,
                "feedback_count": 0,
                "raw_queue_correct_count": 0,
                "queue_correction_count": 0,
            }

        grouped[router_family]["feedback_count"] += 1

        if row.user_queue_correct is True:
            grouped[router_family]["raw_queue_correct_count"] += 1

        if row.user_queue_correct is False:
            grouped[router_family]["queue_correction_count"] += 1

    result = []

    for item in grouped.values():
        feedback_count = item["feedback_count"]
        item["raw_queue_accuracy_pct"] = _pct(
            item["raw_queue_correct_count"],
            feedback_count,
        )
        item["queue_correction_rate_pct"] = _pct(
            item["queue_correction_count"],
            feedback_count,
        )
        result.append(item)

    return sorted(
        result,
        key=lambda item: (item["queue_correction_rate_pct"], item["feedback_count"]),
        reverse=True,
    )


def _recent_corrections(rows: list[TriageLog], limit: int = 20) -> list[dict[str, Any]]:
    corrected_rows = [
        row for row in rows
        if row.feedback_at is not None
        and (
            row.user_queue_correct is False
            or row.user_priority_correct is False
            or row.user_intent_correct is False
            or row.user_recommended_action_correct is False
        )
    ]

    corrected_rows = sorted(
        corrected_rows,
        key=lambda row: row.feedback_at or row.created_at,
        reverse=True,
    )[:limit]

    return [
        {
            "request_id": row.request_id,
            "subject": row.subject,
            "predicted_queue": row.predicted_queue,
            "corrected_queue": row.corrected_queue,
            "predicted_priority": row.predicted_priority,
            "corrected_priority": row.corrected_priority,
            "predicted_intent": row.likely_intent,
            "corrected_intent": row.corrected_intent,
            "predicted_recommended_action": row.recommended_action,
            "corrected_recommended_action": row.corrected_recommended_action,
            "corrected_by": row.correction_applied_by,
            "feedback_at": row.feedback_at.isoformat() if row.feedback_at else None,
        }
        for row in corrected_rows
    ]


def get_correction_aware_benchmark_summary(
    db: Session,
    days: int = 30,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)

    rows = (
        db.execute(
            select(TriageLog)
            .where(TriageLog.created_at >= start_time)
            .order_by(TriageLog.created_at.desc())
        )
        .scalars()
        .all()
    )

    feedback_rows = [row for row in rows if row.feedback_at is not None]

    queue_accuracy = _accuracy_block(rows, "queue")
    priority_accuracy = _accuracy_block(rows, "priority")
    intent_accuracy = _accuracy_block(rows, "intent")
    action_accuracy = _accuracy_block(rows, "recommended_action")

    field_accuracy = [
        queue_accuracy,
        priority_accuracy,
        intent_accuracy,
        action_accuracy,
    ]

    accuracy_by_queue = _accuracy_by_predicted_queue(rows)
    accuracy_by_priority = _accuracy_by_predicted_priority(rows)
    confusion_matrix = _queue_confusion_matrix(rows)
    router_family_accuracy = _router_family_accuracy(rows)
    recent_corrections = _recent_corrections(rows, limit=20)

    worst_queues = sorted(
        accuracy_by_queue,
        key=lambda item: (item["correction_rate_pct"], item["feedback_count"]),
        reverse=True,
    )[:5]

    return {
        "window_days": days,
        "total_runs": len(rows),
        "feedback_count": len(feedback_rows),

        "field_accuracy": field_accuracy,

        "raw_accuracy_summary": {
            "queue_accuracy_pct": queue_accuracy["raw_accuracy_pct"],
            "priority_accuracy_pct": priority_accuracy["raw_accuracy_pct"],
            "intent_accuracy_pct": intent_accuracy["raw_accuracy_pct"],
            "recommended_action_accuracy_pct": action_accuracy["raw_accuracy_pct"],
        },

        "correction_aware_accuracy_summary": {
            "queue_accuracy_pct": queue_accuracy["correction_aware_accuracy_pct"],
            "priority_accuracy_pct": priority_accuracy["correction_aware_accuracy_pct"],
            "intent_accuracy_pct": intent_accuracy["correction_aware_accuracy_pct"],
            "recommended_action_accuracy_pct": action_accuracy["correction_aware_accuracy_pct"],
        },

        "accuracy_by_predicted_queue": accuracy_by_queue,
        "accuracy_by_predicted_priority": accuracy_by_priority,
        "queue_confusion_matrix": confusion_matrix,
        "router_family_accuracy": router_family_accuracy,
        "worst_performing_queues": worst_queues,
        "recent_corrections": recent_corrections,

        "notes": [
            "This benchmark uses stored model predictions and human corrections.",
            "No LLM rerun is performed.",
            "Correction-aware accuracy means wrong predictions are counted as accepted when a human correction exists.",
        ],
    }