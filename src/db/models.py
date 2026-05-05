from __future__ import annotations

import uuid
import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String, Integer, Float, Text, Boolean, DateTime, Date, Enum, ForeignKey, ARRAY,
    Numeric, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# -- Enums -------------------------------------------------------------------

class ApplicationStatus(str, enum.Enum):
    LEAD = "lead"
    DOCS_PENDING = "docs_pending"
    PROCESSING = "processing"
    DECIDED = "decided"
    DISBURSED = "disbursed"
    CANCELLED = "cancelled"


class DocumentType(str, enum.Enum):
    BANK_STATEMENT = "bank_statement"
    PAYSLIP = "payslip"
    PAN_CARD = "pan_card"
    AADHAAR = "aadhaar"
    VOTER_ID = "voter_id"
    PASSPORT = "passport"
    ITR = "itr"
    FORM_16 = "form_16"
    GST_CERTIFICATE = "gst_certificate"
    ADDRESS_PROOF = "address_proof"
    SELFIE = "selfie"
    OTHER = "other"


class OcrStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BureauProvider(str, enum.Enum):
    CIBIL = "cibil"
    EXPERIAN = "experian"
    CRIF = "crif"
    EQUIFAX = "equifax"


class DecisionEnum(str, enum.Enum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    DENIED = "denied"
    ESCALATED = "escalated"


class RiskCategory(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class LoanType(str, enum.Enum):
    PERSONAL = "personal"
    HOME = "home"
    AUTO = "auto"
    BUSINESS = "business"
    EDUCATION = "education"


class EmploymentType(str, enum.Enum):
    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"


class FraudCheckType(str, enum.Enum):
    IDENTITY = "identity"
    DOCUMENT = "document"
    PATTERN = "pattern"


class VerifierType(str, enum.Enum):
    SALARIED = "salaried"
    SELF_EMPLOYED = "self_employed"


class NotificationChannel(str, enum.Enum):
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class NotificationStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class NegativeListType(str, enum.Enum):
    EMPLOYER = "employer"
    INDIVIDUAL = "individual"
    PINCODE = "pincode"


class RuleType(str, enum.Enum):
    ELIGIBILITY = "eligibility"
    POLICY = "policy"
    LIMIT = "limit"


class RegulatoryReportType(str, enum.Enum):
    CERSAI_CHARGE = "cersai_charge"
    BUREAU_REPORTING = "bureau_reporting"


class DisbursementStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    OFFICER = "officer"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


# -- Models ------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applications: Mapped[list["Application"]] = relationship(back_populates="user")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_name: Mapped[str] = mapped_column(String(255))
    pan_number: Mapped[str] = mapped_column(String(10), index=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    loan_amount: Mapped[float] = mapped_column(Numeric(15, 2))
    loan_type: Mapped[LoanType] = mapped_column(Enum(LoanType))
    tenure_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    employment_type: Mapped[Optional[EmploymentType]] = mapped_column(Enum(EmploymentType), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.LEAD
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    phase_history: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    profile: Mapped[Optional["ApplicantProfile"]] = relationship(back_populates="application", uselist=False)
    documents: Mapped[list["Document"]] = relationship(back_populates="application")
    bureau_reports: Mapped[list["BureauReport"]] = relationship(back_populates="application")
    agent_outputs: Mapped[list["AgentOutput"]] = relationship(back_populates="application")
    decision: Mapped[Optional["CreditDecision"]] = relationship(back_populates="application", uselist=False)
    hitl_review: Mapped[Optional["HITLReview"]] = relationship(back_populates="application", uselist=False)
    income_verifications: Mapped[list["IncomeVerification"]] = relationship(back_populates="application")
    fraud_checks: Mapped[list["FraudCheck"]] = relationship(back_populates="application")
    credit_score: Mapped[Optional["CreditScore"]] = relationship(back_populates="application", uselist=False)
    offer: Mapped[Optional["Offer"]] = relationship(back_populates="application", uselist=False)
    disbursement: Mapped[Optional["Disbursement"]] = relationship(back_populates="application", uselist=False)
    notifications: Mapped[list["Notification"]] = relationship(back_populates="application")
    user: Mapped[Optional["User"]] = relationship(back_populates="applications")


class ApplicantProfile(Base):
    __tablename__ = "applicant_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), unique=True
    )
    income: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    employer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[Optional[EmploymentType]] = mapped_column(Enum(EmploymentType), nullable=True)
    tenure_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="profile")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True
    )
    type: Mapped[DocumentType] = mapped_column(Enum(DocumentType))
    file_path: Mapped[str] = mapped_column(String(500))
    classification_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_status: Mapped[OcrStatus] = mapped_column(Enum(OcrStatus), default=OcrStatus.PENDING)
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tampering_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="documents")


