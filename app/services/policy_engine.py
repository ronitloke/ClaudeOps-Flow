from typing import Any


EXTERNAL_ACTIONS = {
    "zapier_workflow",
    "make_workflow",
    "generic_webhook",
}

INTERNAL_ACTIONS = {
    "slack_alert",
}

ACTION_CHANNELS = {
    "slack_alert": "slack",
    "generic_webhook": "webhook",
    "zapier_workflow": "zapier",
    "make_workflow": "make",
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _policy_decision(
    action_key: str,
    allowed: bool,
    rule: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "action_key": action_key,
        "channel": ACTION_CHANNELS.get(action_key, action_key),
        "allowed": allowed,
        "decision": "allowed" if allowed else "blocked",
        "policy_rule": rule,
        "reason": reason,
    }


def evaluate_outbound_action_policy(
    action_key: str,
    actor: str | None,
    actor_role: str | None,
    triage_result: dict[str, Any],
    automation_decision: dict[str, Any],
    approval_status: str | None,
) -> dict[str, Any]:
    """
    Lightweight enterprise-style policy engine.

    No LLM call.
    No external API call.
    Just deterministic policy control before outbound actions.
    """

    role = _norm(actor_role)
    queue = _norm(triage_result.get("predicted_queue"))
    priority = _norm(triage_result.get("predicted_priority"))
    approval = _norm(approval_status)

    if approval not in {"approved", "not_required"}:
        return _policy_decision(
            action_key=action_key,
            allowed=False,
            rule="approval_required_before_action",
            reason="Outbound action blocked because approval is not complete.",
        )

    if action_key in INTERNAL_ACTIONS:
        if role in {"admin", "ops_analyst", "system"}:
            return _policy_decision(
                action_key=action_key,
                allowed=True,
                rule="internal_alert_allowed_for_ops_roles",
                reason="Slack/internal alert is allowed for admin, ops analyst, or system.",
            )

        return _policy_decision(
            action_key=action_key,
            allowed=False,
            rule="internal_alert_role_blocked",
            reason=f"Role '{actor_role}' is not allowed to trigger internal alerts.",
        )

    if action_key in EXTERNAL_ACTIONS:
        if role != "admin":
            return _policy_decision(
                action_key=action_key,
                allowed=False,
                rule="external_actions_admin_only",
                reason="External automation actions are restricted to admin users.",
            )

        if "security" in queue:
            return _policy_decision(
                action_key=action_key,
                allowed=False,
                rule="security_queue_external_block",
                reason="Security queue cannot trigger external workflow actions automatically.",
            )

        if "general" in queue and priority != "high":
            return _policy_decision(
                action_key=action_key,
                allowed=False,
                rule="general_queue_external_requires_high_priority",
                reason="General queue can trigger external actions only for high-priority cases.",
            )

        return _policy_decision(
            action_key=action_key,
            allowed=True,
            rule="admin_external_action_allowed",
            reason="Admin is allowed to trigger this external action for the current queue.",
        )

    return _policy_decision(
        action_key=action_key,
        allowed=False,
        rule="unknown_action_blocked",
        reason=f"Unknown outbound action '{action_key}' is blocked by default.",
    )


def evaluate_outbound_policies(
    actor: str | None,
    actor_role: str | None,
    triage_result: dict[str, Any],
    automation_decision: dict[str, Any],
    approval_status: str | None,
) -> dict[str, Any]:
    action_keys = [
        "slack_alert",
        "generic_webhook",
        "zapier_workflow",
        "make_workflow",
    ]

    return {
        action_key: evaluate_outbound_action_policy(
            action_key=action_key,
            actor=actor,
            actor_role=actor_role,
            triage_result=triage_result,
            automation_decision=automation_decision,
            approval_status=approval_status,
        )
        for action_key in action_keys
    }