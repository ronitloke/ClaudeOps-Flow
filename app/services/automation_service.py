import os
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv
from app.db.database import SessionLocal
from app.repositories.policy_audit_repository import save_outbound_action_audit
from app.services.policy_engine import evaluate_outbound_policies
from app.services.automation_contract import (attach_policy_flags_to_contract,build_outbound_automation_contract,)
load_dotenv()


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


ENABLE_AUTOMATION_HOOKS = _env_flag("ENABLE_AUTOMATION_HOOKS", True)
ENABLE_ZAPIER_HOOK = _env_flag("ENABLE_ZAPIER_HOOK", False)
ENABLE_MAKE_HOOK = _env_flag("ENABLE_MAKE_HOOK", False)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()
GENERIC_WEBHOOK_URL = os.getenv("GENERIC_WEBHOOK_URL", "").strip()
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL", "").strip()
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "").strip()


def _safe_text(value: Any, fallback: str = "N/A") -> str:
    if value is None:
        return fallback

    text = str(value).strip()
    return text if text else fallback


def _yes_no(value: Any) -> str:
    return "Yes" if bool(value) else "No"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def determine_approval_state(
    triage_result: dict[str, Any],
    automation_decision: dict[str, Any],
) -> dict[str, Any]:
    priority = str(triage_result.get("predicted_priority") or "").strip().lower()

    reasons: list[str] = []

    if automation_decision.get("should_escalate"):
        reasons.append("escalation_planned")

    if triage_result.get("sla_risk"):
        reasons.append("sla_risk")

    if priority == "high":
        reasons.append("high_priority")

    if triage_result.get("needs_human_review"):
        reasons.append("needs_human_review")

    required = bool(automation_decision.get("should_escalate")) and any(
        [
            bool(triage_result.get("sla_risk")),
            priority == "high",
            bool(triage_result.get("needs_human_review")),
        ]
    )

    return {
        "required": required,
        "status": "pending" if required else "not_required",
        "reason": ", ".join(reasons) if reasons else None,
        "automation_executed": not required,
    }


def _build_email_body(context: dict[str, Any]) -> str:
    ticket = context.get("ticket") or {}
    triage_result = context.get("triage_result") or {}
    decision = context.get("automation_decision") or {}

    approval_status = _safe_text(context.get("approval_status"), "approved")

    if approval_status == "approved":
        title = "Escalated ticket approved for action"
    elif approval_status == "not_required":
        title = "Automation-ready ticket routed for action"
    else:
        title = "ClaudeOps Flow automation event"

    return (
        f"{title}\n\n"
        "Ticket Details\n"
        "--------------\n"
        f"Request ID: {_safe_text(context.get('request_id'))}\n"
        f"Subject: {_safe_text(ticket.get('subject'))}\n"
        f"Queue: {_safe_text(triage_result.get('predicted_queue'))}\n"
        f"Priority: {_safe_text(triage_result.get('predicted_priority'))}\n"
        f"Intent: {_safe_text(triage_result.get('likely_intent'))}\n"
        f"SLA Risk: {_yes_no(triage_result.get('sla_risk'))}\n"
        f"Human Review Needed: {_yes_no(triage_result.get('needs_human_review'))}\n\n"
        "Routing Decision\n"
        "----------------\n"
        f"Target Team: {_safe_text(decision.get('target_team'))}\n"
        f"Urgency Level: {_safe_text(decision.get('urgency_level'))}\n"
        f"Should Escalate: {_yes_no(decision.get('should_escalate'))}\n\n"
        "Approval / Execution\n"
        "--------------------\n"
        f"Approval Status: {approval_status}\n"
        f"Approved By: {_safe_text(context.get('approved_by'))}\n"
        f"Approved At: {_safe_text(context.get('approved_at'))}\n"
        f"Executed At: {_safe_text(context.get('executed_at'))}\n\n"
        "Summary\n"
        "-------\n"
        f"{_safe_text(triage_result.get('summary'))}\n\n"
        "Recommended Action\n"
        "------------------\n"
        f"{_safe_text(triage_result.get('recommended_action'))}\n\n"
        "Draft Response\n"
        "--------------\n"
        f"{_safe_text(triage_result.get('draft_response'))}"
    )


