from pathlib import Path

import pandas as pd

from app.core.settings import get_settings
from app.schemas.benchmark import BenchmarkRunRequest
from app.schemas.triage import TicketTriageRequest
from app.services.automation_rules import build_escalation_decision
from app.services.queue_mapping import canonicalize_queue_label, queue_family
from app.services.triage_service import get_active_model_name, run_triage


def _resolve_column(df: pd.DataFrame, candidates: list[str], required: bool = False) -> str | None:
    lowered = {col.lower(): col for col in df.columns}

    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]

    if required:
        raise ValueError(f"Required column not found. Tried: {candidates}")

    return None


def run_ticket_benchmark(payload: BenchmarkRunRequest) -> dict:
    settings = get_settings()
    data_path = Path(settings.processed_data_dir) / "tickets_unified.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"{data_path} not found. Run data preparation first.")

    df = pd.read_csv(data_path)

    if df.empty:
        raise ValueError("Benchmark dataset is empty.")

    subject_col = _resolve_column(df, ["subject", "title", "ticket_subject"])
    body_col = _resolve_column(df, ["body", "description", "ticket_body", "message", "content"], required=True)
    queue_col = _resolve_column(df, ["queue", "predicted_queue", "support_queue", "queue_name", "department"], required=True)
    language_col = _resolve_column(df, ["language", "lang", "language_code"])
    business_type_col = _resolve_column(df, ["business_type", "business_context", "domain", "vertical"])

    sample_df = df.sample(
        n=min(payload.sample_size, len(df)),
        random_state=payload.random_seed,
    ).reset_index(drop=True)

    allowed_dataset_queues = sorted(
        {
            str(q).strip()
            for q in sample_df[queue_col].dropna().tolist()
            if str(q).strip()
        }
    )

    rows: list[dict] = []
    success_count = 0
    failure_count = 0
    queue_match_count = 0
    escalated_count = 0
    automation_ready_count = 0
    total_latency = 0.0

    for _, row in sample_df.iterrows():
        subject = str(row[subject_col]).strip() if subject_col and pd.notna(row[subject_col]) else ""
        body = str(row[body_col]).strip() if pd.notna(row[body_col]) else ""
        expected_queue_raw = str(row[queue_col]).strip() if pd.notna(row[queue_col]) else ""

        if not subject:
            subject = (body[:80] + "...") if len(body) > 80 else body

        language_hint = (
            str(row[language_col]).strip()
            if language_col and pd.notna(row[language_col])
            else "en"
        )
        business_type_hint = (
            str(row[business_type_col]).strip()
            if business_type_col and pd.notna(row[business_type_col])
            else "Support Operations"
        )

        triage_payload = TicketTriageRequest(
            subject=subject,
            body=body,
            language_hint=language_hint or None,
            business_type_hint=business_type_hint or None,
            include_draft_response=True,
            simulate_error=False,
        )

        try:
            result = run_triage(triage_payload)
            triage_response = result["triage_response"]
            decision = build_escalation_decision(triage_payload, triage_response)

            latency_ms = float(result["latency_ms"])
            total_latency += latency_ms
            success_count += 1

            expected_queue_normalized = canonicalize_queue_label(expected_queue_raw, allowed_dataset_queues)
            predicted_queue_normalized = canonicalize_queue_label(
                triage_response.predicted_queue,
                allowed_dataset_queues,
            )

            queue_match = (
                expected_queue_normalized == predicted_queue_normalized
                or queue_family(expected_queue_normalized) == queue_family(predicted_queue_normalized)
            )

            if queue_match:
                queue_match_count += 1

            escalated = bool(decision.get("should_escalate", False))
            if escalated:
                escalated_count += 1

            automation_ready = bool(decision)
            if automation_ready:
                automation_ready_count += 1

            rows.append(
                {
                    "subject_excerpt": subject[:80],
                    "expected_queue_raw": expected_queue_raw,
                    "expected_queue_normalized": expected_queue_normalized,
                    "predicted_queue_raw": triage_response.predicted_queue,
                    "predicted_queue_normalized": predicted_queue_normalized,
                    "queue_match": queue_match,
                    "priority": triage_response.predicted_priority,
                    "intent": triage_response.likely_intent,
                    "sla_risk": triage_response.sla_risk,
                    "escalated": escalated,
                    "automation_ready": automation_ready,
                    "latency_ms": latency_ms,
                    "status": "success",
                    "error_message": None,
                }
            )
        except Exception as exc:
            failure_count += 1
            rows.append(
                {
                    "subject_excerpt": subject[:80],
                    "expected_queue_raw": expected_queue_raw,
                    "expected_queue_normalized": canonicalize_queue_label(expected_queue_raw, allowed_dataset_queues),
                    "predicted_queue_raw": None,
                    "predicted_queue_normalized": None,
                    "queue_match": False,
                    "priority": None,
                    "intent": None,
                    "sla_risk": None,
                    "escalated": False,
                    "automation_ready": False,
                    "latency_ms": None,
                    "status": "error",
                    "error_message": str(exc),
                }
            )

    avg_latency_ms = round(total_latency / success_count, 2) if success_count else None
    queue_prediction_consistency_pct = round((queue_match_count / success_count) * 100, 2) if success_count else 0.0

    response = {
        "provider": settings.llm_provider,
        "model_name": get_active_model_name(),
        "dataset_path": str(data_path),
        "sample_size_requested": payload.sample_size,
        "sample_size_used": len(sample_df),
        "success_count": success_count,
        "failure_count": failure_count,
        "queue_match_count": queue_match_count,
        "queue_prediction_consistency_pct": queue_prediction_consistency_pct,
        "average_latency_ms": avg_latency_ms,
        "escalated_count": escalated_count,
        "successful_automation_ready_outputs": automation_ready_count,
    }

    if payload.include_rows:
        response["rows"] = rows

    return response