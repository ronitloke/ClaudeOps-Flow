import time
from typing import Any, Dict, Optional
from app.services.automation_service import determine_approval_state

from app.core.settings import get_settings
from app.schemas.triage import (
    StructuredFields,
    TicketTriageRequest,
    TicketTriageResponse,
)
from app.services.deterministic_router import route_ticket
from app.services.label_catalog import get_label_catalog
from app.services.llm_factory import get_llm_client
from app.services.prompt_builder import PROMPT_VERSION, build_system_prompt, build_user_prompt

class TriageExecutionError(Exception):
    def __init__(
        self,
        message: str,
        latency_ms: float | None = None,
        retry_count: int = 0,
        error_type: str | None = None,
    ) -> None:
        super().__init__(message)
        self.latency_ms = latency_ms
        self.retry_count = retry_count
        self.error_type = error_type


def _pick_allowed(value: Optional[str], allowed: list[str], default: Optional[str] = None) -> Optional[str]:
    if value is None:
        return default

    raw = str(value).strip()
    if not raw:
        return default

    for item in allowed:
        if raw == item:
            return item

    for item in allowed:
        if raw.lower() == item.lower():
            return item

    return default


def _clamp_confidence(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.5

    if score < 0:
        return 0.0
    if score > 1:
        return 1.0
    return score

def _estimate_cost_usd(input_tokens: int | None, output_tokens: int | None) -> float | None:
    settings = get_settings()

    if input_tokens is None and output_tokens is None:
        return None

    input_cost = ((input_tokens or 0) / 1_000_000) * settings.llm_input_cost_per_1m_tokens
    output_cost = ((output_tokens or 0) / 1_000_000) * settings.llm_output_cost_per_1m_tokens

    return round(input_cost + output_cost, 8)

def _build_automation_decision(normalized: dict[str, Any]) -> dict[str, Any]:
    priority = str(normalized.get("predicted_priority") or "").strip().lower()
    queue = str(normalized.get("predicted_queue") or "").strip()

    should_escalate = bool(normalized.get("sla_risk")) or priority == "high"

    if bool(normalized.get("sla_risk")) and priority == "high":
        urgency_level = "critical"
    elif priority == "high":
        urgency_level = "high"
    else:
        urgency_level = "normal"

    return {
        "should_escalate": should_escalate,
        "target_team": queue or "General Inquiry",
        "urgency_level": urgency_level,
    }

def get_active_model_name() -> str:
    settings = get_settings()
    provider = settings.llm_provider.strip().lower()

    if provider == "groq":
        return settings.groq_model
    if provider == "gemini":
        return settings.gemini_model
    if provider == "claude":
        return settings.claude_model

    return "unknown"


def run_triage(payload: TicketTriageRequest) -> Dict[str, Any]:
    settings = get_settings()
    catalog = get_label_catalog()

    deterministic_route = route_ticket(payload=payload, catalog=catalog)

    system_prompt = build_system_prompt(
        catalog=catalog,
        route_context=deterministic_route,
    )
    user_prompt = build_user_prompt(payload)

    client = get_llm_client()
    max_retries = max(settings.llm_max_retries, 0)
    start_time = time.perf_counter()
    last_error: Exception | None = None

    if payload.simulate_error:
        time.sleep(0.25)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        raise TriageExecutionError(
            message="Simulated triage failure for testing error analytics.",
            latency_ms=latency_ms,
            retry_count=0,
            error_type="SimulatedTriageError",
        )

    for attempt in range(max_retries + 1):
        try:
            raw = client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
            llm_usage = raw.pop("_llm_usage", {}) if isinstance(raw, dict) else {}

            default_language = payload.language_hint or (catalog["languages"][0] if catalog["languages"] else "en")
            default_type = catalog["types"][0] if catalog["types"] else "Request"
            default_queue = catalog["queues"][0] if catalog["queues"] else "General Inquiry"
            default_priority = "medium" if "medium" in [p.lower() for p in catalog["priorities"]] else (
                catalog["priorities"][0] if catalog["priorities"] else "medium"
            )

            structured = raw.get("structured_fields") or {}

            normalized = {
                "summary": str(raw.get("summary") or "Ticket received and triaged."),
                "detected_language": _pick_allowed(raw.get("detected_language"), catalog["languages"], default_language),
                "predicted_type": _pick_allowed(raw.get("predicted_type"), catalog["types"], default_type),
                "predicted_queue": _pick_allowed(raw.get("predicted_queue"), catalog["queues"], default_queue),
                "predicted_priority": _pick_allowed(raw.get("predicted_priority"), catalog["priorities"], default_priority),
                "predicted_business_type": _pick_allowed(
                    raw.get("predicted_business_type"),
                    catalog["business_types"],
                    payload.business_type_hint,
                ),
                "likely_intent": _pick_allowed(raw.get("likely_intent"), catalog["intents"], None),
                "urgency_reason": str(raw.get("urgency_reason") or "No urgency reason provided."),
                "sla_risk": bool(raw.get("sla_risk", False)),
                "needs_human_review": bool(raw.get("needs_human_review", False)),
                "recommended_action": str(raw.get("recommended_action") or "Route to the appropriate support queue."),
                "draft_response": str(raw.get("draft_response") or ""),
                "structured_fields": StructuredFields(
                    customer_name=structured.get("customer_name"),
                    order_id=structured.get("order_id"),
                    account_id=structured.get("account_id"),
                    product_name=structured.get("product_name"),
                    issue_keywords=structured.get("issue_keywords") or [],
                ),
                "confidence": _clamp_confidence(raw.get("confidence")),
            }

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            triage_response = TicketTriageResponse(**normalized)

            automation_decision = _build_automation_decision(normalized)
            approval_state = determine_approval_state(normalized, automation_decision)

            input_tokens = llm_usage.get("input_tokens")
            output_tokens = llm_usage.get("output_tokens")
            total_tokens = llm_usage.get("total_tokens")

            estimated_cost_usd = _estimate_cost_usd(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            return {
                "triage_response": triage_response,
                "raw_llm_output": raw,
                "provider": settings.llm_provider,
                "model_name": get_active_model_name(),
                "latency_ms": latency_ms,
                "retry_count": attempt,
                "had_retry": attempt > 0,
                "automation_decision": automation_decision,
                "deterministic_route": deterministic_route,
                "approval": {
                    "required": approval_state["required"],
                    "status": approval_state["status"],
                    "reason": approval_state["reason"],
                    "automation_executed": approval_state["automation_executed"],
                },
                "observability": {
                    "prompt_version": PROMPT_VERSION,
                    "model_version": get_active_model_name(),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": estimated_cost_usd,
                    "trace": {
                        "provider": settings.llm_provider,
                        "model_name": get_active_model_name(),
                        "prompt_version": PROMPT_VERSION,
                        "latency_ms": latency_ms,
                        "retry_count": attempt,
                        "had_retry": attempt > 0,

                        "deterministic_route_family": deterministic_route.get("route_family"),
                        "specialist_profile": deterministic_route.get("specialist_profile"),
                        "preferred_queue_hint": deterministic_route.get("preferred_queue_hint"),
                        "router_confidence_hint": deterministic_route.get("confidence_hint"),
                        "router_reason": deterministic_route.get("route_reason"),
                        "router_matched_keywords": deterministic_route.get("matched_keywords"),
                        "router_family_scores": deterministic_route.get("family_scores"),

                        "approval_required": approval_state["required"],
                        "approval_status": approval_state["status"],
                        "automation_should_escalate": automation_decision.get("should_escalate"),
                        "automation_target_team": automation_decision.get("target_team"),
                        "automation_urgency_level": automation_decision.get("urgency_level"),
                    },
                },
            }

        except Exception as exc:
            last_error = exc

            if attempt < max_retries:
                time.sleep(settings.llm_retry_delay_seconds)
                continue

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raise TriageExecutionError(
                message=str(exc),
                latency_ms=latency_ms,
                retry_count=attempt,
                error_type=exc.__class__.__name__,
            ) from exc

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    raise TriageExecutionError(
        message=str(last_error) if last_error else "Unknown triage error",
        latency_ms=latency_ms,
        retry_count=max_retries,
        error_type=last_error.__class__.__name__ if last_error else "UnknownError",
    )


def get_triage_catalog() -> Dict[str, Any]:
    return get_label_catalog()