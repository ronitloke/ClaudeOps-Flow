from app.schemas.triage import TicketTriageRequest
from app.services.queue_mapping import queue_family


PROMPT_VERSION = "triage_v1.3_router_specialists"


SPECIALIST_GUIDANCE = {
    "billing": """
Billing Specialist guidance:
- Focus on payment failures, refunds, invoice issues, charges, subscriptions, checkout blocks, and revenue-impacting problems.
- If the issue mentions failed payments, checkout failures, billing, invoice, refund, or card transaction problems, strongly prefer the billing/payment queue when it exists.
- SLA risk should be true when customer transactions, revenue, checkout, or payment processing are blocked.
- Recommended action should mention payment gateway, transaction logs, billing review, or finance/payment operations when relevant.
""".strip(),
    "technical": """
IT Support Specialist guidance:
- Focus on bugs, API failures, integration errors, outages, latency, logs, backend errors, database issues, and service degradation.
- If the issue mentions API, system outage, errors, crashes, timeout, integration, webhook, or technical logs, strongly prefer IT/Technical Support when it exists.
- SLA risk should be true when a system outage or customer-facing technical degradation is described.
- Recommended action should mention logs, service health, engineering investigation, or incident escalation when relevant.
""".strip(),
    "account": """
Account Access Specialist guidance:
- Focus on login failures, password resets, account lockouts, authentication, MFA/OTP, credentials, and access problems.
- If the issue mentions login, password, locked account, access denied, authentication, MFA, or OTP, strongly prefer Account Support when it exists.
- Human review should be true for repeated access failures or suspected account compromise.
- Recommended action should mention account verification, access checks, password reset, or authentication troubleshooting when relevant.
""".strip(),
    "order": """
Order Operations Specialist guidance:
- Focus on order status, delivery, shipping, returns, tracking, missing items, damaged items, cancellations, and fulfillment.
- If the issue mentions delivery, shipment, tracking, returns, damaged package, or missing item, strongly prefer Order Support when it exists.
- SLA risk should be true when there is a high-impact delivery failure or many customers/orders are affected.
- Recommended action should mention order lookup, fulfillment review, carrier/shipping investigation, or customer update when relevant.
""".strip(),
    "security": """
Security Escalation Specialist guidance:
- Focus on suspicious activity, fraud, unauthorized access, account compromise, phishing, breach, malware, or data leak.
- Security issues should usually require human review.
- SLA risk should be true when unauthorized access, data exposure, or fraud is possible.
- Recommended action should mention security escalation, account protection, investigation, and immediate containment when relevant.
""".strip(),
    "general": """
General Support Specialist guidance:
- Use this profile when no strong deterministic signal is found.
- Keep the classification conservative.
- Choose the most appropriate allowed queue based on the ticket text.
- Avoid over-escalation unless the ticket clearly indicates SLA risk, high priority, or human review.
""".strip(),
}


def _build_queue_guidance(queues: list[str]) -> str:
    examples = []

    families = {
        "billing": "payment failures, refunds, invoices, charges, subscriptions",
        "technical": "bugs, outages, system errors, integrations, API issues",
        "account": "login issues, password resets, access problems, locked accounts",
        "order": "delivery issues, order updates, shipment tracking, returns",
        "general": "general questions, unclear requests, non-specialized support",
    }

    for family, description in families.items():
        family_queues = [q for q in queues if queue_family(q) == family]
        if family_queues:
            examples.append(f'- Route {description} to "{family_queues[0]}".')

    if not examples:
        return ""

    return "\n".join(examples)


