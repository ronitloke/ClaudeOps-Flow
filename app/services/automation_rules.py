from typing import Any, Dict

from app.schemas.triage import TicketTriageRequest, TicketTriageResponse


HIGH_RISK_QUEUES = {"IT Support", "Billing", "Payments", "Security"}
HIGH_RISK_INTENTS = {"payment_issue", "refund_request", "security_incident", "account_locked"}


def build_escalation_decision(
    payload: TicketTriageRequest,
    triage_response: TicketTriageResponse,
) -> Dict[str, Any]:
    reasons: list[str] = []

    if triage_response.predicted_priority and triage_response.predicted_priority.lower() == "high":
        reasons.append("high_priority")

    if triage_response.sla_risk:
        reasons.append("sla_risk")

    if triage_response.needs_human_review:
        reasons.append("needs_human_review")

    if triage_response.predicted_queue in HIGH_RISK_QUEUES:
        reasons.append("high_risk_queue")

    if triage_response.likely_intent in HIGH_RISK_INTENTS:
        reasons.append("high_risk_intent")

    should_escalate = len(reasons) > 0

    if triage_response.predicted_queue in {"IT Support", "Security"}:
        target_team = "engineering_ops"
    elif triage_response.predicted_queue in {"Billing", "Payments"}:
        target_team = "finance_ops"
    else:
        target_team = "support_ops"

    urgency_level = "critical" if triage_response.sla_risk and triage_response.predicted_priority == "high" else (
        "high" if triage_response.predicted_priority == "high" else "normal"
    )

    return {
        "should_escalate": should_escalate,
        "target_team": target_team,
        "urgency_level": urgency_level,
        "reasons": reasons,
        "send_slack_alert": should_escalate,
        "forward_to_webhook": True,
        "create_internal_case": should_escalate,
        "summary_label": f"{triage_response.predicted_queue} | {triage_response.predicted_priority}",
    }