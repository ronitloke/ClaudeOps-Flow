from typing import Any, Dict

import requests

from app.core.settings import get_settings
from app.schemas.triage import TicketTriageRequest, TicketTriageResponse
from app.services.automation_rules import build_escalation_decision
from app.services.automation_service import build_workflow_payload, execute_automation_hooks


def _ticket_to_dict(payload: TicketTriageRequest) -> dict[str, Any]:
    return payload.model_dump()


def _triage_to_dict(triage_response: TicketTriageResponse) -> dict[str, Any]:
    return triage_response.model_dump()


def _has_any_automation_action(
    decision: dict[str, Any],
    enable_zapier_hook: bool,
    enable_make_hook: bool,
) -> bool:
    return bool(
        decision.get("send_slack_alert")
        or decision.get("forward_to_webhook")
        or (enable_zapier_hook and decision.get("should_escalate"))
        or (enable_make_hook and decision.get("forward_to_webhook"))
    )


# ---------------------------------------------------------------------
# Compatibility helpers
# These keep old imports safe if any older part of the app still calls
# build_slack_payload / build_zapier_payload / build_make_payload.
# The actual source of truth is now automation_service.py.
# ---------------------------------------------------------------------

def _build_downstream_actions(
    payload: TicketTriageRequest,
    triage_response: TicketTriageResponse,
    request_id: str,
    automation_decision: Dict[str, Any],
) -> Dict[str, Any]:
    workflow_payload = build_workflow_payload(
        request_id=request_id,
        log_id=None,
        ticket=_ticket_to_dict(payload),
        triage_result=_triage_to_dict(triage_response),
        automation_decision=automation_decision,
        approved_at=None,
        approved_by="system",
        approval_status="not_required",
    )

    return workflow_payload["downstream_actions"]


def build_slack_payload(
    payload: TicketTriageRequest,
    triage_response: TicketTriageResponse,
    request_id: str,
    log_id: int,
    automation_decision: Dict[str, Any],
) -> Dict[str, Any]:
    workflow_payload = build_workflow_payload(
        request_id=request_id,
        log_id=log_id,
        ticket=_ticket_to_dict(payload),
        triage_result=_triage_to_dict(triage_response),
        automation_decision=automation_decision,
        approved_at=None,
        approved_by="system",
        approval_status="not_required",
    )

    return workflow_payload["downstream_actions"]["send_slack_alert"]


def build_generic_webhook_payload(
    payload: TicketTriageRequest,
    triage_response: TicketTriageResponse,
    request_id: str,
    log_id: int,
    automation_decision: Dict[str, Any],
) -> Dict[str, Any]:
    return build_workflow_payload(
        request_id=request_id,
        log_id=log_id,
        ticket=_ticket_to_dict(payload),
        triage_result=_triage_to_dict(triage_response),
        automation_decision=automation_decision,
        approved_at=None,
        approved_by="system",
        approval_status="not_required",
    )


def build_zapier_payload(
    payload: TicketTriageRequest,
    triage_response: TicketTriageResponse,
    request_id: str,
    log_id: int,
    automation_decision: Dict[str, Any],
) -> Dict[str, Any]:
    return build_generic_webhook_payload(
        payload=payload,
        triage_response=triage_response,
        request_id=request_id,
        log_id=log_id,
        automation_decision=automation_decision,
    )


def build_make_payload(
    payload: TicketTriageRequest,
    triage_response: TicketTriageResponse,
    request_id: str,
    log_id: int,
    automation_decision: Dict[str, Any],
) -> Dict[str, Any]:
    return build_generic_webhook_payload(
        payload=payload,
        triage_response=triage_response,
        request_id=request_id,
        log_id=log_id,
        automation_decision=automation_decision,
    )


def post_json(url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(url, json=body, timeout=20)
    return {
        "status_code": response.status_code,
        "success": 200 <= response.status_code < 300,
        "response_text": response.text[:1000],
    }


# ---------------------------------------------------------------------
# Main dispatcher
# This is used for automatic post-triage automation when approval is
# not required. It now calls automation_service.py so policy rules,
# clean payloads, and audit logs are applied consistently.
# ---------------------------------------------------------------------

def run_post_triage_automation(
    payload: TicketTriageRequest,
    triage_response: TicketTriageResponse,
    request_id: str,
    log_id: int,
) -> Dict[str, Any]:
    settings = get_settings()

    decision = build_escalation_decision(payload, triage_response)

    if not settings.enable_automation_hooks:
        return {
            "enabled": False,
            "decision": decision,
            "automation_ready": False,
            "approval_required": False,
            "approval_status": "not_required",
            "slack_delivery": None,
            "webhook_delivery": None,
            "zapier_delivery": None,
            "make_delivery": None,
            "policy_decisions": None,
            "note": "Automation hooks disabled in environment settings.",
            "error": None,
        }

    has_action = _has_any_automation_action(
        decision=decision,
        enable_zapier_hook=settings.enable_zapier_hook,
        enable_make_hook=settings.enable_make_hook,
    )

    if not has_action:
        return {
            "enabled": True,
            "decision": decision,
            "automation_ready": False,
            "approval_required": False,
            "approval_status": "not_required",
            "slack_delivery": None,
            "webhook_delivery": None,
            "zapier_delivery": None,
            "make_delivery": None,
            "policy_decisions": None,
            "note": "No downstream automation action required for this ticket.",
            "error": None,
        }

    automation_result = execute_automation_hooks(
        request_id=request_id,
        log_id=log_id,
        ticket=_ticket_to_dict(payload),
        triage_result=_triage_to_dict(triage_response),
        automation_decision=decision,
        approved_at=None,
        approved_by="system",
        approval_status="not_required",
        actor_role="system",
    )

    automation_result["enabled"] = True
    automation_result["automation_ready"] = True
    automation_result["approval_required"] = False
    automation_result["approval_status"] = "not_required"

    return automation_result    