def _build_slack_text(context: dict[str, Any]) -> str:
    ticket = context.get("ticket") or {}
    triage_result = context.get("triage_result") or {}
    decision = context.get("automation_decision") or {}

    return (
        "🚨 ClaudeOps Flow Escalation\n\n"
        f"Request ID: {_safe_text(context.get('request_id'))}\n"
        f"Subject: {_safe_text(ticket.get('subject'))}\n"
        f"Queue: {_safe_text(triage_result.get('predicted_queue'))}\n"
        f"Priority: {_safe_text(triage_result.get('predicted_priority'))}\n"
        f"SLA Risk: {_yes_no(triage_result.get('sla_risk'))}\n"
        f"Target Team: {_safe_text(decision.get('target_team'))}\n"
        f"Urgency: {_safe_text(decision.get('urgency_level'))}\n"
        f"Approval Status: {_safe_text(context.get('approval_status'))}\n"
        f"Approved By: {_safe_text(context.get('approved_by'))}\n"
        f"Approved At: {_safe_text(context.get('approved_at'))}\n\n"
        f"Recommended Action: {_safe_text(triage_result.get('recommended_action'))}"
    )


def build_workflow_payload(
    request_id: str,
    log_id: int | None,
    ticket: dict[str, Any],
    triage_result: dict[str, Any],
    automation_decision: dict[str, Any],
    approved_at: str | None = None,
    approved_by: str | None = None,
    approval_status: str = "approved",
) -> dict[str, Any]:
    subject = _safe_text(ticket.get("subject"), "Untitled ticket")

    queue = _safe_text(triage_result.get("predicted_queue"))
    priority = _safe_text(triage_result.get("predicted_priority"), "medium")
    priority_label = priority.upper()

    intent = _safe_text(triage_result.get("likely_intent"))
    target_team = _safe_text(automation_decision.get("target_team"), "support_ops")
    urgency_level = _safe_text(automation_decision.get("urgency_level"), "normal")
    recommended_action = _safe_text(triage_result.get("recommended_action"))

    executed_at = _iso_now()

    # Guaranteed non-empty values for Zapier samples
    approved_at_value = approved_at or executed_at
    approved_by_value = approved_by or "system"

    context_payload = {
        "request_id": request_id,
        "log_id": log_id,
        "ticket": ticket,
        "triage_result": triage_result,
        "automation_decision": automation_decision,
        "approval_status": approval_status,
        "approved_at": approved_at_value,
        "approved_by": approved_by_value,
        "executed_at": executed_at,
    }

    clean_body = _build_email_body(context_payload)

    sheet_row = {
        "request_id": request_id,
        "subject": subject,
        "queue": queue,
        "priority": priority,
        "intent": intent,
        "sla_risk": bool(triage_result.get("sla_risk")),
        "target_team": target_team,
        "urgency_level": urgency_level,
        "recommended_action": recommended_action,
        "approved_at": approved_at_value,

        # Backup Zapier-friendly aliases
        "approvedAt": approved_at_value,
        "approved_timestamp": approved_at_value,
        "executed_at": executed_at,
    }

    email_payload = {
        "subject": f"Escalated Ticket | {queue} | {priority_label}",
        "body": clean_body,
    }

    trello_payload = {
        "card_name": f"[{priority_label}] {subject}",
        "description": clean_body,

        # Zapier compatibility aliases
        "card_description": clean_body,
        "card_list": target_team,

        # Keep labels short only
        "labels": [priority_label, urgency_level],
        "card_labels": [priority_label, urgency_level],
    }

    slack_payload = {
        "text": _build_slack_text(context_payload),
    }

    base_payload = {
        "source": "claudeops_flow",
        "event_type": (
            "approved_ticket_automation"
            if approval_status == "approved"
            else "post_triage_automation"
        ),
        "request_id": request_id,
        "log_id": log_id,

        "approval_status": approval_status,
        "approved_by": approved_by_value,
        "approved_at": approved_at_value,
        "executed_at": executed_at,

        # Contract identity
        "contract_version": "v1",
        "schema_name": "claudeops.outbound_automation",

        # Flat fields for easy Zapier / Make mapping
        "subject": subject,
        "queue": queue,
        "priority": priority,
        "intent": intent,
        "sla_risk": bool(triage_result.get("sla_risk")),
        "target_team": target_team,
        "urgency_level": urgency_level,
        "recommended_action": recommended_action,

        # Extra flat Google Sheets fallback fields
        "sheet_request_id": request_id,
        "sheet_subject": subject,
        "sheet_queue": queue,
        "sheet_priority": priority,
        "sheet_intent": intent,
        "sheet_sla_risk": bool(triage_result.get("sla_risk")),
        "sheet_target_team": target_team,
        "sheet_urgency_level": urgency_level,
        "sheet_recommended_action": recommended_action,
        "sheet_approved_at": approved_at_value,
        "sheet_approved_by": approved_by_value,
        "sheet_executed_at": executed_at,

        "ticket": ticket,
        "triage_result": triage_result,
        "automation_decision": automation_decision,

        # Clean downstream contracts
        "downstream_actions": {
            "create_trello_card": trello_payload,
            "send_email": email_payload,
            "append_google_sheet_row": sheet_row,
            "append_sheet_row": sheet_row,
            "send_slack_alert": slack_payload,
        },
    }

    base_payload["automation_contract"] = build_outbound_automation_contract(
        request_id=request_id,
        log_id=log_id,
        event_type=base_payload["event_type"],
        ticket=ticket,
        triage_result=triage_result,
        automation_decision=automation_decision,
        downstream_actions=base_payload["downstream_actions"],
        approval={
            "approval_required": approval_status == "approved",
            "approval_status": approval_status,
            "approved_by": approved_by_value,
            "approved_at": approved_at_value,
            "executed_at": executed_at,
        },
        policy_flags=None,
        metadata={
            "provider": triage_result.get("provider") or "claude",
            "model_name": triage_result.get("model_name") or "claude-haiku-4-5",
            "prompt_version": triage_result.get("prompt_version"),
            "model_version": triage_result.get("model_version"),
            "environment": "local_demo",
        },
    )

    return base_payload


