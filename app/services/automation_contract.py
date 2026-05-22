from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


CONTRACT_VERSION = "v1"
SCHEMA_NAME = "claudeops.outbound_automation"


def _safe_text(value: Any, fallback: str = "N/A") -> str:
    if value is None:
        return fallback

    text = str(value).strip()
    return text if text else fallback


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_policy_flags(
    policy_decisions: dict[str, Any] | None,
    actor: str | None,
    actor_role: str | None,
) -> dict[str, Any]:
    policy_decisions = policy_decisions or {}

    allowed_actions: list[str] = []
    blocked_actions: list[str] = []

    for action_key, decision in policy_decisions.items():
        if decision.get("allowed"):
            allowed_actions.append(action_key)
        else:
            blocked_actions.append(action_key)

    external_action_keys = {
        "generic_webhook",
        "zapier_workflow",
        "make_workflow",
    }

    external_actions_allowed = any(
        action_key in external_action_keys
        for action_key in allowed_actions
    )

    external_actions_blocked = any(
        action_key in external_action_keys
        for action_key in blocked_actions
    )

    return {
        "actor": actor,
        "actor_role": actor_role,
        "allowed_actions": allowed_actions,
        "blocked_actions": blocked_actions,
        "external_actions_allowed": external_actions_allowed,
        "external_actions_blocked": external_actions_blocked,
        "action_decisions": policy_decisions,
    }


