from typing import List, Optional

from pydantic import BaseModel, Field


class TicketTriageRequest(BaseModel):
    subject: str = Field(..., min_length=3)
    body: str = Field(..., min_length=5)
    language_hint: Optional[str] = None
    business_type_hint: Optional[str] = None
    include_draft_response: bool = True
    simulate_error: bool = False


class StructuredFields(BaseModel):
    customer_name: Optional[str] = None
    order_id: Optional[str] = None
    account_id: Optional[str] = None
    product_name: Optional[str] = None
    issue_keywords: List[str] = Field(default_factory=list)


class TicketTriageResponse(BaseModel):
    summary: str
    detected_language: str
    predicted_type: str
    predicted_queue: str
    predicted_priority: str
    predicted_business_type: Optional[str] = None
    likely_intent: Optional[str] = None
    urgency_reason: str
    sla_risk: bool
    needs_human_review: bool
    recommended_action: str
    draft_response: str
    structured_fields: StructuredFields
    confidence: float = Field(..., ge=0.0, le=1.0)

class TriageFeedbackRequest(BaseModel):
    queue_correct: bool
    corrected_queue: Optional[str] = None

    priority_correct: bool = True
    corrected_priority: Optional[str] = None

    intent_correct: bool = True
    corrected_intent: Optional[str] = None

    recommended_action_correct: bool = True
    corrected_recommended_action: Optional[str] = None

    corrected_by: Optional[str] = None
    correction_source: Optional[str] = "human_review"
    notes: Optional[str] = None