def _post_json(url: str, payload: dict[str, Any], missing_reason: str) -> dict[str, Any]:
    if not url:
        return {
            "success": False,
            "skipped": True,
            "reason": missing_reason,
        }

    try:
        response = requests.post(url, json=payload, timeout=45)

        return {
            "success": response.ok,
            "skipped": False,
            "status_code": response.status_code,
            "response_text": response.text[:1000],
        }

    except Exception as exc:
        return {
            "success": False,
            "skipped": False,
            "error": str(exc),
        }

def _blocked_delivery(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": False,
        "skipped": True,
        "blocked_by_policy": True,
        "policy_rule": policy.get("policy_rule"),
        "reason": policy.get("reason"),
    }


def _save_policy_audit_safely(
    request_id: str,
    log_id: int | None,
    actor: str | None,
    actor_role: str | None,
    action_key: str,
    policy: dict[str, Any],
    triage_result: dict[str, Any],
    delivery_json: dict[str, Any],
) -> None:
    db = SessionLocal()

    try:
        save_outbound_action_audit(
            db=db,
            request_id=request_id,
            log_id=log_id,
            actor=actor,
            actor_role=actor_role,
            action_key=action_key,
            channel=policy.get("channel"),
            decision=policy.get("decision"),
            policy_rule=policy.get("policy_rule"),
            reason=policy.get("reason"),
            queue=triage_result.get("predicted_queue"),
            priority=triage_result.get("predicted_priority"),
            delivery_json=delivery_json,
        )
    except Exception as exc:
        print(f"Policy audit save failed for {action_key}: {exc}")
    finally:
        db.close()  

