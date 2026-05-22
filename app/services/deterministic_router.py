import re
from typing import Any

from app.schemas.triage import TicketTriageRequest
from app.services.queue_mapping import queue_family


ROUTER_KEYWORDS: dict[str, list[str]] = {
    "billing": [
        "payment",
        "payments",
        "failed payment",
        "checkout",
        "card",
        "credit card",
        "debit card",
        "invoice",
        "billing",
        "refund",
        "charge",
        "charged",
        "subscription",
        "transaction",
        "payment gateway",
        "money",
        "price",
    ],
    "technical": [
        "api",
        "integration",
        "webhook",
        "bug",
        "error",
        "exception",
        "crash",
        "outage",
        "server",
        "timeout",
        "latency",
        "system down",
        "not loading",
        "technical",
        "logs",
        "deployment",
        "database",
    ],
    "account": [
        "login",
        "sign in",
        "signin",
        "password",
        "reset password",
        "account locked",
        "locked out",
        "access",
        "authentication",
        "auth",
        "mfa",
        "otp",
        "profile",
        "credentials",
    ],
    "order": [
        "order",
        "delivery",
        "shipping",
        "shipment",
        "tracking",
        "return",
        "package",
        "parcel",
        "delayed",
        "cancel order",
        "missing item",
        "damaged item",
        "fulfillment",
    ],
    "security": [
        "security",
        "fraud",
        "suspicious",
        "breach",
        "phishing",
        "compromised",
        "unauthorized",
        "hacked",
        "malware",
        "data leak",
    ],
}


SPECIALIST_PROFILE_NAMES: dict[str, str] = {
    "billing": "Billing Specialist",
    "technical": "IT Support Specialist",
    "account": "Account Access Specialist",
    "order": "Order Operations Specialist",
    "security": "Security Escalation Specialist",
    "general": "General Support Specialist",
}


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return re.sub(r"\s+", " ", value.lower()).strip()


def _combined_ticket_text(payload: TicketTriageRequest) -> str:
    return _normalize_text(
        f"{payload.subject or ''}\n{payload.body or ''}\n{payload.business_type_hint or ''}"
    )


def _find_keyword_matches(text: str) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = {}

    for family, keywords in ROUTER_KEYWORDS.items():
        matched = []

        for keyword in keywords:
            normalized_keyword = _normalize_text(keyword)

            if normalized_keyword and normalized_keyword in text:
                matched.append(keyword)

        if matched:
            matches[family] = matched

    return matches


def _score_families(matches: dict[str, list[str]]) -> dict[str, int]:
    scores: dict[str, int] = {}

    for family, matched_keywords in matches.items():
        score = 0

        for keyword in matched_keywords:
            # Multi-word phrases are stronger signals than single generic words.
            if " " in keyword:
                score += 3
            else:
                score += 1

        scores[family] = score

    return scores


def _select_route_family(scores: dict[str, int]) -> str:
    if not scores:
        return "general"

    sorted_scores = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    top_family, top_score = sorted_scores[0]

    if top_score <= 0:
        return "general"

    return top_family


def _confidence_hint(scores: dict[str, int], selected_family: str) -> str:
    if selected_family == "general":
        return "low"

    selected_score = scores.get(selected_family, 0)

    if selected_score >= 5:
        return "high"

    if selected_score >= 2:
        return "medium"

    return "low"


def _preferred_queue_for_family(
    route_family: str,
    allowed_queues: list[str],
) -> str | None:
    if not allowed_queues:
        return None

    # Security incidents usually belong to Security if present,
    # otherwise IT Support is a safer fallback.
    if route_family == "security":
        for queue in allowed_queues:
            if "security" in queue.lower():
                return queue

        for queue in allowed_queues:
            if queue_family(queue) == "technical":
                return queue

    for queue in allowed_queues:
        if queue_family(queue) == route_family:
            return queue

    return None


def route_ticket(
    payload: TicketTriageRequest,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """
    Deterministic pre-router.

    This does not call the LLM.
    It uses low-cost rules to choose a specialist prompt profile before the LLM runs.
    """

    text = _combined_ticket_text(payload)
    matches = _find_keyword_matches(text)
    scores = _score_families(matches)

    route_family = _select_route_family(scores)
    confidence_hint = _confidence_hint(scores, route_family)

    allowed_queues = catalog.get("queues", []) or []
    preferred_queue_hint = _preferred_queue_for_family(
        route_family=route_family,
        allowed_queues=allowed_queues,
    )

    matched_keywords = matches.get(route_family, [])

    if route_family == "general":
        route_reason = "No strong deterministic routing signal found."
    else:
        route_reason = (
            f"Matched {route_family} keywords: "
            f"{', '.join(matched_keywords[:6])}"
        )

    return {
        "route_family": route_family,
        "specialist_profile": SPECIALIST_PROFILE_NAMES.get(
            route_family,
            "General Support Specialist",
        ),
        "preferred_queue_hint": preferred_queue_hint,
        "confidence_hint": confidence_hint,
        "route_reason": route_reason,
        "matched_keywords": matched_keywords,
        "family_scores": scores,
    }