def build_outbound_automation_contract(
    request_id: str,
    log_id: int | None,
    event_type: str,
    ticket: dict[str, Any],
    triage_result: dict[str, Any],
    automation_decision: dict[str, Any],
    downstream_actions: dict[str, Any],
    approval: dict[str, Any],
    policy_flags: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Stable cross-platform outbound automation contract.

    This object is safe to map in Zapier, Make, Slack, webhooks,
    or future workflow tools because the shape stays stable.
    """

    policy_flags = policy_flags or {
        "actor": approval.get("approved_by"),
        "actor_role": metadata.get("actor_role") if metadata else None,
        "allowed_actions": [],
        "blocked_actions": [],
        "external_actions_allowed": None,
        "external_actions_blocked": None,
        "action_decisions": {},
    }

    metadata = metadata or {}

    return {
        "contract_version": CONTRACT_VERSION,
        "schema_name": SCHEMA_NAME,
        "contract_id": str(uuid4()),
        "contract_created_at": _utc_now(),

        "source": "claudeops_flow",
        "event_type": event_type,
        "request_id": request_id,
        "log_id": log_id,

        "ticket": {
            "subject": _safe_text(ticket.get("subject")),
            "body": _safe_text(ticket.get("body")),
            "language_hint": ticket.get("language_hint"),
            "business_type_hint": ticket.get("business_type_hint"),
            "include_draft_response": bool(ticket.get("include_draft_response", True)),
        },

        "triage_result": {
            "summary": triage_result.get("summary"),
            "detected_language": triage_result.get("detected_language"),
            "predicted_type": triage_result.get("predicted_type"),
            "predicted_queue": triage_result.get("predicted_queue"),
            "predicted_priority": triage_result.get("predicted_priority"),
            "predicted_business_type": triage_result.get("predicted_business_type"),
            "likely_intent": triage_result.get("likely_intent"),
            "urgency_reason": triage_result.get("urgency_reason"),
            "sla_risk": bool(triage_result.get("sla_risk")),
            "needs_human_review": bool(triage_result.get("needs_human_review")),
            "recommended_action": triage_result.get("recommended_action"),
            "draft_response": triage_result.get("draft_response"),
            "confidence": triage_result.get("confidence"),
            "structured_fields": triage_result.get("structured_fields") or {},
        },

        "automation_decision": {
            "should_escalate": bool(automation_decision.get("should_escalate")),
            "target_team": automation_decision.get("target_team"),
            "urgency_level": automation_decision.get("urgency_level"),
            "reasons": automation_decision.get("reasons", []),
        },

        "approval": approval,

        "policy_flags": policy_flags,

        "downstream_actions": downstream_actions,

        "metadata": {
            "provider": metadata.get("provider"),
            "model_name": metadata.get("model_name"),
            "prompt_version": metadata.get("prompt_version"),
            "model_version": metadata.get("model_version"),
            "actor_role": metadata.get("actor_role"),
            "environment": metadata.get("environment", "local_demo"),
            "contract_note": (
                "Map integrations from automation_contract.downstream_actions "
                "for stable Zapier/Make/Slack workflows."
            ),
        },
    }


def attach_policy_flags_to_contract(
    workflow_payload: dict[str, Any],
    policy_decisions: dict[str, Any],
    actor: str | None,
    actor_role: str | None,
) -> dict[str, Any]:
    policy_flags = build_policy_flags(
        policy_decisions=policy_decisions,
        actor=actor,
        actor_role=actor_role,
    )

    workflow_payload["policy_flags"] = policy_flags

    if isinstance(workflow_payload.get("automation_contract"), dict):
        workflow_payload["automation_contract"]["policy_flags"] = policy_flags
        workflow_payload["automation_contract"]["metadata"]["actor_role"] = actor_role

    return workflow_payload


def build_sample_outbound_contract() -> dict[str, Any]:
    sample_ticket = {
        "subject": "Critical payment issue affecting customer orders",
        "body": "Several customers cannot complete checkout and payment failures are increasing.",
        "language_hint": "en",
        "business_type_hint": "Tech Online Store",
        "include_draft_response": True,
    }

    sample_triage = {
        "summary": "Multiple customers are experiencing payment failures during checkout.",
        "detected_language": "en",
        "predicted_type": "Incident",
        "predicted_queue": "Billing and Payments",
        "predicted_priority": "high",
        "predicted_business_type": "Tech Online Store",
        "likely_intent": "payment_issue",
        "urgency_reason": "Payment outage affecting customers and revenue.",
        "sla_risk": True,
        "needs_human_review": True,
        "recommended_action": "Escalate to payment operations and inspect gateway logs.",
        "draft_response": "We are aware of checkout issues and are investigating urgently.",
        "confidence": 0.95,
        "structured_fields": {
            "issue_keywords": ["payment_failures", "checkout_outage"],
        },
    }

    sample_decision = {
        "should_escalate": True,
        "target_team": "Billing and Payments",
        "urgency_level": "critical",
        "reasons": ["sla_risk", "high_priority"],
    }

    sample_downstream_actions = {
        "send_email": {
            "subject": "Escalated Ticket | Billing and Payments | HIGH",
            "body": "Escalated ticket approved for action...",
        },
        "create_trello_card": {
            "card_name": "[HIGH] Critical payment issue affecting customer orders",
            "card_description": "Request ID: demo-contract-request...",
        },
        "append_google_sheet_row": {
            "request_id": "demo-contract-request",
            "subject": sample_ticket["subject"],
            "queue": "Billing and Payments",
            "priority": "high",
            "intent": "payment_issue",
            "sla_risk": True,
            "target_team": "Billing and Payments",
            "urgency_level": "critical",
            "recommended_action": sample_triage["recommended_action"],
            "approved_at": _utc_now(),
        },
        "send_slack_alert": {
            "text": "🚨 Escalated Ticket Approved...",
        },
    }

    sample_policy_flags = {
        "actor": "admin",
        "actor_role": "admin",
        "allowed_actions": ["slack_alert", "zapier_workflow", "make_workflow"],
        "blocked_actions": [],
        "external_actions_allowed": True,
        "external_actions_blocked": False,
        "action_decisions": {},
    }

    return build_outbound_automation_contract(
        request_id="demo-contract-request",
        log_id=1,
        event_type="approved_ticket_automation",
        ticket=sample_ticket,
        triage_result=sample_triage,
        automation_decision=sample_decision,
        downstream_actions=sample_downstream_actions,
        approval={
            "approval_status": "approved",
            "approval_required": True,
            "approved_by": "admin",
            "approved_at": _utc_now(),
        },
        policy_flags=sample_policy_flags,
        metadata={
            "provider": "claude",
            "model_name": "claude-haiku-4-5",
            "prompt_version": "triage_v1_router_specialist",
            "model_version": "claude-haiku-4-5",
            "actor_role": "admin",
        },
    )