def execute_automation_hooks(
    request_id: str,
    log_id: int | None,
    ticket: dict[str, Any],
    triage_result: dict[str, Any],
    automation_decision: dict[str, Any],
    approved_at: str | None = None,
    approved_by: str | None = None,
    approval_status: str = "approved",
    actor_role: str = "admin",
) -> dict[str, Any]:
    workflow_payload = build_workflow_payload(
        request_id=request_id,
        log_id=log_id,
        ticket=ticket,
        triage_result=triage_result,
        automation_decision=automation_decision,
        approved_at=approved_at,
        approved_by=approved_by,
        approval_status=approval_status,
    )

    policy_decisions = evaluate_outbound_policies(
        actor=approved_by,
        actor_role=actor_role,
        triage_result=triage_result,
        automation_decision=automation_decision,
        approval_status=approval_status,
    )

    workflow_payload["policy"] = {
        "actor": approved_by,
        "actor_role": actor_role,
        "decisions": policy_decisions,
    }

    workflow_payload = attach_policy_flags_to_contract(
        workflow_payload=workflow_payload,
        policy_decisions=policy_decisions,
        actor=approved_by,
        actor_role=actor_role,
    )

    print("POLICY DECISIONS:")
    print(policy_decisions)

    result = {
        "decision": automation_decision,
        "status": "disabled" if not ENABLE_AUTOMATION_HOOKS else "executed",
        "payload_preview": workflow_payload,
        "policy_decisions": policy_decisions,
        "slack_delivery": {},
        "webhook_delivery": {},
        "zapier_delivery": {},
        "make_delivery": {},
        "error": None,
    }

    if not ENABLE_AUTOMATION_HOOKS:
        return result

    slack_policy = policy_decisions["slack_alert"]
    if slack_policy["allowed"]:
        result["slack_delivery"] = _post_json(
            SLACK_WEBHOOK_URL,
            workflow_payload["downstream_actions"]["send_slack_alert"],
            "SLACK_WEBHOOK_URL not configured",
        )
    else:
        result["slack_delivery"] = _blocked_delivery(slack_policy)

    _save_policy_audit_safely(
        request_id=request_id,
        log_id=log_id,
        actor=approved_by,
        actor_role=actor_role,
        action_key="slack_alert",
        policy=slack_policy,
        triage_result=triage_result,
        delivery_json=result["slack_delivery"],
    )

    webhook_policy = policy_decisions["generic_webhook"]
    if webhook_policy["allowed"]:
        result["webhook_delivery"] = _post_json(
            GENERIC_WEBHOOK_URL,
            workflow_payload,
            "GENERIC_WEBHOOK_URL not configured",
        )
    else:
        result["webhook_delivery"] = _blocked_delivery(webhook_policy)

    _save_policy_audit_safely(
        request_id=request_id,
        log_id=log_id,
        actor=approved_by,
        actor_role=actor_role,
        action_key="generic_webhook",
        policy=webhook_policy,
        triage_result=triage_result,
        delivery_json=result["webhook_delivery"],
    )

    zapier_policy = policy_decisions["zapier_workflow"]
    if ENABLE_ZAPIER_HOOK:
        if zapier_policy["allowed"]:
            result["zapier_delivery"] = _post_json(
                ZAPIER_WEBHOOK_URL,
                workflow_payload,
                "ZAPIER_WEBHOOK_URL not configured",
            )
        else:
            result["zapier_delivery"] = _blocked_delivery(zapier_policy)

        _save_policy_audit_safely(
            request_id=request_id,
            log_id=log_id,
            actor=approved_by,
            actor_role=actor_role,
            action_key="zapier_workflow",
            policy=zapier_policy,
            triage_result=triage_result,
            delivery_json=result["zapier_delivery"],
        )

    make_policy = policy_decisions["make_workflow"]
    if ENABLE_MAKE_HOOK:
        if make_policy["allowed"]:
            result["make_delivery"] = _post_json(
                MAKE_WEBHOOK_URL,
                workflow_payload,
                "MAKE_WEBHOOK_URL not configured",
            )
        else:
            result["make_delivery"] = _blocked_delivery(make_policy)

        _save_policy_audit_safely(
            request_id=request_id,
            log_id=log_id,
            actor=approved_by,
            actor_role=actor_role,
            action_key="make_workflow",
            policy=make_policy,
            triage_result=triage_result,
            delivery_json=result["make_delivery"],
        )

    errors: list[str] = []

    for key in ["slack_delivery", "webhook_delivery", "zapier_delivery", "make_delivery"]:
        delivery_result = result.get(key) or {}

        if delivery_result and not delivery_result.get("success") and not delivery_result.get("skipped"):
            errors.append(
                delivery_result.get("error")
                or delivery_result.get("response_text")
                or key
            )

    result["error"] = " | ".join(errors) if errors else None

    return result