class BureauReport(Base):
    __tablename__ = "bureau_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id")
    )
    bureau: Mapped[BureauProvider] = mapped_column(Enum(BureauProvider))
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raw_report: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="bureau_reports")


class IncomeVerification(Base):
    __tablename__ = "income_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id")
    )
    verifier_type: Mapped[VerifierType] = mapped_column(Enum(VerifierType))
    verified_monthly_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discrepancy_flags: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="income_verifications")


class FraudCheck(Base):
    __tablename__ = "fraud_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id")
    )
    check_type: Mapped[FraudCheckType] = mapped_column(Enum(FraudCheckType))
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fraud_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="fraud_checks")


class CreditScore(Base):
    __tablename__ = "credit_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), unique=True
    )
    four_c_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    stability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dti_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    debt_burden: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    composite_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_category: Mapped[Optional[RiskCategory]] = mapped_column(Enum(RiskCategory), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="credit_score")


class CreditDecision(Base):
    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), unique=True
    )
    decision: Mapped[DecisionEnum] = mapped_column(Enum(DecisionEnum))
    interest_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    processing_fee: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    emi_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    conditions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="decision")


class HITLReview(Base):
    __tablename__ = "hitl_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), unique=True
    )
    officer_id: Mapped[str] = mapped_column(String(100))
    officer_decision: Mapped[DecisionEnum] = mapped_column(Enum(DecisionEnum))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="hitl_review")


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), unique=True
    )
    offer_pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    emi_schedule: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    validity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="offer")


class Disbursement(Base):
    __tablename__ = "disbursements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), unique=True
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2))
    beneficiary_account: Mapped[str] = mapped_column(String(50))
    utr_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[DisbursementStatus] = mapped_column(Enum(DisbursementStatus), default=DisbursementStatus.PENDING)
    loan_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    first_emi_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    disbursed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="disbursement")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    current_phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    langgraph_thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship(back_populates="conversations")
    application: Mapped[Optional["Application"]] = relationship()
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id")
    )
    agent_name: Mapped[str] = mapped_column(String(100), index=True)
    phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    input_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    llm_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    llm_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="agent_outputs")


class EvolutionHistory(Base):
    __tablename__ = "evolution_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name: Mapped[str] = mapped_column(String(100), index=True)
    algorithm: Mapped[str] = mapped_column(String(50))
    version: Mapped[int] = mapped_column(Integer)
    changes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metric_before: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metric_after: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(500))
    events: Mapped[list] = mapped_column(ARRAY(Text))
    secret_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RateCard(Base):
    __tablename__ = "rate_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_type: Mapped[LoanType] = mapped_column(Enum(LoanType))
    risk_category: Mapped[RiskCategory] = mapped_column(Enum(RiskCategory))
    min_score: Mapped[int] = mapped_column(Integer)
    max_score: Mapped[int] = mapped_column(Integer)
    interest_rate: Mapped[float] = mapped_column(Float)
    processing_fee_pct: Mapped[float] = mapped_column(Float)
    insurance_pct: Mapped[float] = mapped_column(Float, default=0.0)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProductRule(Base):
    __tablename__ = "product_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_type: Mapped[LoanType] = mapped_column(Enum(LoanType))
    rule_name: Mapped[str] = mapped_column(String(100))
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType))
    rule_config: Mapped[dict] = mapped_column(JSONB)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class NegativeList(Base):
    __tablename__ = "negative_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_type: Mapped[NegativeListType] = mapped_column(Enum(NegativeListType))
    entity_name: Mapped[str] = mapped_column(String(255))
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    added_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True
    )
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel))
    template_name: Mapped[str] = mapped_column(String(100))
    recipient: Mapped[str] = mapped_column(String(255))
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.SENT)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Optional["Application"]] = relationship(back_populates="notifications")


class RegulatoryReport(Base):
    __tablename__ = "regulatory_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id")
    )
    report_type: Mapped[RegulatoryReportType] = mapped_column(Enum(RegulatoryReportType))
    status: Mapped[str] = mapped_column(String(50))
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class ApiAuditLog(Base):
    __tablename__ = "api_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint: Mapped[str] = mapped_column(String(255))
    method: Mapped[str] = mapped_column(String(10))
    request_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    response_status: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