def _build_specialist_guidance(route_context: dict | None) -> str:
    if not route_context:
        return SPECIALIST_GUIDANCE["general"]

    route_family = route_context.get("route_family") or "general"
    specialist_profile = route_context.get("specialist_profile") or "General Support Specialist"
    preferred_queue_hint = route_context.get("preferred_queue_hint")
    confidence_hint = route_context.get("confidence_hint")
    route_reason = route_context.get("route_reason")
    matched_keywords = route_context.get("matched_keywords") or []

    specialist_text = SPECIALIST_GUIDANCE.get(
        route_family,
        SPECIALIST_GUIDANCE["general"],
    )

    preferred_queue_instruction = ""
    if preferred_queue_hint:
        preferred_queue_instruction = (
            f'- Deterministic router preferred queue: "{preferred_queue_hint}". '
            "Use this exact queue if the ticket evidence supports it."
        )
    else:
        preferred_queue_instruction = (
            "- Deterministic router did not find an exact preferred queue. "
            "Choose the best exact queue from the allowed queue list."
        )

    return f"""
Deterministic router context:
- Specialist profile: {specialist_profile}
- Route family: {route_family}
- Router confidence hint: {confidence_hint}
- Router reason: {route_reason}
- Matched keywords: {matched_keywords}
{preferred_queue_instruction}

{specialist_text}

Important:
- The deterministic router is a strong hint, not a blind override.
- If the ticket evidence clearly conflicts with the router hint, choose the best allowed label from the catalog.
- Do not invent queue, priority, type, language, intent, or business type labels.
""".strip()


def build_system_prompt(catalog: dict, route_context: dict | None = None) -> str:
    queues = catalog.get("queues", [])
    priorities = catalog.get("priorities", [])
    types = catalog.get("types", [])
    languages = catalog.get("languages", [])
    intents = catalog.get("intents", [])
    business_types = catalog.get("business_types", [])

    queue_guidance = _build_queue_guidance(queues)
    specialist_guidance = _build_specialist_guidance(route_context)

    return f"""
You are an AI support ticket triage engine.

Return ONLY valid JSON.
Do not include markdown.
Do not wrap the output in ```json.
Do not include explanations outside JSON.
Output must start with {{ and end with }}.

You must choose values ONLY from these allowed labels:

queues: {queues}
priorities: {priorities}
types: {types}
languages: {languages}
intents: {intents}
business_types: {business_types}

Important routing rules:
- predicted_queue must be one exact value from the allowed queues list
- predicted_priority must be one exact value from the allowed priorities list
- predicted_type must be one exact value from the allowed types list
- detected_language must be one exact value from the allowed languages list when possible
- likely_intent should match one exact allowed intent when possible
- predicted_business_type should match one exact allowed business type when possible

Important queue alias handling:
- If the ticket sounds like Billing Support, Payment Support, Refund Support, or Invoice Support, prefer "Billing" or the closest billing/payment queue when that label exists
- If the ticket sounds like Technical Support, API Support, Integration Support, or IT Helpdesk, prefer "IT Support" or the closest technical queue when that label exists
- If the ticket sounds like login/access/account recovery help, prefer "Account Support" or the closest account/access queue when that label exists
- If the ticket sounds like delivery/order/return/shipping help, prefer "Order Support" or the closest order/shipping queue when that label exists

Queue guidance:
{queue_guidance}

Specialist guidance:
{specialist_guidance}

Keep the output concise:
- summary: max 25 words
- urgency_reason: max 20 words
- recommended_action: max 20 words
- draft_response: max 24 words, at most 2 short sentences
- issue_keywords: max 3 short items
- if include_draft_response is false, return draft_response as ""

JSON schema:
{{
  "summary": "short operational summary",
  "detected_language": "allowed language",
  "predicted_type": "allowed type",
  "predicted_queue": "allowed queue",
  "predicted_priority": "allowed priority",
  "predicted_business_type": "allowed business type or null",
  "likely_intent": "allowed intent or null",
  "urgency_reason": "brief reason",
  "sla_risk": true,
  "needs_human_review": true,
  "recommended_action": "action recommendation",
  "draft_response": "very short customer-facing response or empty string",
  "structured_fields": {{
    "customer_name": null,
    "order_id": null,
    "account_id": null,
    "product_name": null,
    "issue_keywords": []
  }},
  "confidence": 0.0
}}
""".strip()


def build_user_prompt(payload: TicketTriageRequest) -> str:
    return f"""
subject: {payload.subject}
body: {payload.body}
language_hint: {payload.language_hint}
business_type_hint: {payload.business_type_hint}
include_draft_response: {payload.include_draft_response}
""".strip()