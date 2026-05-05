from __future__ import annotations

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class LoanApplicationState(TypedDict, total=False):
    """Full state for the loan application LangGraph."""
    messages: Annotated[list, add_messages]
    user_id: str
    application_id: str
    reference_number: str
    applicant_name: str
    pan_number: str
    dob: str
    mobile: str
    email: str
    employment_type: str
    monthly_income: float
    employer: str
    city: str
    state: str
    loan_amount: float
    loan_type: str
    tenure_months: int
    documents_uploaded: dict
    documents_required: list[str]
    documents_pending: list[str]
    pan_verified: bool
    aadhaar_verified: bool
    face_match_score: float
    bureau_reports: dict
    income_verified: dict
    employer_verified: bool
    four_c_scores: dict
    dti_ratio: float
    stability_score: float
    fraud_flags: list[str]
    composite_score: int
    risk_category: str
    compliance_status: str
    pricing: dict
    decision: str
    decision_rationale: str
    confidence: float
    offer: dict
    current_phase: str
    needs_human_review: bool
    officer_decision: str
    conversation_complete: bool
