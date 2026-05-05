from __future__ import annotations

import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field
from src.db.models import (
    ApplicationStatus, DocumentType, DecisionEnum, RiskCategory, LoanType,
    EmploymentType, OcrStatus,
)


# -- Application Schemas ----------------------------------------------------

class ApplicantInfoCreate(BaseModel):
    name: str = Field(..., max_length=255)
    pan_number: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    dob: date | None = None
    mobile: str | None = Field(None, max_length=15)
    email: str | None = Field(None, max_length=255)
    income: float | None = None
    employer: str | None = None
    employment_type: EmploymentType | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None


class LoanDetails(BaseModel):
    amount: float = Field(..., gt=0)
    loan_type: LoanType
    tenure_months: int | None = None


class ApplicationCreate(BaseModel):
    applicant_info: ApplicantInfoCreate
    loan_details: LoanDetails


class ApplicationResponse(BaseModel):
    application_id: uuid.UUID
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationStatusResponse(BaseModel):
    application_id: uuid.UUID
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
    current_stage: str | None = None

    model_config = {"from_attributes": True}


class DecisionResponse(BaseModel):
    application_id: uuid.UUID
    decision: DecisionEnum
    credit_score: int | None = None
    risk_category: RiskCategory | None = None
    reasons: list[str] = []
    confidence: float

    model_config = {"from_attributes": True}


class AgentStageInfo(BaseModel):
    agent: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    output_summary: dict | None = None


class TimelineResponse(BaseModel):
    application_id: uuid.UUID
    stages: list[AgentStageInfo]


# -- Document Schemas --------------------------------------------------------

class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    status: str = "uploaded"
    ocr_status: OcrStatus

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    document_id: uuid.UUID
    type: DocumentType
    ocr_status: OcrStatus
    extracted_data: dict | None = None

    model_config = {"from_attributes": True}


# -- HITL Schemas ------------------------------------------------------------

class HITLItem(BaseModel):
    application_id: uuid.UUID
    applicant_name: str = ""
    reference_number: str = ""
    loan_amount: float = 0
    composite_score: int | None = None
    risk_flags: list[str] = []
    waiting_since: str | None = None
    escalation_reason: str
    priority: str
    agent_recommendation: DecisionEnum

    model_config = {"from_attributes": True}


class HITLQueueResponse(BaseModel):
    items: list[HITLItem]


class HITLDetailResponse(BaseModel):
    application_id: uuid.UUID
    full_application_data: dict
    agent_outputs: list[dict]
    recommended_decision: DecisionEnum
    risk_flags: list[str]


class HITLReviewCreate(BaseModel):
    decision: DecisionEnum
    officer_notes: str | None = None
    override_reason: str | None = None


class HITLReviewResponse(BaseModel):
    status: str = "reviewed"
    final_decision: DecisionEnum


# -- Evolution Schemas -------------------------------------------------------

class EvolutionChange(BaseModel):
    version: int
    agent: str
    change_type: str
    before: str | None = None
    after: str | None = None
    metric_impact: dict | None = None


class EvolutionHistoryResponse(BaseModel):
    changes: list[EvolutionChange]


class EvolutionTrigger(BaseModel):
    scope: str
    algorithm: str = "textgrad"


class EvolutionTriggerResponse(BaseModel):
    evolution_id: uuid.UUID
    status: str = "running"


# -- Report Schemas ----------------------------------------------------------

class KPIReport(BaseModel):
    default_rate: float
    approval_rate: float
    avg_processing_time_seconds: float
    thin_file_approval_rate: float
    bias_metrics: dict


class AgentPerformance(BaseModel):
    name: str
    avg_latency_ms: float
    success_rate: float
    evolution_count: int
    last_evolved: datetime | None = None


class AgentReport(BaseModel):
    agents: list[AgentPerformance]


# -- Webhook Schemas ---------------------------------------------------------

class WebhookCreate(BaseModel):
    url: str
    events: list[str]


class WebhookResponse(BaseModel):
    webhook_id: uuid.UUID
    status: str = "active"

    model_config = {"from_attributes": True}


# -- Health Check ------------------------------------------------------------

class ComponentHealth(BaseModel):
    status: str
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    status: str
    components: dict[str, ComponentHealth]
