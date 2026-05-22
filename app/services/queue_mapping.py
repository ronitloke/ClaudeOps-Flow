import re
from typing import Iterable


def _norm(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower().strip())


QUEUE_ALIAS_MAP = {
    "billingsupport": "Billing",
    "billingteam": "Billing",
    "billingissue": "Billing",
    "billing": "Billing",
    "refundsupport": "Billing",
    "paymentsupport": "Billing",
    "paymentissues": "Billing",

    "technicalsupport": "IT Support",
    "techsupport": "IT Support",
    "itsupport": "IT Support",
    "technical": "IT Support",
    "ithelpdesk": "IT Support",
    "apisupport": "IT Support",
    "integrationsupport": "IT Support",

    "accountsupport": "Account Support",
    "accounthelp": "Account Support",
    "loginissues": "Account Support",
    "accesssupport": "Account Support",

    "ordersupport": "Order Support",
    "deliverysupport": "Order Support",
    "shippingsupport": "Order Support",
    "returnsupport": "Order Support",
}


QUEUE_FAMILY_KEYWORDS = {
    "billing": ["billing", "bill", "refund", "payment", "invoice", "charge", "subscription"],
    "technical": ["technical", "tech", "it", "bug", "error", "issue", "outage", "system", "integration", "api"],
    "account": ["account", "login", "password", "signin", "access", "auth", "unlock", "profile"],
    "order": ["order", "delivery", "shipping", "shipment", "tracking", "return", "fulfillment"],
    "general": ["general", "other", "support", "help", "inquiry", "query"],
}


def queue_family(label: str | None) -> str:
    normalized = _norm(label)
    if not normalized:
        return "unknown"

    if normalized in QUEUE_ALIAS_MAP:
        normalized = _norm(QUEUE_ALIAS_MAP[normalized])

    for family, keywords in QUEUE_FAMILY_KEYWORDS.items():
        if any(_norm(keyword) in normalized for keyword in keywords):
            return family

    return normalized


def canonicalize_queue_label(label: str | None, allowed_labels: Iterable[str] | None = None) -> str:
    raw = (label or "").strip()
    if not raw:
        return ""

    normalized_raw = _norm(raw)

    if normalized_raw in QUEUE_ALIAS_MAP:
        mapped_value = QUEUE_ALIAS_MAP[normalized_raw]

        if allowed_labels:
            for item in allowed_labels:
                if _norm(item) == _norm(mapped_value):
                    return item

        return mapped_value

    if allowed_labels:
        allowed_map = {_norm(item): item for item in allowed_labels if item}

        exact = allowed_map.get(normalized_raw)
        if exact:
            return exact

        raw_family = queue_family(raw)
        for item in allowed_labels:
            if queue_family(item) == raw_family:
                return item

    return raw