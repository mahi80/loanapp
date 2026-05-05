# Personal Loan Underwriting Agent System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the existing 11-agent credit scoring system into a 22-agent personal loan underwriting system covering the complete loan journey from lead walk-in to cash disbursement.

**Architecture:** The system decomposes the loan journey into 5 phases (Intake, Extraction/Verification, Risk Assessment, Decision/Offer, Fulfillment) plus 2 cross-cutting agents (Orchestrator, XAI Explainer). Each agent follows Single Responsibility Principle using EvoAgentX CustomizeAgent with LiteLLM routing to Azure OpenAI (Opus for reasoning, GPT-4o for tool-calling). All agents share a PostgreSQL database, Redis broker, Qdrant vector store, and Mem0 memory layer.

**Tech Stack:** Python 3.11+, EvoAgentX, FastAPI, SQLAlchemy async, PostgreSQL 16 + pgvector, Redis 7, Qdrant, LiteLLM, Mem0, Docker Compose (8 containers)

---

## File Structure

### Existing files to MODIFY:
- `src/config.py` -- Add new API keys, rename project references
- `src/db/models.py` -- Add 9 new tables, update 4 existing tables, new enums
- `src/main.py` -- Update title/description, add new route modules
- `src/api/models/schemas.py` -- Add schemas for offers, notifications, config, audit, disbursement
- `src/api/routes/applications.py` -- Add accept-offer, resend-offer, documents/checklist endpoints
- `src/api/routes/documents.py` -- Add checklist endpoint
- `src/agents/orchestrator.py` -- Full rewrite for 22-agent DAG
- `src/agents/bureau_pull.py` -- Add CRIF/Equifax, unified schema
- `src/agents/risk_modeler.py` -- Rewrite for 4Cs framework
- `src/agents/compliance.py` -- Add RBI/FEMA, adverse action
- `src/agents/decision.py` -- Add CONDITIONAL decision, confidence routing
- `src/agents/xai_explainer.py` -- Add adverse action notices, Hindi translation
- `src/workflows/credit_scoring_workflow.py` -- DELETE (replaced by new workflow)
- `src/tools/external/__init__.py` -- Export new clients
- `src/tools/internal/__init__.py` -- Export new tools
- `docker-compose.yml` -- Update DB name, add pgvector init
- `requirements.txt` -- Add new dependencies
- `tests/conftest.py` -- Update for new DB models

### Existing files to DELETE:
- `src/agents/data_ingestion.py` -- Replaced by doc_classifier + ocr_extractor + data_normalizer
- `src/agents/id_verification.py` -- Replaced by fraud_identity + employer_verify
- `src/agents/income_analyst.py` -- Replaced by income_salaried + income_self_employed
- `src/agents/debt_analyst.py` -- Replaced by debt_burden

### New files to CREATE:

**Agents (13 new):**
- `src/agents/lead_qualification.py` -- Agent #1: eligibility checks
- `src/agents/document_collection.py` -- Agent #2: doc checklist tracking
- `src/agents/doc_classifier.py` -- Agent #3: document type classification
- `src/agents/ocr_extractor.py` -- Agent #4: OCR extraction
- `src/agents/data_normalizer.py` -- Agent #5: data normalization
- `src/agents/income_salaried.py` -- Agent #7: salaried income verification
- `src/agents/income_self_employed.py` -- Agent #8: self-employed income verification
- `src/agents/employer_verify.py` -- Agent #9: employer verification
- `src/agents/account_aggregator.py` -- Agent #10: RBI Account Aggregator
- `src/agents/income_stability.py` -- Agent #12: income stability scoring
- `src/agents/score_aggregator.py` -- Agent #14: composite score aggregation
- `src/agents/fraud_identity.py` -- Agent #15: synthetic identity detection
- `src/agents/fraud_document.py` -- Agent #16: document tampering detection
- `src/agents/pricing.py` -- Agent #18: interest rate/fee calculation
- `src/agents/offer_generator.py` -- Agent #20: loan offer PDF generation
- `src/agents/disbursement.py` -- Agent #21: fund transfer + loan activation
- `src/agents/debt_burden.py` -- Agent #13: DTI + hidden debt (replaces debt_analyst)

**Workflow:**
- `src/workflows/loan_underwriting_workflow.py` -- 22-agent DAG

**Internal Tools (17 new):**
- `src/tools/internal/eligibility_rules.py` -- Age/income/geography checks
- `src/tools/internal/negative_list.py` -- Employer/individual/pincode blacklists
- `src/tools/internal/checklist_manager.py` -- Document checklist tracking
- `src/tools/internal/classification_model.py` -- Document type classifier
- `src/tools/internal/normalization_rules.py` -- Data standardization
- `src/tools/internal/cross_validator.py` -- Cross-document consistency checks
- `src/tools/internal/salary_credit_matcher.py` -- Bank credit vs payslip matching
- `src/tools/internal/income_trend_analyzer.py` -- Income trajectory analysis
- `src/tools/internal/cashflow_calculator.py` -- Business cashflow from bank statements
- `src/tools/internal/four_c_scorer.py` -- Character/Capacity/Capital/Collateral scoring
- `src/tools/internal/volatility_calculator.py` -- Income coefficient of variation
- `src/tools/internal/hidden_debt_scanner.py` -- Non-bureau debt detection
- `src/tools/internal/weighted_aggregator.py` -- Configurable score aggregation
- `src/tools/internal/rate_card_engine.py` -- Interest rate lookup
- `src/tools/internal/emi_scheduler.py` -- EMI schedule generation
- `src/tools/internal/bias_detector.py` -- 4/5ths rule bias check
- `src/tools/internal/pdf_generator.py` -- Loan offer PDF creation

**External API Clients (18 new):**
- `src/tools/external/crif_client.py` -- CRIF HighMark bureau
- `src/tools/external/equifax_client.py` -- Equifax bureau
- `src/tools/external/face_match.py` -- Azure Face API
- `src/tools/external/company_registry.py` -- MCA company lookup
- `src/tools/external/sanctions_checker.py` -- PEP/sanctions screening
- `src/tools/external/gst_verifier.py` -- GST filing verification
- `src/tools/external/itr_verifier.py` -- ITR filing verification
- `src/tools/external/setu_aa_client.py` -- Setu Account Aggregator
- `src/tools/external/digilocker.py` -- DigiLocker document pull
- `src/tools/external/esign_client.py` -- Leegality e-sign
- `src/tools/external/emandate_client.py` -- NPCI e-NACH mandate
- `src/tools/external/neft_client.py` -- NEFT/IMPS transfer
- `src/tools/external/penny_drop.py` -- Bank account verification
- `src/tools/external/cbs_connector.py` -- Core banking integration
- `src/tools/external/sms_gateway.py` -- MSG91/Twilio SMS
- `src/tools/external/email_client.py` -- SendGrid email
- `src/tools/external/whatsapp_client.py` -- WhatsApp Business API
- `src/tools/external/ckyc_registry.py` -- Central KYC Registry

**API Routes (4 new):**
- `src/api/routes/offers.py` -- Offer acceptance, resend
- `src/api/routes/notifications.py` -- Notification dispatch
- `src/api/routes/config.py` -- Rate cards, product rules
- `src/api/routes/audit.py` -- Decision audit trail

**Test Files (20 new):**
- `tests/test_agents/test_lead_qualification.py`
- `tests/test_agents/test_document_collection.py`
- `tests/test_agents/test_doc_classifier.py`
- `tests/test_agents/test_ocr_extractor.py`
- `tests/test_agents/test_data_normalizer.py`
- `tests/test_agents/test_income_verifiers.py`
- `tests/test_agents/test_employer_verify.py`
- `tests/test_agents/test_fraud_agents.py`
- `tests/test_agents/test_scoring_agents.py`
- `tests/test_agents/test_decision_pipeline.py`
- `tests/test_agents/test_disbursement.py`
- `tests/test_tools/test_eligibility_rules.py`
- `tests/test_tools/test_internal_tools.py`
- `tests/test_tools/test_external_clients.py` (update existing)
- `tests/test_api/test_offers.py`
- `tests/test_api/test_config.py`
- `tests/test_api/test_audit.py`
- `tests/test_api/test_notifications.py`
- `tests/test_workflow/test_loan_underwriting.py`
- `tests/fixtures/*.json` (new mock responses)

---

## Task 1: Foundation -- Config, Dependencies, and Database Schema

**Files:**
- Modify: `src/config.py`
- Modify: `src/db/models.py`
- Modify: `requirements.txt`
- Modify: `docker-compose.yml`
- Modify: `tests/conftest.py`
- Create: `tests/test_db/test_models.py`

- [ ] **Step 1: Update requirements.txt with new dependencies**

```python
# Add to requirements.txt after existing entries:

# PDF Generation
reportlab>=4.1.0
weasyprint>=62.0

# Document forensics
pikepdf>=8.0.0
Pillow>=10.4.0

# AA/KYC
python-jose>=3.3.0

# Testing
aiosqlite>=0.20.0
```

- [ ] **Step 2: Update config.py with all new API keys and settings**

Replace the entire `Settings` class body in `src/config.py`:

```python
class Settings(BaseSettings):
    # Environment
    environment: str = "development"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://loan:loan@postgres:5432/loan_underwriting"

    # Redis
    redis_url: str = "redis://redis:6379"

    # Qdrant
    qdrant_url: str = "http://qdrant:6333"

    # LiteLLM
    litellm_base_url: str = "http://litellm:4000"

    # Azure AI (Opus - Sweden Central)
    azure_ai_api_key: str = ""
    azure_ai_api_base: str = ""
    azure_ai_chat_deployment: str = "claude-opus-4-6"
    azure_ai_api_version: str = "2024-12-01-preview"

    # Azure OpenAI (GPT-4o fallback - East US 2)
    azure_api_key: str = ""
    azure_api_base: str = ""
    azure_api_version: str = "2024-12-01-preview"
    azure_chat_deployment: str = "gpt-4o"
    azure_embed_deployment: str = "text-embedding-3-large"
    azure_embed_api_version: str = "2024-02-01"

    # Document Store
    document_store_endpoint: str = "http://minio:9000"
    document_store_type: str = "s3"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"

    # Mem0
    mem0_api_key: str = ""
    mem0_project_name: str = "loan_underwriting"
    mem0_vector_store: str = "qdrant"
    mem0_collection_name: str = "loan_memory"

    # Azure Document Intelligence (OCR)
    azure_form_recognizer_endpoint: str = ""
    azure_form_recognizer_key: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-me-in-production"
    api_rate_limit: str = "100/minute"

    # Credit Bureau APIs
    cibil_api_key: str = ""
    experian_api_key: str = ""
    crif_api_key: str = ""
    equifax_api_key: str = ""

    # KYC APIs
    pan_verify_api_key: str = ""
    aadhaar_api_key: str = ""
    ckyc_api_key: str = ""
    face_match_api_key: str = ""
    sanctions_api_key: str = ""

    # Financial APIs
    perfios_api_key: str = ""
    setu_aa_api_key: str = ""
    gst_verify_api_key: str = ""
    itr_verify_api_key: str = ""

    # Employer
    company_registry_api_key: str = ""

    # Disbursement APIs
    esign_api_key: str = ""
    emandate_api_key: str = ""
    neft_api_key: str = ""
    penny_drop_api_key: str = ""
    cbs_api_key: str = ""

    # Notification APIs
    sms_api_key: str = ""
    email_api_key: str = ""
    whatsapp_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "")
```

- [ ] **Step 3: Update docker-compose.yml postgres config**

Change the postgres service environment from:
```yaml
POSTGRES_USER: ${POSTGRES_USER:-credit}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-credit}
POSTGRES_DB: ${POSTGRES_DB:-credit_scoring}
```
to:
```yaml
POSTGRES_USER: ${POSTGRES_USER:-loan}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-loan}
POSTGRES_DB: ${POSTGRES_DB:-loan_underwriting}
```

And update the healthcheck:
```yaml
test: ["CMD-SHELL", "pg_isready -U loan"]
```

- [ ] **Step 4: Rewrite src/db/models.py with all 19 tables**

Replace the entire file with the expanded schema. Key changes:
- `ApplicationStatus` enum: add `LEAD`, `DOCS_PENDING`, `PROCESSING`, `DECIDED`, `DISBURSED` statuses
- `Decision` enum: add `CONDITIONAL` value
- `Application` model: add `mobile`, `tenure_months`, `employment_type` columns
- `ApplicantProfile`: add `designation`, `tenure_months`, `age`, `city`, `state` columns
- `Document`: add `classification_confidence`, `tampering_score` columns
- `AgentOutput`: add `phase`, `input_hash`, `llm_tokens_used`, `llm_cost` columns
- `CreditDecision`: add `interest_rate`, `processing_fee`, `emi_amount`, `conditions`, `rationale` columns
- `EvolutionHistory`: replace `prompt_before`/`prompt_after`/`workflow_diff` with `changes` JSONB, add `approved_by`
- Add 9 new tables: `IncomeVerification`, `FraudCheck`, `CreditScore`, `Offer`, `Disbursement`, `RateCard`, `ProductRule`, `NegativeList`, `Notification`, `RegulatoryReport`

```python
from __future__ import annotations

import uuid
import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String, Integer, Float, Text, Boolean, DateTime, Date, Enum, ForeignKey, ARRAY,
    func, Numeric,
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


# -- Models ------------------------------------------------------------------

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_name: Mapped[str] = mapped_column(String(255))
    pan_number: Mapped[str] = mapped_column(String(10), index=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    loan_amount: Mapped[float] = mapped_column(Float)
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


class ApplicantProfile(Base):
    __tablename__ = "applicant_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), unique=True
    )
    income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id")
    )
    type: Mapped[DocumentType] = mapped_column(Enum(DocumentType))
    file_path: Mapped[str] = mapped_column(String(500))
    classification_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_status: Mapped[OcrStatus] = mapped_column(Enum(OcrStatus), default=OcrStatus.PENDING)
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tampering_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    interest_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    processing_fee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    emi_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    total_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
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
    amount: Mapped[float] = mapped_column(Float)
    beneficiary_account: Mapped[str] = mapped_column(String(50))
    utr_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[DisbursementStatus] = mapped_column(Enum(DisbursementStatus), default=DisbursementStatus.PENDING)
    loan_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    first_emi_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    disbursed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="disbursement")


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
```

- [ ] **Step 5: Update tests/conftest.py for new DB**

Change `DATABASE_URL` env var:
```python
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
```
stays the same, but add SQLAlchemy table creation fixture:

```python
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before tests, drop after."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from src.db.models import Base
    engine = create_async_engine("sqlite+aiosqlite:///test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

- [ ] **Step 6: Write model import test**

Create `tests/test_db/__init__.py` (empty) and `tests/test_db/test_models.py`:

```python
from src.db.models import (
    Application, ApplicantProfile, Document, BureauReport,
    IncomeVerification, FraudCheck, CreditScore, CreditDecision,
    HITLReview, Offer, Disbursement, AgentOutput, EvolutionHistory,
    Webhook, RateCard, ProductRule, NegativeList, Notification,
    RegulatoryReport, ApiAuditLog,
    ApplicationStatus, DecisionEnum, RiskCategory, EmploymentType,
)


def test_all_19_tables_defined():
    """Verify all 19 spec tables plus ApiAuditLog exist."""
    tables = [
        Application, ApplicantProfile, Document, BureauReport,
        IncomeVerification, FraudCheck, CreditScore, CreditDecision,
        HITLReview, Offer, Disbursement, AgentOutput, EvolutionHistory,
        Webhook, RateCard, ProductRule, NegativeList, Notification,
        RegulatoryReport, ApiAuditLog,
    ]
    assert len(tables) == 20  # 19 spec + ApiAuditLog


def test_application_status_enum():
    assert ApplicationStatus.LEAD.value == "lead"
    assert ApplicationStatus.DISBURSED.value == "disbursed"


def test_decision_enum_has_conditional():
    assert DecisionEnum.CONDITIONAL.value == "conditional"


def test_employment_type_enum():
    assert EmploymentType.SALARIED.value == "salaried"
    assert EmploymentType.SELF_EMPLOYED.value == "self_employed"
```

- [ ] **Step 7: Run tests to verify models**

Run: `cd /Users/hemantrawat/Documents/ACP_framework/sub-agents/Loan_origination_Agent && python -m pytest tests/test_db/test_models.py -v`
Expected: 4 tests PASS

- [ ] **Step 8: Commit**

```bash
git add src/config.py src/db/models.py requirements.txt docker-compose.yml tests/conftest.py tests/test_db/
git commit -m "feat: expand DB schema to 19 tables for 22-agent loan underwriting system"
```

---

## Task 2: Internal Tools -- Eligibility, Scoring, and Financial Calculators

**Files:**
- Create: `src/tools/internal/eligibility_rules.py`
- Create: `src/tools/internal/negative_list.py`
- Create: `src/tools/internal/four_c_scorer.py`
- Create: `src/tools/internal/volatility_calculator.py`
- Create: `src/tools/internal/hidden_debt_scanner.py`
- Create: `src/tools/internal/weighted_aggregator.py`
- Create: `src/tools/internal/rate_card_engine.py`
- Create: `src/tools/internal/emi_scheduler.py`
- Create: `src/tools/internal/bias_detector.py`
- Modify: `src/tools/internal/dti_calculator.py`
- Modify: `src/tools/internal/risk_scorer.py`
- Create: `tests/test_tools/__init__.py`
- Create: `tests/test_tools/test_eligibility_rules.py`
- Create: `tests/test_tools/test_internal_tools.py`

- [ ] **Step 1: Write failing tests for eligibility rules**

Create `tests/test_tools/__init__.py` (empty) and `tests/test_tools/test_eligibility_rules.py`:

```python
from src.tools.internal.eligibility_rules import check_eligibility


def test_eligible_applicant():
    result = check_eligibility(age=30, monthly_income=50000, city="Mumbai", loan_amount=500000)
    assert result["eligible"] is True
    assert result["rejection_reason"] is None


def test_reject_underage():
    result = check_eligibility(age=20, monthly_income=50000, city="Mumbai", loan_amount=500000)
    assert result["eligible"] is False
    assert "age" in result["rejection_reason"].lower()


def test_reject_overage():
    result = check_eligibility(age=59, monthly_income=50000, city="Mumbai", loan_amount=500000)
    assert result["eligible"] is False


def test_reject_low_income():
    result = check_eligibility(age=30, monthly_income=10000, city="Mumbai", loan_amount=500000)
    assert result["eligible"] is False
    assert "income" in result["rejection_reason"].lower()


def test_reject_excessive_loan():
    result = check_eligibility(age=30, monthly_income=30000, city="Mumbai", loan_amount=50000000)
    assert result["eligible"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_tools/test_eligibility_rules.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement eligibility rules**

Create `src/tools/internal/eligibility_rules.py`:

```python
from __future__ import annotations

import structlog

logger = structlog.get_logger()

MIN_AGE = 21
MAX_AGE = 58
MIN_MONTHLY_INCOME = 15000
MAX_LOAN_TO_INCOME_RATIO = 60  # max loan = 60x monthly income


def check_eligibility(
    age: int,
    monthly_income: float,
    city: str,
    loan_amount: float,
) -> dict:
    """Check basic eligibility: age, income, geography, loan-to-income ratio."""
    if age < MIN_AGE:
        return _reject(f"Age {age} below minimum {MIN_AGE}")
    if age > MAX_AGE:
        return _reject(f"Age {age} above maximum {MAX_AGE}")
    if monthly_income < MIN_MONTHLY_INCOME:
        return _reject(f"Monthly income {monthly_income} below minimum {MIN_MONTHLY_INCOME}")
    if loan_amount > monthly_income * MAX_LOAN_TO_INCOME_RATIO:
        return _reject(f"Loan amount {loan_amount} exceeds {MAX_LOAN_TO_INCOME_RATIO}x monthly income")

    logger.info("eligibility_check_passed", age=age, income=monthly_income, city=city)
    return {"eligible": True, "rejection_reason": None}


def _reject(reason: str) -> dict:
    logger.info("eligibility_check_failed", reason=reason)
    return {"eligible": False, "rejection_reason": reason}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_tools/test_eligibility_rules.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Write failing tests for internal tools**

Create `tests/test_tools/test_internal_tools.py`:

```python
from src.tools.internal.four_c_scorer import score_four_cs
from src.tools.internal.volatility_calculator import calculate_volatility
from src.tools.internal.hidden_debt_scanner import scan_hidden_debts
from src.tools.internal.weighted_aggregator import aggregate_scores
from src.tools.internal.rate_card_engine import lookup_rate
from src.tools.internal.emi_scheduler import generate_emi_schedule
from src.tools.internal.bias_detector import check_bias
from src.tools.internal.negative_list import check_negative_list


def test_four_c_scorer():
    result = score_four_cs(
        bureau_score=750, repayment_history=[{"status": "on_time"}] * 12,
        monthly_income=80000, total_obligations=20000,
        assets_value=500000, savings_balance=200000,
    )
    assert "character" in result
    assert "capacity" in result
    assert "capital" in result
    assert all(0 <= result[k] <= 100 for k in ["character", "capacity", "capital", "collateral"])


def test_volatility_calculator():
    incomes = [50000, 52000, 48000, 51000, 49000, 53000]
    result = calculate_volatility(incomes)
    assert "coefficient_of_variation" in result
    assert "stability_score" in result
    assert 0 <= result["stability_score"] <= 100


def test_hidden_debt_scanner():
    bank_debits = [
        {"description": "EMI HDFC", "amount": 15000, "recurring": True},
        {"description": "GROCERY", "amount": 3000, "recurring": False},
    ]
    bureau_emis = [{"lender": "ICICI", "emi": 10000}]
    result = scan_hidden_debts(bank_debits, bureau_emis)
    assert "hidden_debts" in result
    assert isinstance(result["hidden_debts"], list)


def test_weighted_aggregator():
    scores = {"risk_modeler": 72, "income_stability": 85, "debt_burden": 65}
    weights = {"risk_modeler": 0.4, "income_stability": 0.3, "debt_burden": 0.3}
    result = aggregate_scores(scores, weights)
    assert "composite_score" in result
    assert 300 <= result["composite_score"] <= 900


def test_rate_card_lookup():
    result = lookup_rate(risk_category="low", loan_type="personal", score=780)
    assert "interest_rate" in result
    assert "processing_fee_pct" in result


def test_emi_schedule():
    schedule = generate_emi_schedule(principal=500000, annual_rate=12.0, tenure_months=36)
    assert len(schedule["payments"]) == 36
    assert "emi_amount" in schedule
    assert schedule["emi_amount"] > 0


def test_bias_detector():
    decisions = [
        {"demographic": "group_a", "approved": True},
        {"demographic": "group_a", "approved": True},
        {"demographic": "group_b", "approved": True},
        {"demographic": "group_b", "approved": False},
        {"demographic": "group_b", "approved": False},
    ]
    result = check_bias(decisions, protected_field="demographic")
    assert "disparate_impact_ratio" in result
    assert "bias_detected" in result


def test_negative_list_check():
    result = check_negative_list(
        entity_name="TestCorp",
        list_type="employer",
        negative_entries=[{"entity_name": "BadCorp", "list_type": "employer"}],
    )
    assert result["is_negative"] is False
```

- [ ] **Step 6: Run test to verify it fails**

Run: `python -m pytest tests/test_tools/test_internal_tools.py -v`
Expected: FAIL with ImportError

- [ ] **Step 7: Implement all internal tools**

Create `src/tools/internal/negative_list.py`:

```python
from __future__ import annotations

import structlog

logger = structlog.get_logger()


def check_negative_list(
    entity_name: str,
    list_type: str,
    negative_entries: list[dict],
) -> dict:
    """Check if entity appears in negative/blacklist."""
    entity_lower = entity_name.lower()
    for entry in negative_entries:
        if entry.get("list_type") == list_type and entry["entity_name"].lower() in entity_lower:
            logger.warning("negative_list_match", entity=entity_name, matched=entry["entity_name"])
            return {"is_negative": True, "matched_entry": entry}
    return {"is_negative": False, "matched_entry": None}
```

Create `src/tools/internal/four_c_scorer.py`:

```python
from __future__ import annotations

import structlog

logger = structlog.get_logger()


def score_four_cs(
    bureau_score: int | None,
    repayment_history: list[dict],
    monthly_income: float,
    total_obligations: float,
    assets_value: float = 0,
    savings_balance: float = 0,
) -> dict:
    """Evaluate the 4Cs: Character, Capacity, Capital, Collateral."""
    # Character: repayment behavior from bureau
    on_time = sum(1 for r in repayment_history if r.get("status") == "on_time")
    total = len(repayment_history) or 1
    bureau_factor = ((bureau_score - 300) / 600 * 50) if bureau_score else 25
    character = min(100, bureau_factor + (on_time / total * 50))

    # Capacity: income vs obligations
    surplus_ratio = max(0, (monthly_income - total_obligations) / monthly_income) if monthly_income > 0 else 0
    capacity = min(100, surplus_ratio * 100)

    # Capital: assets and savings
    capital_value = assets_value + savings_balance
    capital = min(100, (capital_value / max(monthly_income * 12, 1)) * 50)

    # Collateral: for personal loans, this is limited (unsecured)
    collateral = 50  # Neutral for unsecured personal loans

    logger.info("four_c_scored", character=round(character, 1), capacity=round(capacity, 1),
                capital=round(capital, 1), collateral=collateral)

    return {
        "character": round(character, 2),
        "capacity": round(capacity, 2),
        "capital": round(capital, 2),
        "collateral": round(collateral, 2),
    }
```

Create `src/tools/internal/volatility_calculator.py`:

```python
from __future__ import annotations

import statistics
import structlog

logger = structlog.get_logger()


def calculate_volatility(monthly_incomes: list[float]) -> dict:
    """Calculate income volatility using coefficient of variation."""
    if len(monthly_incomes) < 2:
        return {"coefficient_of_variation": 0, "stability_score": 50, "trend": "insufficient_data"}

    mean = statistics.mean(monthly_incomes)
    if mean == 0:
        return {"coefficient_of_variation": 1.0, "stability_score": 0, "trend": "zero_income"}

    stdev = statistics.stdev(monthly_incomes)
    cv = stdev / mean

    # Stability score: lower CV = higher stability
    stability_score = max(0, min(100, (1 - cv) * 100))

    # Trend: compare last 3 months avg to first 3 months avg
    if len(monthly_incomes) >= 6:
        first_half = statistics.mean(monthly_incomes[:3])
        second_half = statistics.mean(monthly_incomes[-3:])
        if second_half > first_half * 1.05:
            trend = "growing"
        elif second_half < first_half * 0.95:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "coefficient_of_variation": round(cv, 4),
        "stability_score": round(stability_score, 2),
        "trend": trend,
        "mean_income": round(mean, 2),
    }
```

Create `src/tools/internal/hidden_debt_scanner.py`:

```python
from __future__ import annotations

import re
import structlog

logger = structlog.get_logger()

EMI_KEYWORDS = ["emi", "loan", "repay", "instalment", "installment"]


def scan_hidden_debts(
    bank_debits: list[dict],
    bureau_emis: list[dict],
) -> dict:
    """Detect recurring debits that look like EMIs but don't appear in bureau."""
    bureau_amounts = {e.get("emi", 0) for e in bureau_emis}

    hidden = []
    for debit in bank_debits:
        if not debit.get("recurring", False):
            continue
        desc = debit.get("description", "").lower()
        amount = debit.get("amount", 0)

        is_emi_like = any(kw in desc for kw in EMI_KEYWORDS)
        not_in_bureau = amount not in bureau_amounts

        if is_emi_like and not_in_bureau and amount >= 1000:
            hidden.append({
                "description": debit["description"],
                "amount": amount,
                "confidence": "high" if is_emi_like else "medium",
            })

    total_hidden = sum(d["amount"] for d in hidden)
    logger.info("hidden_debt_scan", found=len(hidden), total=total_hidden)

    return {"hidden_debts": hidden, "total_hidden_monthly": total_hidden}
```

Create `src/tools/internal/weighted_aggregator.py`:

```python
from __future__ import annotations

import structlog

logger = structlog.get_logger()


def aggregate_scores(
    scores: dict[str, float],
    weights: dict[str, float],
    fraud_flags: dict | None = None,
) -> dict:
    """Combine multiple scores into a composite credit score (300-900 scale)."""
    weighted_sum = sum(scores.get(k, 0) * w for k, w in weights.items())
    # Normalize from 0-100 scale to 300-900 scale
    composite = int(300 + (weighted_sum / 100) * 600)
    composite = max(300, min(900, composite))

    # Apply fraud penalty
    if fraud_flags:
        fraud_penalty = sum(f.get("risk_score", 0) for f in fraud_flags.values()) / len(fraud_flags)
        composite = max(300, int(composite - fraud_penalty * 2))

    # Risk category from composite
    if composite >= 750:
        risk_category = "low"
    elif composite >= 600:
        risk_category = "medium"
    elif composite >= 450:
        risk_category = "high"
    else:
        risk_category = "very_high"

    confidence = min(1.0, len(scores) / len(weights)) if weights else 0.5

    return {
        "composite_score": composite,
        "risk_category": risk_category,
        "confidence": round(confidence, 2),
        "component_scores": scores,
    }
```

Create `src/tools/internal/rate_card_engine.py`:

```python
from __future__ import annotations

import structlog

logger = structlog.get_logger()

DEFAULT_RATE_CARDS = {
    ("personal", "low"): {"interest_rate": 10.5, "processing_fee_pct": 1.0, "insurance_pct": 0.5},
    ("personal", "medium"): {"interest_rate": 14.0, "processing_fee_pct": 1.5, "insurance_pct": 0.75},
    ("personal", "high"): {"interest_rate": 18.0, "processing_fee_pct": 2.0, "insurance_pct": 1.0},
    ("personal", "very_high"): {"interest_rate": 22.0, "processing_fee_pct": 2.5, "insurance_pct": 1.5},
}


def lookup_rate(
    risk_category: str,
    loan_type: str = "personal",
    score: int = 0,
    db_rate_cards: list[dict] | None = None,
) -> dict:
    """Look up interest rate and fees from rate card."""
    if db_rate_cards:
        for card in db_rate_cards:
            if (card["product_type"] == loan_type
                    and card["risk_category"] == risk_category
                    and card["min_score"] <= score <= card["max_score"]
                    and card.get("active", True)):
                return {
                    "interest_rate": card["interest_rate"],
                    "processing_fee_pct": card["processing_fee_pct"],
                    "insurance_pct": card.get("insurance_pct", 0),
                }

    default = DEFAULT_RATE_CARDS.get((loan_type, risk_category))
    if default:
        return dict(default)

    return {"interest_rate": 18.0, "processing_fee_pct": 2.0, "insurance_pct": 1.0}
```

Create `src/tools/internal/emi_scheduler.py`:

```python
from __future__ import annotations

from datetime import date, timedelta
import structlog

logger = structlog.get_logger()


def generate_emi_schedule(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    start_date: date | None = None,
) -> dict:
    """Generate complete EMI amortization schedule."""
    if annual_rate == 0:
        emi = principal / tenure_months
    else:
        monthly_rate = annual_rate / 12 / 100
        emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / (
            (1 + monthly_rate) ** tenure_months - 1
        )
    emi = round(emi, 2)

    payments = []
    balance = principal
    total_interest = 0
    start = start_date or date.today()

    for month in range(1, tenure_months + 1):
        interest = round(balance * (annual_rate / 12 / 100), 2) if annual_rate > 0 else 0
        principal_component = round(emi - interest, 2)
        balance = round(balance - principal_component, 2)
        total_interest += interest

        payment_date = start + timedelta(days=30 * month)
        payments.append({
            "month": month,
            "date": payment_date.isoformat(),
            "emi": emi,
            "principal": principal_component,
            "interest": interest,
            "balance": max(0, balance),
        })

    return {
        "emi_amount": emi,
        "total_interest": round(total_interest, 2),
        "total_payment": round(emi * tenure_months, 2),
        "payments": payments,
    }
```

Create `src/tools/internal/bias_detector.py`:

```python
from __future__ import annotations

import structlog
from collections import defaultdict

logger = structlog.get_logger()

DISPARATE_IMPACT_THRESHOLD = 0.80


def check_bias(
    decisions: list[dict],
    protected_field: str,
) -> dict:
    """Check for bias using the 4/5ths (80%) rule."""
    groups: dict[str, dict] = defaultdict(lambda: {"approved": 0, "total": 0})

    for d in decisions:
        group = d.get(protected_field, "unknown")
        groups[group]["total"] += 1
        if d.get("approved"):
            groups[group]["approved"] += 1

    approval_rates = {}
    for group, counts in groups.items():
        approval_rates[group] = counts["approved"] / counts["total"] if counts["total"] > 0 else 0

    if not approval_rates:
        return {"disparate_impact_ratio": 1.0, "bias_detected": False, "details": {}}

    max_rate = max(approval_rates.values())
    min_rate = min(approval_rates.values())
    ratio = min_rate / max_rate if max_rate > 0 else 1.0

    bias_detected = ratio < DISPARATE_IMPACT_THRESHOLD

    if bias_detected:
        logger.warning("bias_detected", ratio=round(ratio, 4), groups=approval_rates)

    return {
        "disparate_impact_ratio": round(ratio, 4),
        "bias_detected": bias_detected,
        "approval_rates": approval_rates,
        "threshold": DISPARATE_IMPACT_THRESHOLD,
    }
```

- [ ] **Step 8: Run all tool tests**

Run: `python -m pytest tests/test_tools/ -v`
Expected: All tests PASS

- [ ] **Step 9: Commit**

```bash
git add src/tools/internal/ tests/test_tools/
git commit -m "feat: add internal tools for eligibility, scoring, bias detection, and financial calculators"
```

---

## Task 3: External API Clients -- Bureau, KYC, Financial, Disbursement, Notification

**Files:**
- Create: 18 new files in `src/tools/external/`
- Create: `tests/fixtures/crif_response.json` (and other fixtures)
- Modify: `tests/test_agents/test_external_clients.py`

All clients follow the existing `BaseExternalClient` pattern with circuit breaker, retry, and mock mode.

- [ ] **Step 1: Write failing test for new external clients**

Add to `tests/test_agents/test_external_clients.py`:

```python
import pytest
from src.tools.external.crif_client import CRIFClient
from src.tools.external.equifax_client import EquifaxClient
from src.tools.external.face_match import FaceMatchClient
from src.tools.external.company_registry import CompanyRegistryClient
from src.tools.external.sanctions_checker import SanctionsClient
from src.tools.external.gst_verifier import GSTVerifierClient
from src.tools.external.itr_verifier import ITRVerifierClient
from src.tools.external.setu_aa_client import SetuAAClient
from src.tools.external.digilocker import DigiLockerClient
from src.tools.external.esign_client import ESignClient
from src.tools.external.emandate_client import EMandateClient
from src.tools.external.neft_client import NEFTClient
from src.tools.external.penny_drop import PennyDropClient
from src.tools.external.cbs_connector import CBSConnectorClient
from src.tools.external.sms_gateway import SMSGatewayClient
from src.tools.external.email_client import EmailClient
from src.tools.external.whatsapp_client import WhatsAppClient
from src.tools.external.ckyc_registry import CKYCRegistryClient


@pytest.mark.asyncio
async def test_crif_client_mock():
    client = CRIFClient()
    result = await client.execute(pan="ABCDE1234F", name="Test User", dob="1990-01-01")
    assert result.success is True
    assert result.provider == "crif"
    await client.close()


@pytest.mark.asyncio
async def test_equifax_client_mock():
    client = EquifaxClient()
    result = await client.execute(pan="ABCDE1234F", name="Test User", dob="1990-01-01")
    assert result.success is True
    assert result.provider == "equifax"
    await client.close()


@pytest.mark.asyncio
async def test_face_match_client_mock():
    client = FaceMatchClient()
    result = await client.execute(selfie_path="/tmp/selfie.jpg", id_photo_path="/tmp/id.jpg")
    assert result.success is True
    assert "match_confidence" in result.data
    await client.close()


@pytest.mark.asyncio
async def test_company_registry_mock():
    client = CompanyRegistryClient()
    result = await client.execute(company_name="TCS Ltd")
    assert result.success is True
    await client.close()


@pytest.mark.asyncio
async def test_sanctions_mock():
    client = SanctionsClient()
    result = await client.execute(name="Test User", dob="1990-01-01")
    assert result.success is True
    assert "pep_match" in result.data
    await client.close()


@pytest.mark.asyncio
async def test_sms_gateway_mock():
    client = SMSGatewayClient()
    result = await client.execute(mobile="+919999999999", message="Test", template_id="test")
    assert result.success is True
    await client.close()


@pytest.mark.asyncio
async def test_email_client_mock():
    client = EmailClient()
    result = await client.execute(to="test@test.com", subject="Test", body="Test body")
    assert result.success is True
    await client.close()


@pytest.mark.asyncio
async def test_penny_drop_mock():
    client = PennyDropClient()
    result = await client.execute(account_number="1234567890", ifsc="HDFC0001234")
    assert result.success is True
    assert "account_active" in result.data
    await client.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agents/test_external_clients.py -v -k "crif or equifax or face_match or company or sanctions or sms or email or penny"`
Expected: FAIL with ImportError

- [ ] **Step 3: Create all 18 external API client files**

Each follows the same pattern. Here's the template used for all -- showing CRIF as example:

Create `src/tools/external/crif_client.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CRIFClient(BaseExternalClient):
    provider_name = "crif"

    async def _call_api(self, pan: str, name: str, dob: str) -> CreditDataResponse:
        if settings.is_development:
            mock = self._load_mock("crif_response")
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.crifhighmark.com/credit-report",
            headers={"Authorization": f"Bearer {settings.crif_api_key}", "Content-Type": "application/json"},
            json={"pan": pan, "name": name, "dob": dob},
        )
        data = response.json()
        return CreditDataResponse(
            success=True, provider=self.provider_name,
            data={"score": data.get("score"), "microfinance_history": data.get("mfiHistory", []),
                  "nbfc_data": data.get("nbfcData", [])},
            raw_response=data,
        )
```

Create `src/tools/external/equifax_client.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class EquifaxClient(BaseExternalClient):
    provider_name = "equifax"

    async def _call_api(self, pan: str, name: str, dob: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"score": 720, "report": {"accounts": [], "enquiries": []}})

        response = await self._make_request(
            method="POST", url="https://api.equifax.co.in/credit-report",
            headers={"Authorization": f"Bearer {settings.equifax_api_key}"},
            json={"pan": pan, "name": name, "dob": dob},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name,
                                  data={"score": data.get("score"), "report": data}, raw_response=data)
```

Create `src/tools/external/face_match.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class FaceMatchClient(BaseExternalClient):
    provider_name = "face_match"

    async def _call_api(self, selfie_path: str, id_photo_path: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"match_confidence": 92.5, "is_match": True})

        response = await self._make_request(
            method="POST", url=f"{settings.azure_api_base}/face/v1.0/verify",
            headers={"Ocp-Apim-Subscription-Key": settings.face_match_api_key},
            json={"url1": selfie_path, "url2": id_photo_path},
        )
        data = response.json()
        confidence = data.get("confidence", 0) * 100
        return CreditDataResponse(success=True, provider=self.provider_name,
                                  data={"match_confidence": confidence, "is_match": confidence >= 70},
                                  raw_response=data)
```

Create `src/tools/external/company_registry.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CompanyRegistryClient(BaseExternalClient):
    provider_name = "company_registry"

    async def _call_api(self, company_name: str, cin: str | None = None) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"registered": True, "category": "MNC", "status": "active",
                                            "company_name": company_name})

        response = await self._make_request(
            method="GET", url="https://api.mca.gov.in/company/search",
            headers={"Authorization": f"Bearer {settings.company_registry_api_key}"},
            json={"name": company_name, "cin": cin},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/sanctions_checker.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class SanctionsClient(BaseExternalClient):
    provider_name = "sanctions"

    async def _call_api(self, name: str, dob: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"pep_match": False, "sanctions_match": False, "match_score": 0})

        response = await self._make_request(
            method="POST", url="https://api.sanctions-provider.com/screen",
            headers={"Authorization": f"Bearer {settings.sanctions_api_key}"},
            json={"name": name, "dob": dob},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name,
                                  data={"pep_match": data.get("pepMatch", False),
                                        "sanctions_match": data.get("sanctionsMatch", False),
                                        "match_score": data.get("matchScore", 0)},
                                  raw_response=data)
```

Create `src/tools/external/gst_verifier.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class GSTVerifierClient(BaseExternalClient):
    provider_name = "gst_verifier"

    async def _call_api(self, gstin: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"valid": True, "business_name": "Test Corp",
                                            "filing_status": "regular", "turnover_slab": "1-5Cr"})

        response = await self._make_request(
            method="GET", url=f"https://api.surepass.io/api/v1/gst/{gstin}",
            headers={"Authorization": f"Bearer {settings.gst_verify_api_key}"},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/itr_verifier.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class ITRVerifierClient(BaseExternalClient):
    provider_name = "itr_verifier"

    async def _call_api(self, pan: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"filed": True, "assessment_years": ["2024-25", "2023-24"],
                                            "declared_income": 1200000})

        response = await self._make_request(
            method="POST", url="https://api.surepass.io/api/v1/itr/verify",
            headers={"Authorization": f"Bearer {settings.itr_verify_api_key}"},
            json={"pan": pan},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/setu_aa_client.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class SetuAAClient(BaseExternalClient):
    provider_name = "setu_aa"

    async def _call_api(self, consent_id: str, aa_handle: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"consent_status": "ACTIVE",
                                            "accounts": [{"type": "SAVINGS", "balance": 250000}],
                                            "deposits": [], "mutual_funds": []})

        response = await self._make_request(
            method="POST", url="https://api.setu.co/aa/v2/data/fetch",
            headers={"Authorization": f"Bearer {settings.setu_aa_api_key}"},
            json={"consent_id": consent_id, "aa_handle": aa_handle},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/digilocker.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class DigiLockerClient(BaseExternalClient):
    provider_name = "digilocker"

    async def _call_api(self, aadhaar_linked_token: str, doc_type: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"document_available": True, "doc_type": doc_type,
                                            "verified": True})

        response = await self._make_request(
            method="POST", url="https://api.digilocker.gov.in/v3/pull",
            headers={"Authorization": f"Bearer {settings.aadhaar_api_key}"},
            json={"token": aadhaar_linked_token, "doctype": doc_type},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/esign_client.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class ESignClient(BaseExternalClient):
    provider_name = "esign"

    async def _call_api(self, document_id: str, signer_name: str, signer_email: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"signed": True, "certificate_id": "MOCK-CERT-001",
                                            "signed_document_url": "/mock/signed.pdf"})

        response = await self._make_request(
            method="POST", url="https://api.leegality.com/sign",
            headers={"Authorization": f"Bearer {settings.esign_api_key}"},
            json={"document_id": document_id, "signer": {"name": signer_name, "email": signer_email}},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/emandate_client.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class EMandateClient(BaseExternalClient):
    provider_name = "emandate"

    async def _call_api(self, account_number: str, ifsc: str, amount: float, frequency: str = "monthly") -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"mandate_registered": True, "umrn": "MOCK-UMRN-001",
                                            "status": "active"})

        response = await self._make_request(
            method="POST", url="https://api.npci.org.in/emandate/register",
            headers={"Authorization": f"Bearer {settings.emandate_api_key}"},
            json={"account": account_number, "ifsc": ifsc, "amount": amount, "frequency": frequency},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/neft_client.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class NEFTClient(BaseExternalClient):
    provider_name = "neft"

    async def _call_api(self, beneficiary_account: str, beneficiary_ifsc: str, amount: float, narration: str = "") -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"transfer_status": "success", "utr_number": "MOCK-UTR-001"})

        response = await self._make_request(
            method="POST", url="https://api.bank.com/neft/transfer",
            headers={"Authorization": f"Bearer {settings.neft_api_key}"},
            json={"account": beneficiary_account, "ifsc": beneficiary_ifsc,
                  "amount": amount, "narration": narration},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/penny_drop.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class PennyDropClient(BaseExternalClient):
    provider_name = "penny_drop"

    async def _call_api(self, account_number: str, ifsc: str) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"account_active": True, "name_match": True,
                                            "bank_name": "HDFC Bank", "account_holder": "Test User"})

        response = await self._make_request(
            method="POST", url="https://api.surepass.io/api/v1/bank/verify",
            headers={"Authorization": f"Bearer {settings.penny_drop_api_key}"},
            json={"account_number": account_number, "ifsc": ifsc},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name,
                                  data={"account_active": data.get("active"), "name_match": data.get("nameMatch"),
                                        "bank_name": data.get("bankName")},
                                  raw_response=data)
```

Create `src/tools/external/cbs_connector.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CBSConnectorClient(BaseExternalClient):
    provider_name = "cbs"

    async def _call_api(self, borrower_id: str, loan_amount: float, interest_rate: float, tenure_months: int) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"loan_account_number": "MOCK-LA-001",
                                            "status": "activated", "first_emi_date": "2026-06-01"})

        response = await self._make_request(
            method="POST", url="https://cbs.bank.com/api/loan/create",
            headers={"Authorization": f"Bearer {settings.cbs_api_key}"},
            json={"borrower_id": borrower_id, "amount": loan_amount,
                  "rate": interest_rate, "tenure": tenure_months},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/sms_gateway.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class SMSGatewayClient(BaseExternalClient):
    provider_name = "sms_gateway"

    async def _call_api(self, mobile: str, message: str, template_id: str = "") -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"delivered": True, "message_id": "MOCK-MSG-001"})

        response = await self._make_request(
            method="POST", url="https://api.msg91.com/api/v5/flow/",
            headers={"authkey": settings.sms_api_key},
            json={"mobiles": mobile, "message": message, "template_id": template_id},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/email_client.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class EmailClient(BaseExternalClient):
    provider_name = "email"

    async def _call_api(self, to: str, subject: str, body: str, from_email: str = "noreply@loanapp.com") -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"delivered": True, "message_id": "MOCK-EMAIL-001"})

        response = await self._make_request(
            method="POST", url="https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.email_api_key}"},
            json={"personalizations": [{"to": [{"email": to}]}],
                  "from": {"email": from_email}, "subject": subject,
                  "content": [{"type": "text/html", "value": body}]},
        )
        return CreditDataResponse(success=True, provider=self.provider_name,
                                  data={"delivered": True, "message_id": response.headers.get("X-Message-Id", "")})
```

Create `src/tools/external/whatsapp_client.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class WhatsAppClient(BaseExternalClient):
    provider_name = "whatsapp"

    async def _call_api(self, mobile: str, template_name: str, params: dict | None = None) -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"delivered": True, "message_id": "MOCK-WA-001"})

        response = await self._make_request(
            method="POST", url="https://api.gupshup.io/wa/api/v1/msg",
            headers={"apikey": settings.whatsapp_api_key},
            json={"destination": mobile, "template": {"name": template_name, "params": params or {}}},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

Create `src/tools/external/ckyc_registry.py`:

```python
from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CKYCRegistryClient(BaseExternalClient):
    provider_name = "ckyc"

    async def _call_api(self, pan: str = "", aadhaar: str = "", ckyc_id: str = "") -> CreditDataResponse:
        if settings.is_development:
            return CreditDataResponse(success=True, provider=self.provider_name,
                                      data={"kyc_exists": True, "ckyc_number": "MOCK-CKYC-001",
                                            "verified": True})

        response = await self._make_request(
            method="POST", url="https://api.cersai.org.in/ckyc/search",
            headers={"Authorization": f"Bearer {settings.ckyc_api_key}"},
            json={"pan": pan, "aadhaar": aadhaar, "ckyc_id": ckyc_id},
        )
        data = response.json()
        return CreditDataResponse(success=True, provider=self.provider_name, data=data, raw_response=data)
```

- [ ] **Step 4: Create mock fixture files**

Create `tests/fixtures/crif_response.json`:

```json
{"score": 710, "mfiHistory": [{"lender": "Grameen", "status": "active"}], "nbfcData": []}
```

- [ ] **Step 5: Run external client tests**

Run: `python -m pytest tests/test_agents/test_external_clients.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/tools/external/ tests/test_agents/test_external_clients.py tests/fixtures/
git commit -m "feat: add 18 external API clients (bureau, KYC, financial, disbursement, notification)"
```

---

## Task 4: Phase 1 and Phase 2 Agents -- Intake, Extraction, Verification

**Files:**
- Create: `src/agents/lead_qualification.py`
- Create: `src/agents/document_collection.py`
- Create: `src/agents/doc_classifier.py`
- Create: `src/agents/ocr_extractor.py`
- Create: `src/agents/data_normalizer.py`
- Modify: `src/agents/bureau_pull.py`
- Create: `src/agents/income_salaried.py`
- Create: `src/agents/income_self_employed.py`
- Create: `src/agents/employer_verify.py`
- Create: `src/agents/account_aggregator.py`
- Delete: `src/agents/data_ingestion.py`
- Delete: `src/agents/id_verification.py`
- Delete: `src/agents/income_analyst.py`
- Create: `tests/test_agents/test_lead_qualification.py`
- Create: `tests/test_agents/test_intake_extraction.py`

- [ ] **Step 1: Write failing tests for Phase 1+2 agents**

Create `tests/test_agents/test_intake_extraction.py`:

```python
"""Test that all Phase 1 and Phase 2 agent factories produce valid CustomizeAgent instances."""
from evoagentx.agents import CustomizeAgent

from src.agents.lead_qualification import create_lead_qualification_agent
from src.agents.document_collection import create_document_collection_agent
from src.agents.doc_classifier import create_doc_classifier_agent
from src.agents.ocr_extractor import create_ocr_extractor_agent
from src.agents.data_normalizer import create_data_normalizer_agent
from src.agents.bureau_pull import create_bureau_pull_agent
from src.agents.income_salaried import create_salaried_income_agent
from src.agents.income_self_employed import create_self_employed_income_agent
from src.agents.employer_verify import create_employer_verify_agent
from src.agents.account_aggregator import create_account_aggregator_agent


def test_lead_qualification_agent():
    agent = create_lead_qualification_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "LeadQualificationAgent"
    assert any(i["name"] == "applicant_info" for i in agent.inputs)


def test_document_collection_agent():
    agent = create_document_collection_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "DocumentCollectionAgent"


def test_doc_classifier_agent():
    agent = create_doc_classifier_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "DocumentClassifierAgent"


def test_ocr_extractor_agent():
    agent = create_ocr_extractor_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "OCRExtractionAgent"


def test_data_normalizer_agent():
    agent = create_data_normalizer_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "DataNormalizerAgent"


def test_bureau_pull_agent():
    agent = create_bureau_pull_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "BureauPullAgent"
    # Should now reference CRIF in addition to CIBIL/Experian
    assert "crif" in agent.prompt.lower() or "CRIF" in agent.prompt


def test_salaried_income_agent():
    agent = create_salaried_income_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "SalariedIncomeAgent"
    assert agent.llm_config.model == "opus-primary"


def test_self_employed_income_agent():
    agent = create_self_employed_income_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "SelfEmployedIncomeAgent"
    assert agent.llm_config.model == "opus-primary"


def test_employer_verify_agent():
    agent = create_employer_verify_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "EmployerVerifyAgent"


def test_account_aggregator_agent():
    agent = create_account_aggregator_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "AccountAggregatorAgent"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agents/test_intake_extraction.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create lead_qualification.py (Agent #1)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_lead_qualification_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="LeadQualificationAgent",
        description="Check basic eligibility: age 21-58, min income, geography, product fit, negative list screening.",
        prompt=(
            "You are a Lead Qualification specialist for personal loan applications.\n\n"
            "Applicant Info:\n{applicant_info}\n\n"
            "Product Rules:\n{product_rules}\n\n"
            "Negative List Results:\n{negative_list_results}\n\n"
            "Instructions:\n"
            "1. Verify age is between 21 and 58.\n"
            "2. Verify monthly income meets minimum threshold for the product.\n"
            "3. Check if applicant's city/geography is serviceable.\n"
            "4. Check negative list screening results.\n"
            "5. Determine product fit based on loan amount and income.\n\n"
            "Respond with eligibility status and rejection reason if not eligible."
        ),
        inputs=[
            {"name": "applicant_info", "type": "str", "required": True, "description": "Name, age, income, city, loan amount"},
            {"name": "product_rules", "type": "str", "required": True, "description": "Eligibility rules for the product"},
            {"name": "negative_list_results", "type": "str", "required": True, "description": "Negative list screening output"},
        ],
        outputs=[
            {"name": "eligible", "type": "str", "required": True, "description": "Eligible / Not Eligible"},
            {"name": "rejection_reason", "type": "str", "required": False, "description": "Reason if not eligible"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 4: Create document_collection.py (Agent #2)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_document_collection_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="DocumentCollectionAgent",
        description="Track required document checklist, identify missing docs, send collection reminders, validate upload completeness.",
        prompt=(
            "You are a Document Collection specialist.\n\n"
            "Application ID: {application_id}\n"
            "Product Type: {product_type}\n"
            "Employment Type: {employment_type}\n"
            "Current Documents: {current_documents}\n\n"
            "Instructions:\n"
            "1. Determine required documents based on product type and employment type.\n"
            "   - Salaried: PAN, Aadhaar, 3 months payslips, 6 months bank statements, Form 16.\n"
            "   - Self-employed: PAN, Aadhaar, 2 years ITR, GST certificate, 12 months bank statements.\n"
            "2. Check which required documents have been uploaded.\n"
            "3. List missing documents.\n"
            "4. Determine if collection is complete.\n\n"
            "Provide checklist status with complete/pending items."
        ),
        inputs=[
            {"name": "application_id", "type": "str", "required": True, "description": "Application ID"},
            {"name": "product_type", "type": "str", "required": True, "description": "Loan product type"},
            {"name": "employment_type", "type": "str", "required": True, "description": "salaried or self_employed"},
            {"name": "current_documents", "type": "str", "required": True, "description": "List of uploaded docs"},
        ],
        outputs=[
            {"name": "checklist_status", "type": "str", "required": True, "description": "complete / pending"},
            {"name": "missing_documents", "type": "str", "required": True, "description": "Missing document types"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 5: Create doc_classifier.py (Agent #3)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_doc_classifier_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="DocumentClassifierAgent",
        description="Classify uploaded documents into types: bank statement, payslip, ID proof, address proof, ITR, Form 16, etc.",
        prompt=(
            "You are a Document Classification specialist.\n\n"
            "File Metadata:\n{file_metadata}\n\n"
            "OCR Text Preview:\n{text_preview}\n\n"
            "Instructions:\n"
            "1. Analyze the document's text content and metadata.\n"
            "2. Classify into one of: bank_statement, payslip, pan_card, aadhaar, voter_id, "
            "passport, itr, form_16, gst_certificate, address_proof, selfie, other.\n"
            "3. Assign a confidence score (0-100).\n"
            "4. If confidence < 80, flag for manual review.\n\n"
            "Provide document type and confidence."
        ),
        inputs=[
            {"name": "file_metadata", "type": "str", "required": True, "description": "File name, size, type"},
            {"name": "text_preview", "type": "str", "required": True, "description": "First 500 chars of OCR text"},
        ],
        outputs=[
            {"name": "document_type", "type": "str", "required": True, "description": "Classified document type"},
            {"name": "confidence", "type": "str", "required": True, "description": "Classification confidence 0-100"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 6: Create ocr_extractor.py (Agent #4)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_ocr_extractor_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="OCRExtractionAgent",
        description="Run OCR using format-specific templates for bank statements, payslips, IDs. Extract structured key-value pairs.",
        prompt=(
            "You are an OCR Extraction specialist.\n\n"
            "Document Type: {document_type}\n"
            "Raw OCR Output:\n{raw_ocr}\n\n"
            "Instructions:\n"
            "1. Apply the extraction template for this document type.\n"
            "2. For bank statements: extract account holder, bank, period, transactions.\n"
            "3. For payslips: extract employee name, gross salary, net salary, employer.\n"
            "4. For PAN: extract name, PAN number, DOB.\n"
            "5. For Aadhaar: extract name, address, DOB.\n"
            "6. For ITR: extract assessment year, total income, tax paid.\n"
            "7. Output structured JSON with all extracted key-value pairs.\n\n"
            "Provide extracted data as structured JSON."
        ),
        inputs=[
            {"name": "document_type", "type": "str", "required": True, "description": "Classified document type"},
            {"name": "raw_ocr", "type": "str", "required": True, "description": "Raw OCR key-value pairs and tables"},
        ],
        outputs=[
            {"name": "extracted_data", "type": "str", "required": True, "description": "Structured JSON key-value pairs"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 7: Create data_normalizer.py (Agent #5)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_data_normalizer_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="DataNormalizerAgent",
        description="Normalize, validate, and cross-check extracted data. Standardize formats, flag inconsistencies.",
        prompt=(
            "You are a Data Normalization specialist.\n\n"
            "Extracted Data from Multiple Documents:\n{extracted_data}\n\n"
            "Application Form Data:\n{application_data}\n\n"
            "Instructions:\n"
            "1. Standardize all dates to YYYY-MM-DD format.\n"
            "2. Normalize currency values to float (remove commas, Rs, INR prefixes).\n"
            "3. Standardize employer names (remove Ltd/Limited/Pvt variations).\n"
            "4. Cross-check name across all documents. Flag mismatches.\n"
            "5. Cross-check income: payslip vs bank credits vs declared.\n"
            "6. Cross-check address consistency.\n"
            "7. Flag any inconsistencies found.\n\n"
            "Provide normalized data JSON and inconsistency flags."
        ),
        inputs=[
            {"name": "extracted_data", "type": "str", "required": True, "description": "OCR extracted data from all docs"},
            {"name": "application_data", "type": "str", "required": True, "description": "Applicant-provided data"},
        ],
        outputs=[
            {"name": "normalized_data", "type": "str", "required": True, "description": "Clean normalized JSON"},
            {"name": "inconsistency_flags", "type": "str", "required": True, "description": "List of inconsistencies"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 8: Update bureau_pull.py (Agent #6) -- add CRIF/Equifax**

Replace `src/agents/bureau_pull.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_bureau_pull_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="BureauPullAgent",
        description="Call credit bureau APIs (CIBIL, Experian, CRIF, Equifax), handle retries/fallbacks, normalize into unified schema.",
        prompt=(
            "You are a Credit Bureau specialist. Consolidate multi-bureau credit reports.\n\n"
            "CIBIL Report:\n{cibil_report}\n\n"
            "Experian Report:\n{experian_report}\n\n"
            "CRIF Report:\n{crif_report}\n\n"
            "Applicant Info:\n{applicant_info}\n\n"
            "Instructions:\n"
            "1. Extract credit scores from each available bureau.\n"
            "2. Consolidate active account information across bureaus.\n"
            "3. Identify repayment patterns and delinquencies.\n"
            "4. Count recent enquiries (last 6 months).\n"
            "5. Calculate total outstanding obligations.\n"
            "6. Include microfinance history from CRIF.\n"
            "7. Flag if this is a thin file (< 12 months credit history).\n\n"
            "Provide unified bureau report with all data normalized."
        ),
        inputs=[
            {"name": "cibil_report", "type": "str", "required": True, "description": "CIBIL bureau report"},
            {"name": "experian_report", "type": "str", "required": True, "description": "Experian bureau report"},
            {"name": "crif_report", "type": "str", "required": True, "description": "CRIF HighMark report"},
            {"name": "applicant_info", "type": "str", "required": True, "description": "Applicant PAN, name, DOB"},
        ],
        outputs=[
            {"name": "consolidated_profile", "type": "str", "required": True, "description": "Unified credit profile"},
            {"name": "bureau_scores", "type": "str", "required": True, "description": "Scores from each bureau"},
            {"name": "credit_flags", "type": "str", "required": True, "description": "Credit history flags"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 9: Create income_salaried.py (Agent #7)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_salaried_income_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="SalariedIncomeAgent",
        description="Verify salaried income: cross-check salary slips with bank credits, verify employer match, check salary trend, calculate average net monthly income.",
        prompt=(
            "You are a Salaried Income Verification specialist.\n\n"
            "Bank Statement Data:\n{bank_statement_data}\n\n"
            "Salary Slips:\n{salary_slips}\n\n"
            "Employer Name from Application:\n{employer_name}\n\n"
            "Instructions:\n"
            "1. Match salary slip amounts with bank credit entries.\n"
            "2. Verify the crediting entity name matches the declared employer.\n"
            "3. Analyze salary trend over 6 months (growing/stable/declining).\n"
            "4. Calculate average net monthly income from bank credits.\n"
            "5. Flag discrepancies > 10% between payslip and bank credits.\n"
            "6. Calculate income stability score (0-100).\n\n"
            "Provide verified monthly income with stability assessment."
        ),
        inputs=[
            {"name": "bank_statement_data", "type": "str", "required": True, "description": "Extracted bank transactions"},
            {"name": "salary_slips", "type": "str", "required": True, "description": "Extracted payslip data"},
            {"name": "employer_name", "type": "str", "required": True, "description": "Declared employer name"},
        ],
        outputs=[
            {"name": "verified_monthly_income", "type": "str", "required": True, "description": "Verified net income"},
            {"name": "income_stability_score", "type": "str", "required": True, "description": "Stability 0-100"},
            {"name": "discrepancy_flags", "type": "str", "required": True, "description": "Income discrepancies"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 10: Create income_self_employed.py (Agent #8)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_self_employed_income_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="SelfEmployedIncomeAgent",
        description="Verify self-employed income: analyze ITR, GST returns, bank cashflows, calculate business income using surrogate method.",
        prompt=(
            "You are a Self-Employed Income Verification specialist.\n\n"
            "Bank Statement Data:\n{bank_statement_data}\n\n"
            "ITR Data:\n{itr_data}\n\n"
            "GST Returns:\n{gst_data}\n\n"
            "Business Proof:\n{business_proof}\n\n"
            "Instructions:\n"
            "1. Analyze ITR declared income for the last 2 years.\n"
            "2. Cross-check GST turnover with bank credits.\n"
            "3. Calculate business income using bank statement surrogate method.\n"
            "4. Assess income sustainability and seasonality.\n"
            "5. Compare ITR income, GST turnover, and bank-derived income.\n"
            "6. Flag discrepancies > 20% across sources.\n\n"
            "Provide estimated monthly income with business stability assessment."
        ),
        inputs=[
            {"name": "bank_statement_data", "type": "str", "required": True, "description": "12-month bank transactions"},
            {"name": "itr_data", "type": "str", "required": True, "description": "ITR filing data"},
            {"name": "gst_data", "type": "str", "required": True, "description": "GST return data"},
            {"name": "business_proof", "type": "str", "required": True, "description": "Business registration proof"},
        ],
        outputs=[
            {"name": "estimated_monthly_income", "type": "str", "required": True, "description": "Estimated income"},
            {"name": "business_stability_score", "type": "str", "required": True, "description": "Stability 0-100"},
            {"name": "seasonality_flags", "type": "str", "required": True, "description": "Seasonal income patterns"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 11: Create employer_verify.py (Agent #9)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_employer_verify_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="EmployerVerifyAgent",
        description="Verify employer exists, check company category, validate employment tenure, check approved/negative employer lists.",
        prompt=(
            "You are an Employer Verification specialist.\n\n"
            "Employer Details:\n{employer_details}\n\n"
            "Company Registry Result:\n{registry_result}\n\n"
            "Negative List Result:\n{negative_list_result}\n\n"
            "Instructions:\n"
            "1. Verify employer exists in company registry (MCA).\n"
            "2. Determine company category: MNC / Large / SME / Startup / Govt.\n"
            "3. Validate stated employment tenure is reasonable.\n"
            "4. Check if employer is on negative list.\n"
            "5. Check if employer is on approved employer list (preferred).\n\n"
            "Provide verification status with company details."
        ),
        inputs=[
            {"name": "employer_details", "type": "str", "required": True, "description": "Employer name, designation, tenure"},
            {"name": "registry_result", "type": "str", "required": True, "description": "Company registry API result"},
            {"name": "negative_list_result", "type": "str", "required": True, "description": "Negative list check result"},
        ],
        outputs=[
            {"name": "employer_verified", "type": "str", "required": True, "description": "Y/N"},
            {"name": "company_category", "type": "str", "required": True, "description": "MNC/Large/SME/Startup/Govt"},
            {"name": "risk_flag", "type": "str", "required": True, "description": "Employer risk assessment"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 12: Create account_aggregator.py (Agent #10)**

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_account_aggregator_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="AccountAggregatorAgent",
        description="Manage RBI Account Aggregator consent flow, pull financial data via AA framework, supplement bureau data.",
        prompt=(
            "You are an Account Aggregator (AA) specialist.\n\n"
            "Consent Status:\n{consent_status}\n\n"
            "AA Financial Data:\n{aa_data}\n\n"
            "Instructions:\n"
            "1. Verify consent is active and valid.\n"
            "2. Parse multi-bank account data.\n"
            "3. Aggregate savings account balances.\n"
            "4. Identify investment holdings (mutual funds, FDs).\n"
            "5. Map recurring payment patterns.\n"
            "6. Calculate total financial assets.\n\n"
            "Provide enriched financial profile from AA data."
        ),
        inputs=[
            {"name": "consent_status", "type": "str", "required": True, "description": "Consent artifact status"},
            {"name": "aa_data", "type": "str", "required": True, "description": "Financial data from AA"},
        ],
        outputs=[
            {"name": "enriched_financial_data", "type": "str", "required": True, "description": "All bank balances, investments, payments"},
            {"name": "data_coverage", "type": "str", "required": True, "description": "How much data was available"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 13: Delete old agents**

```bash
rm src/agents/data_ingestion.py src/agents/id_verification.py src/agents/income_analyst.py
```

- [ ] **Step 14: Run tests**

Run: `python -m pytest tests/test_agents/test_intake_extraction.py -v`
Expected: All 11 tests PASS

- [ ] **Step 15: Commit**

```bash
git add src/agents/ tests/test_agents/test_intake_extraction.py
git rm src/agents/data_ingestion.py src/agents/id_verification.py src/agents/income_analyst.py
git commit -m "feat: add Phase 1-2 agents (intake, extraction, verification) - 10 agents"
```

---

## Task 5: Phase 3 Agents -- Risk Assessment and Fraud Detection

**Files:**
- Modify: `src/agents/risk_modeler.py` (rewrite for 4Cs)
- Create: `src/agents/income_stability.py`
- Create: `src/agents/debt_burden.py` (replaces debt_analyst.py)
- Create: `src/agents/score_aggregator.py`
- Create: `src/agents/fraud_identity.py`
- Create: `src/agents/fraud_document.py`
- Delete: `src/agents/debt_analyst.py`
- Create: `tests/test_agents/test_scoring_agents.py`
- Create: `tests/test_agents/test_fraud_agents.py`

- [ ] **Step 1: Write failing tests for scoring and fraud agents**

Create `tests/test_agents/test_scoring_agents.py`:

```python
from evoagentx.agents import CustomizeAgent

from src.agents.risk_modeler import create_risk_modeler_agent
from src.agents.income_stability import create_income_stability_agent
from src.agents.debt_burden import create_debt_burden_agent
from src.agents.score_aggregator import create_score_aggregator_agent


def test_risk_modeler_4cs():
    agent = create_risk_modeler_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "RiskModelerAgent"
    assert "character" in agent.prompt.lower()
    assert "capacity" in agent.prompt.lower()
    assert agent.llm_config.model == "opus-primary"


def test_income_stability_agent():
    agent = create_income_stability_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "IncomeStabilityScorerAgent"
    assert agent.llm_config.model == "opus-primary"


def test_debt_burden_agent():
    agent = create_debt_burden_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "DebtBurdenAnalyzerAgent"
    assert agent.llm_config.model == "opus-primary"


def test_score_aggregator_agent():
    agent = create_score_aggregator_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "ScoreAggregatorAgent"
    assert agent.llm_config.model == "opus-primary"
```

Create `tests/test_agents/test_fraud_agents.py`:

```python
from evoagentx.agents import CustomizeAgent

from src.agents.fraud_identity import create_identity_fraud_agent
from src.agents.fraud_document import create_doc_tampering_agent


def test_identity_fraud_agent():
    agent = create_identity_fraud_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "IdentityFraudAgent"
    assert agent.llm_config.model == "opus-primary"
    assert "synthetic" in agent.prompt.lower() or "pan" in agent.prompt.lower()


def test_doc_tampering_agent():
    agent = create_doc_tampering_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "DocTamperingAgent"
    assert agent.llm_config.model == "opus-primary"
    assert "pdf" in agent.prompt.lower() or "metadata" in agent.prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agents/test_scoring_agents.py tests/test_agents/test_fraud_agents.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Rewrite risk_modeler.py for 4Cs framework**

Replace `src/agents/risk_modeler.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_risk_modeler_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="RiskModelerAgent",
        description="Evaluate Character (repayment behavior), Capacity (income vs obligations), Capital (assets/savings), Collateral. Apply 4Cs framework with domain reasoning.",
        prompt=(
            "You are an expert Credit Risk Modeler using the 4Cs framework.\n\n"
            "Bureau Report:\n{bureau_report}\n\n"
            "Verified Income Data:\n{verified_income}\n\n"
            "Asset Data:\n{asset_data}\n\n"
            "Historical Patterns (from memory):\n{agent_memory}\n\n"
            "Instructions -- evaluate each C on a 0-100 scale:\n"
            "1. CHARACTER: Analyze repayment behavior from bureau history.\n"
            "   - On-time payment ratio, delinquency count, oldest account age.\n"
            "   - Higher score = better repayment discipline.\n"
            "2. CAPACITY: Income vs total obligations.\n"
            "   - Monthly surplus after all obligations.\n"
            "   - Employment stability factor.\n"
            "3. CAPITAL: Assets and savings as safety net.\n"
            "   - Bank balances, FDs, mutual funds, property.\n"
            "   - Months of EMI coverage from savings.\n"
            "4. COLLATERAL: For unsecured personal loans, rate at 50 (neutral).\n"
            "   - Adjust if borrower offers security.\n\n"
            "Provide 4C scores with qualitative risk narrative."
        ),
        inputs=[
            {"name": "bureau_report", "type": "str", "required": True, "description": "Consolidated bureau data"},
            {"name": "verified_income", "type": "str", "required": True, "description": "Verified income and employment data"},
            {"name": "asset_data", "type": "str", "required": True, "description": "Assets, savings, investments"},
            {"name": "agent_memory", "type": "str", "required": False, "description": "Patterns from Mem0"},
        ],
        outputs=[
            {"name": "character_score", "type": "str", "required": True, "description": "Character 0-100"},
            {"name": "capacity_score", "type": "str", "required": True, "description": "Capacity 0-100"},
            {"name": "capital_score", "type": "str", "required": True, "description": "Capital 0-100"},
            {"name": "collateral_score", "type": "str", "required": True, "description": "Collateral 0-100"},
            {"name": "risk_narrative", "type": "str", "required": True, "description": "Qualitative assessment"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 4: Create income_stability.py, debt_burden.py, score_aggregator.py, fraud_identity.py, fraud_document.py**

Create `src/agents/income_stability.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_income_stability_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="IncomeStabilityScorerAgent",
        description="Analyze income volatility: coefficient of variation over 6-12 months, salary growth trajectory, job switch frequency, industry risk.",
        prompt=(
            "You are an Income Stability scoring specialist.\n\n"
            "Income History (6-12 months):\n{income_history}\n\n"
            "Employment History:\n{employment_history}\n\n"
            "Industry:\n{industry}\n\n"
            "Instructions:\n"
            "1. Calculate coefficient of variation of monthly income.\n"
            "2. Assess salary growth trajectory (growing/stable/declining).\n"
            "3. Count job switches in last 3 years -- frequent switches = lower stability.\n"
            "4. Assess industry risk (IT stable, construction volatile, etc.).\n"
            "5. Calculate stability score 0-100.\n\n"
            "Provide stability score with volatility assessment."
        ),
        inputs=[
            {"name": "income_history", "type": "str", "required": True, "description": "6-12 months income data"},
            {"name": "employment_history", "type": "str", "required": True, "description": "Job history"},
            {"name": "industry", "type": "str", "required": True, "description": "Industry/sector"},
        ],
        outputs=[
            {"name": "stability_score", "type": "str", "required": True, "description": "Score 0-100"},
            {"name": "volatility_flag", "type": "str", "required": True, "description": "Low/Medium/High volatility"},
            {"name": "industry_risk", "type": "str", "required": True, "description": "Industry risk rating"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

Create `src/agents/debt_burden.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_debt_burden_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="DebtBurdenAnalyzerAgent",
        description="Calculate precise DTI ratio, total EMI burden, credit utilization, identify hidden obligations from bank statements.",
        prompt=(
            "You are a Debt Burden Analysis specialist.\n\n"
            "Bureau Active Loans:\n{bureau_loans}\n\n"
            "Bank Statement Debits:\n{bank_debits}\n\n"
            "Requested Loan Details:\n{loan_details}\n\n"
            "Verified Monthly Income:\n{monthly_income}\n\n"
            "Instructions:\n"
            "1. List all existing EMIs from bureau reports.\n"
            "2. Calculate credit card utilization.\n"
            "3. Scan bank debits for recurring payments not in bureau (hidden debts).\n"
            "4. Calculate proposed EMI for the requested loan.\n"
            "5. Compute DTI: (total obligations + proposed EMI) / monthly income.\n"
            "6. Calculate remaining monthly surplus.\n"
            "7. Flag if DTI > 50%.\n\n"
            "Provide DTI with full breakdown."
        ),
        inputs=[
            {"name": "bureau_loans", "type": "str", "required": True, "description": "Active loans from bureau"},
            {"name": "bank_debits", "type": "str", "required": True, "description": "Recurring bank debits"},
            {"name": "loan_details", "type": "str", "required": True, "description": "Requested loan amount, tenure, rate"},
            {"name": "monthly_income", "type": "str", "required": True, "description": "Verified monthly income"},
        ],
        outputs=[
            {"name": "dti_ratio", "type": "str", "required": True, "description": "Debt-to-income ratio"},
            {"name": "total_obligations", "type": "str", "required": True, "description": "Total monthly EMIs"},
            {"name": "hidden_debts", "type": "str", "required": True, "description": "Non-bureau debts found"},
            {"name": "surplus", "type": "str", "required": True, "description": "Remaining monthly surplus"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

Create `src/agents/score_aggregator.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_score_aggregator_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="ScoreAggregatorAgent",
        description="Combine 4C scores, income stability, debt burden, and fraud flags into composite credit score (300-900). Weights evolve via TextGrad.",
        prompt=(
            "You are the Score Aggregation specialist.\n\n"
            "4C Scores:\n{four_c_scores}\n\n"
            "Income Stability Score:\n{stability_score}\n\n"
            "DTI and Debt Burden:\n{debt_burden}\n\n"
            "Fraud Detection Results:\n{fraud_results}\n\n"
            "Current Weights:\n{aggregation_weights}\n\n"
            "Instructions:\n"
            "1. Apply weights to each component score.\n"
            "2. Normalize to 300-900 composite scale.\n"
            "3. Apply fraud penalty if any fraud flags are raised.\n"
            "4. Determine risk category: Low (750+), Medium (600-749), High (450-599), Very High (<450).\n"
            "5. Calculate confidence level based on data completeness.\n\n"
            "Provide composite score with risk category."
        ),
        inputs=[
            {"name": "four_c_scores", "type": "str", "required": True, "description": "Character/Capacity/Capital/Collateral scores"},
            {"name": "stability_score", "type": "str", "required": True, "description": "Income stability 0-100"},
            {"name": "debt_burden", "type": "str", "required": True, "description": "DTI and obligations"},
            {"name": "fraud_results", "type": "str", "required": True, "description": "Identity and document fraud flags"},
            {"name": "aggregation_weights", "type": "str", "required": True, "description": "Component weights (evolve via TextGrad)"},
        ],
        outputs=[
            {"name": "composite_score", "type": "str", "required": True, "description": "Score 300-900"},
            {"name": "risk_category", "type": "str", "required": True, "description": "Low/Medium/High/Very High"},
            {"name": "confidence", "type": "str", "required": True, "description": "Confidence level 0-1"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

Create `src/agents/fraud_identity.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_identity_fraud_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="IdentityFraudAgent",
        description="Detect synthetic identities: PAN-name mismatch, Aadhaar-face mismatch, duplicate PAN, age inconsistencies, impossible document combinations.",
        prompt=(
            "You are a Fraud Detection specialist focused on identity verification.\n\n"
            "KYC Documents:\n{kyc_documents}\n\n"
            "PAN Verification:\n{pan_verification}\n\n"
            "Aadhaar Data:\n{aadhaar_data}\n\n"
            "Face Match Result:\n{face_match}\n\n"
            "Application Metadata:\n{app_metadata}\n\n"
            "Instructions:\n"
            "1. Cross-check PAN name vs application name vs Aadhaar name.\n"
            "2. Verify face match confidence between selfie and ID photo.\n"
            "3. Check for duplicate PAN across recent applications.\n"
            "4. Detect age inconsistencies across documents.\n"
            "5. Flag impossible document combinations (e.g., DOB mismatch > 1 year).\n"
            "6. Calculate fraud risk score 0-100.\n\n"
            "Provide fraud assessment with evidence."
        ),
        inputs=[
            {"name": "kyc_documents", "type": "str", "required": True, "description": "All KYC document data"},
            {"name": "pan_verification", "type": "str", "required": True, "description": "PAN verification API result"},
            {"name": "aadhaar_data", "type": "str", "required": True, "description": "Aadhaar eKYC data"},
            {"name": "face_match", "type": "str", "required": True, "description": "Face match API result"},
            {"name": "app_metadata", "type": "str", "required": True, "description": "Application metadata"},
        ],
        outputs=[
            {"name": "fraud_risk_score", "type": "str", "required": True, "description": "Risk score 0-100"},
            {"name": "fraud_type", "type": "str", "required": True, "description": "Type of fraud if detected"},
            {"name": "confidence", "type": "str", "required": True, "description": "Detection confidence"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

Create `src/agents/fraud_document.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_doc_tampering_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="DocTamperingAgent",
        description="Detect document forgery: PDF metadata analysis, font consistency, image manipulation detection, salary figure anomaly detection.",
        prompt=(
            "You are a Document Forensics specialist.\n\n"
            "PDF Metadata:\n{pdf_metadata}\n\n"
            "OCR Extracted Data:\n{ocr_data}\n\n"
            "Font Analysis:\n{font_analysis}\n\n"
            "Instructions:\n"
            "1. Check PDF creation date vs stated document date.\n"
            "2. Analyze PDF creator software -- flag unusual editors.\n"
            "3. Check font consistency within the document.\n"
            "4. Detect salary figure anomalies (round numbers, unusual patterns).\n"
            "5. Check for image manipulation artifacts.\n"
            "6. Calculate tampering risk score 0-100.\n\n"
            "Provide tampering assessment with evidence."
        ),
        inputs=[
            {"name": "pdf_metadata", "type": "str", "required": True, "description": "PDF metadata (creator, dates, software)"},
            {"name": "ocr_data", "type": "str", "required": True, "description": "OCR extracted data from document"},
            {"name": "font_analysis", "type": "str", "required": True, "description": "Font consistency check results"},
        ],
        outputs=[
            {"name": "tampering_risk_score", "type": "str", "required": True, "description": "Risk score 0-100"},
            {"name": "tampered_fields", "type": "str", "required": True, "description": "Suspected tampered fields"},
            {"name": "evidence", "type": "str", "required": True, "description": "Forensic evidence found"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 5: Delete old debt_analyst.py**

```bash
rm src/agents/debt_analyst.py
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_agents/test_scoring_agents.py tests/test_agents/test_fraud_agents.py -v`
Expected: All 6 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/agents/ tests/test_agents/test_scoring_agents.py tests/test_agents/test_fraud_agents.py
git rm src/agents/debt_analyst.py
git commit -m "feat: add Phase 3 agents (risk assessment, fraud detection) - 6 agents with 4Cs framework"
```

---

## Task 6: Phase 4+5 Agents -- Decision Pipeline, Offer, Disbursement

**Files:**
- Modify: `src/agents/compliance.py`
- Create: `src/agents/pricing.py`
- Modify: `src/agents/decision.py`
- Create: `src/agents/offer_generator.py`
- Modify: `src/agents/xai_explainer.py`
- Create: `src/agents/disbursement.py`
- Create: `tests/test_agents/test_decision_pipeline.py`
- Create: `tests/test_agents/test_disbursement.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_agents/test_decision_pipeline.py`:

```python
from evoagentx.agents import CustomizeAgent

from src.agents.compliance import create_compliance_agent
from src.agents.pricing import create_pricing_agent
from src.agents.decision import create_decision_agent
from src.agents.offer_generator import create_offer_generator_agent
from src.agents.xai_explainer import create_xai_explainer_agent


def test_compliance_agent():
    agent = create_compliance_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "ComplianceCheckerAgent"
    assert "rbi" in agent.prompt.lower() or "fema" in agent.prompt.lower()


def test_pricing_agent():
    agent = create_pricing_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "PricingAgent"
    assert agent.llm_config.model == "gpt4o-fallback"


def test_decision_agent():
    agent = create_decision_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "DecisionMakerAgent"
    assert "conditional" in agent.prompt.lower()


def test_offer_generator_agent():
    agent = create_offer_generator_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "OfferGenerationAgent"
    assert agent.llm_config.model == "gpt4o-fallback"


def test_xai_explainer_agent():
    agent = create_xai_explainer_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "XAIExplainerAgent"
    assert "adverse" in agent.prompt.lower()
    assert "hindi" in agent.prompt.lower()
```

Create `tests/test_agents/test_disbursement.py`:

```python
from evoagentx.agents import CustomizeAgent

from src.agents.disbursement import create_disbursement_agent


def test_disbursement_agent():
    agent = create_disbursement_agent()
    assert isinstance(agent, CustomizeAgent)
    assert agent.name == "DisbursementAgent"
    assert agent.llm_config.model == "gpt4o-fallback"
    assert "neft" in agent.prompt.lower() or "imps" in agent.prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_agents/test_decision_pipeline.py tests/test_agents/test_disbursement.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Update compliance.py**

Replace `src/agents/compliance.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_compliance_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="ComplianceCheckerAgent",
        description="Validate against RBI guidelines, fair lending rules, FEMA for NRIs, adverse action requirements, bias checks.",
        prompt=(
            "You are a Regulatory Compliance specialist for Indian lending.\n\n"
            "All Agent Outputs:\n{agent_outputs}\n\n"
            "Proposed Score:\n{proposed_score}\n\n"
            "Applicant Demographics:\n{applicant_demographics}\n\n"
            "Instructions:\n"
            "1. Check fair lending compliance -- decision must not be based on gender, religion, caste.\n"
            "2. Apply the 4/5ths rule: approval rate disparity > 20% across demographics = flag.\n"
            "3. Verify RBI guidelines: income documentation, KYC requirements met.\n"
            "4. For NRI applicants, check FEMA compliance.\n"
            "5. If decision is denial, validate adverse action notice requirements.\n"
            "6. Verify interest rate is within RBI regulatory limits.\n"
            "7. Flag any regulatory concerns.\n\n"
            "Provide compliance status with detailed findings."
        ),
        inputs=[
            {"name": "agent_outputs", "type": "str", "required": True, "description": "All upstream agent outputs"},
            {"name": "proposed_score", "type": "str", "required": True, "description": "Composite credit score"},
            {"name": "applicant_demographics", "type": "str", "required": True, "description": "Demographics for bias check"},
        ],
        outputs=[
            {"name": "compliance_status", "type": "str", "required": True, "description": "pass/fail"},
            {"name": "required_conditions", "type": "str", "required": True, "description": "Conditions to meet"},
            {"name": "bias_flags", "type": "str", "required": True, "description": "Bias detection results"},
            {"name": "adverse_action_reasons", "type": "str", "required": False, "description": "Reasons if denial"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 4: Create pricing.py, update decision.py, create offer_generator.py, update xai_explainer.py, create disbursement.py**

Create `src/agents/pricing.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_pricing_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="PricingAgent",
        description="Calculate interest rate, processing fee, insurance premium based on risk score, loan amount, tenure, customer segment, and rate card.",
        prompt=(
            "You are a Loan Pricing specialist.\n\n"
            "Credit Score:\n{credit_score}\n\n"
            "Risk Category:\n{risk_category}\n\n"
            "Loan Details:\n{loan_details}\n\n"
            "Customer Segment:\n{customer_segment}\n\n"
            "Rate Card:\n{rate_card}\n\n"
            "Instructions:\n"
            "1. Look up base interest rate from rate card using risk category.\n"
            "2. Apply customer segment adjustment (existing customer, salaried at MNC, etc.).\n"
            "3. Calculate processing fee.\n"
            "4. Calculate insurance premium.\n"
            "5. Compute total cost of credit.\n"
            "6. Calculate EMI amount.\n\n"
            "Provide complete pricing breakdown."
        ),
        inputs=[
            {"name": "credit_score", "type": "str", "required": True, "description": "Composite credit score"},
            {"name": "risk_category", "type": "str", "required": True, "description": "Risk category"},
            {"name": "loan_details", "type": "str", "required": True, "description": "Amount, tenure"},
            {"name": "customer_segment", "type": "str", "required": True, "description": "Customer classification"},
            {"name": "rate_card", "type": "str", "required": True, "description": "Current rate card config"},
        ],
        outputs=[
            {"name": "interest_rate", "type": "str", "required": True, "description": "Annual interest rate %"},
            {"name": "processing_fee", "type": "str", "required": True, "description": "Processing fee amount"},
            {"name": "emi_amount", "type": "str", "required": True, "description": "Monthly EMI"},
            {"name": "total_cost", "type": "str", "required": True, "description": "Total cost of credit"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

Replace `src/agents/decision.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_decision_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="DecisionMakerAgent",
        description="Make final routing decision: Approve / Conditional Approve / Deny / Escalate to HITL. Apply confidence thresholds.",
        prompt=(
            "You are the Credit Decision Maker.\n\n"
            "Composite Score:\n{composite_score}\n\n"
            "Compliance Status:\n{compliance_status}\n\n"
            "Pricing:\n{pricing}\n\n"
            "Fraud Flags:\n{fraud_flags}\n\n"
            "Income Verification:\n{income_verification}\n\n"
            "Debt Burden:\n{debt_burden}\n\n"
            "Decision Rules:\n"
            "- APPROVED if: score >= 700, DTI <= 0.50, compliance = pass, no fraud flags, confidence >= 0.8.\n"
            "- CONDITIONAL if: score 600-699, or minor conditions from compliance.\n"
            "- DENIED if: score < 450, OR DTI > 0.65, OR compliance = fail, OR fraud detected.\n"
            "- ESCALATED if: score 450-599 with low confidence, OR compliance review needed, "
            "OR any agent flagged uncertainty.\n\n"
            "Instructions:\n"
            "1. Evaluate all criteria against thresholds.\n"
            "2. For CONDITIONAL: specify exact conditions (e.g., additional documentation, guarantor).\n"
            "3. For DENIED: generate specific adverse action reason codes.\n"
            "4. For ESCALATED: specify what requires human review.\n"
            "5. Log complete decision rationale.\n"
            "6. Assign confidence level.\n\n"
            "Provide decision with full reasoning."
        ),
        inputs=[
            {"name": "composite_score", "type": "str", "required": True, "description": "Score and risk category"},
            {"name": "compliance_status", "type": "str", "required": True, "description": "Compliance check result"},
            {"name": "pricing", "type": "str", "required": True, "description": "Pricing output"},
            {"name": "fraud_flags", "type": "str", "required": True, "description": "Fraud detection results"},
            {"name": "income_verification", "type": "str", "required": True, "description": "Income verification output"},
            {"name": "debt_burden", "type": "str", "required": True, "description": "DTI and obligations"},
        ],
        outputs=[
            {"name": "decision", "type": "str", "required": True, "description": "APPROVED/CONDITIONAL/DENIED/ESCALATED"},
            {"name": "conditions", "type": "str", "required": False, "description": "Conditions if conditional"},
            {"name": "rationale", "type": "str", "required": True, "description": "Decision reasoning"},
            {"name": "confidence", "type": "str", "required": True, "description": "Confidence 0-1"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

Create `src/agents/offer_generator.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_offer_generator_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="OfferGenerationAgent",
        description="Generate loan offer document with EMI schedule, interest rate, total cost, pre-payment clauses, T&C, validity.",
        prompt=(
            "You are a Loan Offer Generation specialist.\n\n"
            "Decision:\n{decision}\n\n"
            "Pricing:\n{pricing}\n\n"
            "Applicant Details:\n{applicant_details}\n\n"
            "Loan Details:\n{loan_details}\n\n"
            "Instructions:\n"
            "1. Generate complete EMI schedule (month-by-month).\n"
            "2. Include interest rate, processing fee, insurance premium.\n"
            "3. Calculate total cost of credit.\n"
            "4. Include pre-payment terms and charges.\n"
            "5. Set offer validity period (30 days from generation).\n"
            "6. Include standard T&C.\n\n"
            "Provide complete offer terms for PDF generation."
        ),
        inputs=[
            {"name": "decision", "type": "str", "required": True, "description": "Approved decision details"},
            {"name": "pricing", "type": "str", "required": True, "description": "Pricing breakdown"},
            {"name": "applicant_details", "type": "str", "required": True, "description": "Borrower info"},
            {"name": "loan_details", "type": "str", "required": True, "description": "Loan amount, tenure"},
        ],
        outputs=[
            {"name": "offer_terms", "type": "str", "required": True, "description": "Complete offer terms JSON"},
            {"name": "emi_schedule", "type": "str", "required": True, "description": "Month-by-month schedule"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

Replace `src/agents/xai_explainer.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_xai_explainer_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="XAIExplainerAgent",
        description="Generate human-readable explanations for credit decisions. Produce adverse action notices for denials. Support English + Hindi.",
        prompt=(
            "You are an Explainable AI (XAI) specialist.\n\n"
            "Decision Output:\n{decision_output}\n\n"
            "All Contributing Agent Outputs:\n{agent_outputs}\n\n"
            "Instructions:\n"
            "1. Generate plain-language explanation of the decision.\n"
            "2. List top contributing factors (positive and negative).\n"
            "3. For DENIED: create specific adverse action reason codes per regulatory requirements.\n"
            "4. For CONDITIONAL: explain what conditions must be met.\n"
            "5. For APPROVED: explain key strengths of the application.\n"
            "6. Provide actionable suggestions for improvement.\n"
            "7. Generate Hindi translation of the summary explanation.\n"
            "8. Create audit-ready decision summary.\n"
            "9. Never reveal proprietary scoring algorithms or exact thresholds.\n\n"
            "Provide explanations at three levels: summary, detailed, and regulatory audit."
        ),
        inputs=[
            {"name": "decision_output", "type": "str", "required": True, "description": "Decision and rationale"},
            {"name": "agent_outputs", "type": "str", "required": True, "description": "All agent outputs for context"},
        ],
        outputs=[
            {"name": "summary_explanation", "type": "str", "required": True, "description": "One-paragraph summary"},
            {"name": "detailed_explanation", "type": "str", "required": True, "description": "Factor breakdown"},
            {"name": "adverse_action_reasons", "type": "str", "required": False, "description": "Adverse action if denied"},
            {"name": "hindi_summary", "type": "str", "required": True, "description": "Hindi translation"},
            {"name": "audit_summary", "type": "str", "required": True, "description": "Audit-ready summary"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

Create `src/agents/disbursement.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_disbursement_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="gpt4o-fallback", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="DisbursementAgent",
        description="Verify e-sign, confirm e-mandate/NACH, trigger NEFT/IMPS transfer, create loan account in CBS, activate repayment schedule.",
        prompt=(
            "You are a Loan Disbursement specialist.\n\n"
            "Offer Acceptance:\n{offer_acceptance}\n\n"
            "E-Sign Status:\n{esign_status}\n\n"
            "E-Mandate Status:\n{emandate_status}\n\n"
            "Bank Account Details:\n{bank_details}\n\n"
            "Instructions:\n"
            "1. Verify e-sign is complete and valid.\n"
            "2. Confirm e-mandate/NACH registration is active.\n"
            "3. Verify beneficiary bank account via penny drop.\n"
            "4. Trigger NEFT/IMPS fund transfer.\n"
            "5. Create loan account in core banking system.\n"
            "6. Activate repayment schedule with first EMI date.\n"
            "7. Report disbursement status.\n\n"
            "Provide disbursement status with all details."
        ),
        inputs=[
            {"name": "offer_acceptance", "type": "str", "required": True, "description": "Accepted offer details"},
            {"name": "esign_status", "type": "str", "required": True, "description": "E-sign verification result"},
            {"name": "emandate_status", "type": "str", "required": True, "description": "E-mandate registration status"},
            {"name": "bank_details", "type": "str", "required": True, "description": "Beneficiary account details"},
        ],
        outputs=[
            {"name": "disbursement_status", "type": "str", "required": True, "description": "success/failed"},
            {"name": "loan_account_number", "type": "str", "required": True, "description": "CBS loan account"},
            {"name": "first_emi_date", "type": "str", "required": True, "description": "First EMI date"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_agents/test_decision_pipeline.py tests/test_agents/test_disbursement.py -v`
Expected: All 6 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/agents/ tests/test_agents/test_decision_pipeline.py tests/test_agents/test_disbursement.py
git commit -m "feat: add Phase 4-5 agents (compliance, pricing, decision, offer, XAI, disbursement)"
```

---

## Task 7: Orchestrator Rewrite and Workflow DAG

**Files:**
- Modify: `src/agents/orchestrator.py` (full rewrite)
- Delete: `src/workflows/credit_scoring_workflow.py`
- Create: `src/workflows/loan_underwriting_workflow.py`
- Modify: `src/agents/__init__.py`
- Create: `tests/test_workflow/test_loan_underwriting.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_workflow/__init__.py` (empty) and `tests/test_workflow/test_loan_underwriting.py`:

```python
from src.workflows.loan_underwriting_workflow import build_workflow_graph, create_workflow


def test_workflow_graph_has_22_nodes():
    graph = build_workflow_graph()
    # 22 agents as workflow nodes (excluding orchestrator which manages the workflow)
    assert len(graph.nodes) == 22


def test_workflow_graph_has_correct_edges():
    graph = build_workflow_graph()
    edge_sources = {e.source for e in graph.edges}
    edge_targets = {e.target for e in graph.edges}
    # Key edges exist
    assert "LeadQualification" in edge_sources
    assert "CreditDecision" in edge_targets
    assert "ScoreAggregation" in edge_targets


def test_create_workflow():
    workflow, agent_manager = create_workflow()
    assert workflow is not None
    assert agent_manager is not None
    # 23 agents total (22 + orchestrator)
    assert len(agent_manager._agents) >= 22
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workflow/test_loan_underwriting.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Rewrite orchestrator.py**

Replace `src/agents/orchestrator.py`:

```python
from __future__ import annotations

from evoagentx.agents import CustomizeAgent
from evoagentx.models import LiteLLMConfig

from src.config import get_settings

settings = get_settings()


def create_orchestrator_agent() -> CustomizeAgent:
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)

    return CustomizeAgent(
        name="OrchestratorAgent",
        description=(
            "Central coordinator: routes applications through the 22-agent workflow DAG, "
            "manages parallel execution in Phase 2 and 3, handles HITL escalation routing, "
            "feeds outcomes to evolution engine. Does NOT make credit decisions."
        ),
        prompt=(
            "You are the Orchestrator for the Personal Loan Underwriting system.\n\n"
            "Application Data:\n{application_data}\n\n"
            "Current Phase: {current_phase}\n"
            "Agent Outputs So Far: {agent_outputs}\n"
            "Applicant Employment Type: {employment_type}\n"
            "AA Consent: {aa_consent}\n\n"
            "Workflow Phases:\n"
            "Phase 1 (Intake): LeadQualification -> DocumentCollection\n"
            "Phase 2 (Extraction - parallel): DocClassifier -> OCR -> Normalizer | BureauPull | EmployerVerify | "
            "SalariedIncome OR SelfEmployedIncome | AccountAggregator (if consent)\n"
            "Phase 3 (Risk - parallel scoring then aggregate): RiskModeler | IncomeStability | DebtBurden | "
            "IdentityFraud | DocTampering -> ScoreAggregator\n"
            "Phase 4 (Decision - sequential): Compliance -> Pricing -> Decision -> OfferGeneration | XAI\n"
            "Phase 5 (Fulfillment): Disbursement (if offer accepted)\n\n"
            "Instructions:\n"
            "1. Determine current phase and which agents to invoke next.\n"
            "2. For Phase 2: route to SalariedIncome or SelfEmployedIncome based on employment type.\n"
            "3. For Phase 2: only invoke AccountAggregator if AA consent is true.\n"
            "4. Manage parallel group execution within phases.\n"
            "5. If any agent fails, determine recovery action.\n"
            "6. If decision is ESCALATED, route to HITL queue.\n\n"
            "Respond with next agents to invoke and routing decisions."
        ),
        inputs=[
            {"name": "application_data", "type": "str", "required": True, "description": "Application JSON"},
            {"name": "current_phase", "type": "str", "required": True, "description": "Current workflow phase"},
            {"name": "agent_outputs", "type": "str", "required": True, "description": "Completed agent outputs"},
            {"name": "employment_type", "type": "str", "required": True, "description": "salaried or self_employed"},
            {"name": "aa_consent", "type": "str", "required": True, "description": "Account Aggregator consent"},
        ],
        outputs=[
            {"name": "next_agents", "type": "str", "required": True, "description": "Agents to invoke next"},
            {"name": "routing_decision", "type": "str", "required": True, "description": "Routing rationale"},
        ],
        parse_mode="title",
        llm_config=llm_config,
    )
```

- [ ] **Step 4: Create loan_underwriting_workflow.py and delete old workflow**

Delete `src/workflows/credit_scoring_workflow.py` and create `src/workflows/loan_underwriting_workflow.py`:

```python
"""Personal Loan Underwriting Workflow DAG using EvoAgentX.

22-agent DAG across 5 phases:
  Phase 1 (Intake): LeadQualification -> DocumentCollection
  Phase 2 (Extraction): DocClassifier -> OCR -> Normalizer | BureauPull | EmployerVerify | Income | AA
  Phase 3 (Risk): RiskModeler | IncomeStability | DebtBurden | Fraud -> ScoreAggregator
  Phase 4 (Decision): Compliance -> Pricing -> Decision -> OfferGen | XAI
  Phase 5 (Fulfillment): Disbursement
"""
from __future__ import annotations

from evoagentx.workflow.workflow_graph import WorkFlowGraph, WorkFlowNode, WorkFlowEdge
from evoagentx.workflow import WorkFlow
from evoagentx.agents import AgentManager
from evoagentx.models import LiteLLMConfig, LiteLLM

from src.config import get_settings
from src.agents.orchestrator import create_orchestrator_agent
from src.agents.lead_qualification import create_lead_qualification_agent
from src.agents.document_collection import create_document_collection_agent
from src.agents.doc_classifier import create_doc_classifier_agent
from src.agents.ocr_extractor import create_ocr_extractor_agent
from src.agents.data_normalizer import create_data_normalizer_agent
from src.agents.bureau_pull import create_bureau_pull_agent
from src.agents.income_salaried import create_salaried_income_agent
from src.agents.income_self_employed import create_self_employed_income_agent
from src.agents.employer_verify import create_employer_verify_agent
from src.agents.account_aggregator import create_account_aggregator_agent
from src.agents.risk_modeler import create_risk_modeler_agent
from src.agents.income_stability import create_income_stability_agent
from src.agents.debt_burden import create_debt_burden_agent
from src.agents.score_aggregator import create_score_aggregator_agent
from src.agents.fraud_identity import create_identity_fraud_agent
from src.agents.fraud_document import create_doc_tampering_agent
from src.agents.compliance import create_compliance_agent
from src.agents.pricing import create_pricing_agent
from src.agents.decision import create_decision_agent
from src.agents.offer_generator import create_offer_generator_agent
from src.agents.xai_explainer import create_xai_explainer_agent
from src.agents.disbursement import create_disbursement_agent

settings = get_settings()

# Agent factory registry for easy iteration
AGENT_FACTORIES = [
    create_orchestrator_agent,
    create_lead_qualification_agent,
    create_document_collection_agent,
    create_doc_classifier_agent,
    create_ocr_extractor_agent,
    create_data_normalizer_agent,
    create_bureau_pull_agent,
    create_salaried_income_agent,
    create_self_employed_income_agent,
    create_employer_verify_agent,
    create_account_aggregator_agent,
    create_risk_modeler_agent,
    create_income_stability_agent,
    create_debt_burden_agent,
    create_score_aggregator_agent,
    create_identity_fraud_agent,
    create_doc_tampering_agent,
    create_compliance_agent,
    create_pricing_agent,
    create_decision_agent,
    create_offer_generator_agent,
    create_xai_explainer_agent,
    create_disbursement_agent,
]


def _node(name, desc, inputs, outputs, agents):
    return WorkFlowNode(name=name, description=desc, inputs=inputs, outputs=outputs, agents=agents)


def build_workflow_graph() -> WorkFlowGraph:
    """Build the 22-agent personal loan underwriting workflow DAG."""

    # -- Phase 1: Intake ---------------------------------------------------
    lead_qual = _node("LeadQualification", "Check eligibility",
        [{"name": "applicant_info", "type": "str", "required": True, "description": "Basic info"}],
        [{"name": "eligible", "type": "str", "description": "Result"}],
        ["LeadQualificationAgent"])

    doc_collect = _node("DocumentCollection", "Collect docs",
        [{"name": "application_id", "type": "str", "required": True, "description": "App ID"}],
        [{"name": "checklist_status", "type": "str", "description": "Status"}],
        ["DocumentCollectionAgent"])

    # -- Phase 2: Extraction -----------------------------------------------
    doc_classify = _node("DocumentClassification", "Classify docs",
        [{"name": "file_metadata", "type": "str", "required": True, "description": "File info"}],
        [{"name": "document_type", "type": "str", "description": "Type"}],
        ["DocumentClassifierAgent"])

    ocr_extract = _node("OCRExtraction", "Extract data via OCR",
        [{"name": "document_type", "type": "str", "required": True, "description": "Doc type"}],
        [{"name": "extracted_data", "type": "str", "description": "Extracted"}],
        ["OCRExtractionAgent"])

    data_norm = _node("DataNormalization", "Normalize data",
        [{"name": "extracted_data", "type": "str", "required": True, "description": "Raw data"}],
        [{"name": "normalized_data", "type": "str", "description": "Clean data"}],
        ["DataNormalizerAgent"])

    bureau = _node("BureauPull", "Pull bureau reports",
        [{"name": "applicant_info", "type": "str", "required": True, "description": "PAN/Name/DOB"}],
        [{"name": "consolidated_profile", "type": "str", "description": "Bureau data"}],
        ["BureauPullAgent"])

    employer = _node("EmployerVerification", "Verify employer",
        [{"name": "employer_details", "type": "str", "required": True, "description": "Employer info"}],
        [{"name": "employer_verified", "type": "str", "description": "Result"}],
        ["EmployerVerifyAgent"])

    income_sal = _node("SalariedIncome", "Verify salaried income",
        [{"name": "bank_statement_data", "type": "str", "required": True, "description": "Bank data"}],
        [{"name": "verified_monthly_income", "type": "str", "description": "Income"}],
        ["SalariedIncomeAgent"])

    income_se = _node("SelfEmployedIncome", "Verify self-employed income",
        [{"name": "bank_statement_data", "type": "str", "required": True, "description": "Bank data"}],
        [{"name": "estimated_monthly_income", "type": "str", "description": "Income"}],
        ["SelfEmployedIncomeAgent"])

    aa = _node("AccountAggregator", "Pull AA data",
        [{"name": "consent_status", "type": "str", "required": True, "description": "Consent"}],
        [{"name": "enriched_financial_data", "type": "str", "description": "AA data"}],
        ["AccountAggregatorAgent"])

    # -- Phase 3: Risk Assessment ------------------------------------------
    risk_model = _node("RiskModeling", "4Cs risk assessment",
        [{"name": "bureau_report", "type": "str", "required": True, "description": "Bureau"}],
        [{"name": "character_score", "type": "str", "description": "Score"}],
        ["RiskModelerAgent"])

    income_stab = _node("IncomeStability", "Income volatility scoring",
        [{"name": "income_history", "type": "str", "required": True, "description": "History"}],
        [{"name": "stability_score", "type": "str", "description": "Score"}],
        ["IncomeStabilityScorerAgent"])

    debt = _node("DebtBurden", "DTI and debt analysis",
        [{"name": "bureau_loans", "type": "str", "required": True, "description": "Loans"}],
        [{"name": "dti_ratio", "type": "str", "description": "DTI"}],
        ["DebtBurdenAnalyzerAgent"])

    fraud_id = _node("IdentityFraud", "Identity fraud detection",
        [{"name": "kyc_documents", "type": "str", "required": True, "description": "KYC"}],
        [{"name": "fraud_risk_score", "type": "str", "description": "Score"}],
        ["IdentityFraudAgent"])

    fraud_doc = _node("DocTampering", "Document tampering detection",
        [{"name": "pdf_metadata", "type": "str", "required": True, "description": "PDF data"}],
        [{"name": "tampering_risk_score", "type": "str", "description": "Score"}],
        ["DocTamperingAgent"])

    score_agg = _node("ScoreAggregation", "Combine scores",
        [{"name": "four_c_scores", "type": "str", "required": True, "description": "4Cs"}],
        [{"name": "composite_score", "type": "str", "description": "Score 300-900"}],
        ["ScoreAggregatorAgent"])

    # -- Phase 4: Decision -------------------------------------------------
    compliance = _node("ComplianceCheck", "Regulatory compliance",
        [{"name": "agent_outputs", "type": "str", "required": True, "description": "All outputs"}],
        [{"name": "compliance_status", "type": "str", "description": "Status"}],
        ["ComplianceCheckerAgent"])

    pricing = _node("Pricing", "Calculate rates and fees",
        [{"name": "credit_score", "type": "str", "required": True, "description": "Score"}],
        [{"name": "interest_rate", "type": "str", "description": "Rate"}],
        ["PricingAgent"])

    decision = _node("CreditDecision", "Final decision",
        [{"name": "composite_score", "type": "str", "required": True, "description": "Score"}],
        [{"name": "decision", "type": "str", "description": "Decision"}],
        ["DecisionMakerAgent"])

    offer = _node("OfferGeneration", "Generate offer PDF",
        [{"name": "decision", "type": "str", "required": True, "description": "Decision"}],
        [{"name": "offer_terms", "type": "str", "description": "Terms"}],
        ["OfferGenerationAgent"])

    xai = _node("Explanation", "Generate explanations",
        [{"name": "decision_output", "type": "str", "required": True, "description": "Decision"}],
        [{"name": "summary_explanation", "type": "str", "description": "Summary"}],
        ["XAIExplainerAgent"])

    # -- Phase 5: Fulfillment ----------------------------------------------
    disburse = _node("Disbursement", "Fund transfer and activation",
        [{"name": "offer_acceptance", "type": "str", "required": True, "description": "Accepted offer"}],
        [{"name": "disbursement_status", "type": "str", "description": "Status"}],
        ["DisbursementAgent"])

    # -- Edges (DAG dependencies) ------------------------------------------
    edges = [
        # Phase 1
        WorkFlowEdge(source="LeadQualification", target="DocumentCollection"),
        # Phase 1 -> Phase 2
        WorkFlowEdge(source="DocumentCollection", target="DocumentClassification"),
        WorkFlowEdge(source="DocumentCollection", target="BureauPull"),
        WorkFlowEdge(source="DocumentCollection", target="AccountAggregator"),
        # Phase 2 extraction chain
        WorkFlowEdge(source="DocumentClassification", target="OCRExtraction"),
        WorkFlowEdge(source="OCRExtraction", target="DataNormalization"),
        # Phase 2 verification (depends on normalized data)
        WorkFlowEdge(source="DataNormalization", target="EmployerVerification"),
        WorkFlowEdge(source="DataNormalization", target="SalariedIncome"),
        WorkFlowEdge(source="DataNormalization", target="SelfEmployedIncome"),
        # Phase 2 -> Phase 3
        WorkFlowEdge(source="BureauPull", target="RiskModeling"),
        WorkFlowEdge(source="DataNormalization", target="RiskModeling"),
        WorkFlowEdge(source="SalariedIncome", target="IncomeStability"),
        WorkFlowEdge(source="SelfEmployedIncome", target="IncomeStability"),
        WorkFlowEdge(source="BureauPull", target="DebtBurden"),
        WorkFlowEdge(source="DataNormalization", target="DebtBurden"),
        WorkFlowEdge(source="DataNormalization", target="IdentityFraud"),
        WorkFlowEdge(source="DocumentClassification", target="DocTampering"),
        # Phase 3 -> Score Aggregation
        WorkFlowEdge(source="RiskModeling", target="ScoreAggregation"),
        WorkFlowEdge(source="IncomeStability", target="ScoreAggregation"),
        WorkFlowEdge(source="DebtBurden", target="ScoreAggregation"),
        WorkFlowEdge(source="IdentityFraud", target="ScoreAggregation"),
        WorkFlowEdge(source="DocTampering", target="ScoreAggregation"),
        # Phase 3 -> Phase 4
        WorkFlowEdge(source="ScoreAggregation", target="ComplianceCheck"),
        WorkFlowEdge(source="ScoreAggregation", target="Pricing"),
        WorkFlowEdge(source="ComplianceCheck", target="CreditDecision"),
        WorkFlowEdge(source="Pricing", target="CreditDecision"),
        # Phase 4 -> Offer + XAI
        WorkFlowEdge(source="CreditDecision", target="OfferGeneration"),
        WorkFlowEdge(source="CreditDecision", target="Explanation"),
        # Phase 4 -> Phase 5
        WorkFlowEdge(source="OfferGeneration", target="Disbursement"),
    ]

    return WorkFlowGraph(
        goal="Process a personal loan application end-to-end: qualify lead, collect and extract documents, "
             "verify income and employment, assess risk with 4Cs framework, detect fraud, check compliance, "
             "price the loan, make a decision, generate offer, explain decision, and disburse funds.",
        nodes=[
            lead_qual, doc_collect, doc_classify, ocr_extract, data_norm, bureau,
            employer, income_sal, income_se, aa, risk_model, income_stab, debt,
            fraud_id, fraud_doc, score_agg, compliance, pricing, decision, offer, xai, disburse,
        ],
        edges=edges,
    )


def create_workflow() -> tuple[WorkFlow, AgentManager]:
    """Create the full 22-agent loan underwriting workflow."""
    llm_config = LiteLLMConfig(model="opus-primary", api_base=settings.litellm_base_url)
    llm = LiteLLM(llm_config)

    graph = build_workflow_graph()
    agent_manager = AgentManager()

    for factory in AGENT_FACTORIES:
        agent_manager.add_agent(factory())

    workflow = WorkFlow(graph=graph, agent_manager=agent_manager, llm=llm)
    return workflow, agent_manager
```

- [ ] **Step 5: Delete old workflow**

```bash
rm src/workflows/credit_scoring_workflow.py
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_workflow/test_loan_underwriting.py -v`
Expected: All 3 tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/agents/orchestrator.py src/workflows/ tests/test_workflow/
git rm src/workflows/credit_scoring_workflow.py
git commit -m "feat: rewrite orchestrator and workflow DAG for 22-agent architecture"
```

---

## Task 8: API Routes and Schemas -- Offers, Config, Audit, Notifications

**Files:**
- Modify: `src/api/models/schemas.py`
- Modify: `src/api/routes/applications.py`
- Create: `src/api/routes/offers.py`
- Create: `src/api/routes/config.py`
- Create: `src/api/routes/audit.py`
- Create: `src/api/routes/notifications.py`
- Modify: `src/main.py`
- Create: `tests/test_api/test_offers.py`
- Create: `tests/test_api/test_config.py`

This task adds the remaining API endpoints specified in the design doc: offer acceptance/resend, rate card config, product rules config, audit trail, and notification dispatch.

- [ ] **Step 1: Update schemas.py with new Pydantic models**

Add to `src/api/models/schemas.py`:

```python
# After existing schemas, add:

# -- Offer Schemas --------------------------------------------------------

class OfferAcceptRequest(BaseModel):
    accepted: bool = True
    bank_account_number: str | None = None
    bank_ifsc: str | None = None


class OfferAcceptResponse(BaseModel):
    status: str
    next_step: str


class OfferResponse(BaseModel):
    application_id: uuid.UUID
    emi_schedule: dict | None = None
    interest_rate: float | None = None
    total_cost: float | None = None
    validity_date: datetime | None = None
    accepted: bool = False

    model_config = {"from_attributes": True}


# -- Config Schemas -------------------------------------------------------

class RateCardResponse(BaseModel):
    id: uuid.UUID
    product_type: str
    risk_category: str
    interest_rate: float
    processing_fee_pct: float

    model_config = {"from_attributes": True}


class RateCardUpdate(BaseModel):
    interest_rate: float | None = None
    processing_fee_pct: float | None = None
    insurance_pct: float | None = None


class ProductRuleResponse(BaseModel):
    id: uuid.UUID
    product_type: str
    rule_name: str
    rule_type: str
    rule_config: dict

    model_config = {"from_attributes": True}


# -- Audit Schemas --------------------------------------------------------

class AuditDecisionEntry(BaseModel):
    application_id: uuid.UUID
    decision: str
    confidence: float
    decided_at: datetime
    rationale: str | None = None


class AuditResponse(BaseModel):
    decisions: list[AuditDecisionEntry]


# -- Notification Schemas -------------------------------------------------

class NotificationSendRequest(BaseModel):
    application_id: uuid.UUID | None = None
    channel: str  # sms, email, whatsapp
    recipient: str
    template_name: str


class NotificationResponse(BaseModel):
    status: str = "sent"
    notification_id: uuid.UUID

    model_config = {"from_attributes": True}


# -- Document Checklist ---------------------------------------------------

class DocumentChecklistItem(BaseModel):
    document_type: str
    required: bool = True
    uploaded: bool = False


class DocumentChecklistResponse(BaseModel):
    application_id: uuid.UUID
    checklist: list[DocumentChecklistItem]
    complete: bool
```

- [ ] **Step 2: Create new route files**

Create `src/api/routes/offers.py`:

```python
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Application, Offer, ApplicationStatus
from src.api.models.schemas import OfferAcceptRequest, OfferAcceptResponse, OfferResponse

router = APIRouter(prefix="/api/v1/applications", tags=["offers"])


@router.post("/{application_id}/accept-offer", response_model=OfferAcceptResponse)
async def accept_offer(application_id: uuid.UUID, payload: OfferAcceptRequest, db: AsyncSession = Depends(get_db)):
    """Borrower accepts offer. Triggers e-sign + disbursement workflow."""
    result = await db.execute(select(Offer).where(Offer.application_id == application_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.accepted:
        raise HTTPException(status_code=400, detail="Offer already accepted")

    offer.accepted = payload.accepted
    if payload.accepted:
        from datetime import datetime, timezone
        offer.accepted_at = datetime.now(timezone.utc)

    return OfferAcceptResponse(status="accepted", next_step="e-sign and disbursement initiated")


@router.post("/{application_id}/resend-offer")
async def resend_offer(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Resend offer via SMS/email/WhatsApp."""
    result = await db.execute(select(Offer).where(Offer.application_id == application_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # TODO: Trigger notification dispatch
    return {"status": "resent", "channels": ["sms", "email"]}
```

Create `src/api/routes/config.py`:

```python
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import RateCard, ProductRule

router = APIRouter(prefix="/api/v1/config", tags=["config"])


@router.get("/rate-cards")
async def get_rate_cards(db: AsyncSession = Depends(get_db)):
    """Current rate card configuration."""
    result = await db.execute(select(RateCard).where(RateCard.active == True))
    cards = result.scalars().all()
    return [{"id": str(c.id), "product_type": c.product_type.value, "risk_category": c.risk_category.value,
             "interest_rate": c.interest_rate, "processing_fee_pct": c.processing_fee_pct} for c in cards]


@router.put("/rate-cards/{card_id}")
async def update_rate_card(card_id: uuid.UUID, updates: dict, db: AsyncSession = Depends(get_db)):
    """Update rate card (admin only)."""
    result = await db.execute(select(RateCard).where(RateCard.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Rate card not found")

    for key, value in updates.items():
        if hasattr(card, key):
            setattr(card, key, value)

    return {"status": "updated"}


@router.get("/product-rules")
async def get_product_rules(db: AsyncSession = Depends(get_db)):
    """Product eligibility rules."""
    result = await db.execute(select(ProductRule).where(ProductRule.active == True))
    rules = result.scalars().all()
    return [{"id": str(r.id), "product_type": r.product_type.value, "rule_name": r.rule_name,
             "rule_type": r.rule_type.value, "rule_config": r.rule_config} for r in rules]


@router.put("/product-rules/{rule_id}")
async def update_product_rule(rule_id: uuid.UUID, updates: dict, db: AsyncSession = Depends(get_db)):
    """Update product rules (admin only)."""
    result = await db.execute(select(ProductRule).where(ProductRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for key, value in updates.items():
        if hasattr(rule, key):
            setattr(rule, key, value)

    return {"status": "updated"}
```

Create `src/api/routes/audit.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import CreditDecision

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/decisions")
async def get_decision_audit(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Query audit trail of all decisions."""
    result = await db.execute(
        select(CreditDecision)
        .order_by(CreditDecision.decided_at.desc())
        .offset(offset)
        .limit(limit)
    )
    decisions = result.scalars().all()

    return {
        "decisions": [
            {
                "application_id": str(d.application_id),
                "decision": d.decision.value,
                "confidence": d.confidence,
                "decided_at": d.decided_at.isoformat() if d.decided_at else None,
                "rationale": d.rationale,
            }
            for d in decisions
        ]
    }
```

Create `src/api/routes/notifications.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import Notification, NotificationChannel, NotificationStatus
from src.api.models.schemas import NotificationSendRequest

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("/send")
async def send_notification(payload: NotificationSendRequest, db: AsyncSession = Depends(get_db)):
    """Internal notification dispatch (SMS/email/WhatsApp)."""
    notification = Notification(
        application_id=payload.application_id,
        channel=NotificationChannel(payload.channel),
        template_name=payload.template_name,
        recipient=payload.recipient,
        status=NotificationStatus.SENT,
    )
    db.add(notification)
    await db.flush()

    # TODO: Dispatch to actual SMS/Email/WhatsApp gateway

    return {"status": "sent", "notification_id": str(notification.id)}
```

- [ ] **Step 3: Update main.py to include new routes**

In `src/main.py`, update the title and add new route imports:

Change:
```python
app = FastAPI(
    title="Credit Scoring Agent API",
    description="Self-evolving multi-agent credit scoring system",
    version="2.0.0",
    lifespan=lifespan,
)
```
to:
```python
app = FastAPI(
    title="Personal Loan Underwriting API",
    description="22-agent self-evolving personal loan underwriting system",
    version="3.0.0",
    lifespan=lifespan,
)
```

Add imports and route includes for offers, config, audit, notifications:
```python
from src.api.routes import applications, documents, hitl, evolution, reports, webhooks, offers, config, audit, notifications
```
and:
```python
app.include_router(offers.router)
app.include_router(config.router)
app.include_router(audit.router)
app.include_router(notifications.router)
```

Also update the lifespan log message:
```python
logger.info("starting_loan_underwriting_system", environment=settings.environment)
```

- [ ] **Step 4: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/ src/main.py
git commit -m "feat: add API routes for offers, config, audit, notifications - 26 total endpoints"
```

---

## Task 9: Update Existing Routes and Schemas for V3 Compatibility

**Files:**
- Modify: `src/api/routes/applications.py`
- Modify: `src/api/routes/hitl.py`
- Modify: `src/api/routes/evolution.py`
- Modify: `src/api/models/schemas.py`

- [ ] **Step 1: Update applications.py for new status flow and document checklist**

Add document checklist endpoint and update status handling to use new `ApplicationStatus` values:

Add to `src/api/routes/applications.py`:
```python
@router.get("/{application_id}/documents/checklist")
async def get_document_checklist(application_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Document checklist with status per required doc."""
    from src.db.models import Document, ApplicantProfile, EmploymentType

    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    profile_result = await db.execute(
        select(ApplicantProfile).where(ApplicantProfile.application_id == application_id)
    )
    profile = profile_result.scalar_one_or_none()

    docs_result = await db.execute(
        select(Document).where(Document.application_id == application_id)
    )
    uploaded_docs = {d.type.value for d in docs_result.scalars().all()}

    required = ["pan_card", "aadhaar", "bank_statement", "selfie"]
    if profile and profile.employment_type == EmploymentType.SALARIED:
        required.extend(["payslip", "form_16"])
    elif profile and profile.employment_type == EmploymentType.SELF_EMPLOYED:
        required.extend(["itr", "gst_certificate"])

    checklist = [{"document_type": r, "required": True, "uploaded": r in uploaded_docs} for r in required]

    return {"application_id": str(application_id), "checklist": checklist,
            "complete": all(item["uploaded"] for item in checklist)}
```

- [ ] **Step 2: Update schemas.py -- replace old Decision enum references**

In `src/api/models/schemas.py`, update imports to use `DecisionEnum` instead of `Decision`:

Change the import line to:
```python
from src.db.models import (
    ApplicationStatus, DocumentType, DecisionEnum, RiskCategory, LoanType,
    EmploymentType, OcrStatus,
)
```

And update all references from `Decision` to `DecisionEnum` in the schema classes (HITLItem, HITLDetailResponse, HITLReviewCreate, HITLReviewResponse, DecisionResponse).

- [ ] **Step 3: Update hitl.py to use DecisionEnum**

Update imports in `src/api/routes/hitl.py`:
```python
from src.db.models import Application, ApplicationStatus, CreditDecision, HITLReview, AgentOutput, DecisionEnum
```
Replace all `Decision.` with `DecisionEnum.` references.

- [ ] **Step 4: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/
git commit -m "feat: update existing routes for v3 schema compatibility"
```

---

## Task 10: Evolution Engine Updates and Final Integration

**Files:**
- Modify: `src/evolution/textgrad_config.py`
- Modify: `src/evolution/aflow_config.py`
- Modify: `src/evolution/mipro_config.py`
- Modify: `src/evolution/guardrails.py`
- Modify: `src/agents/__init__.py`
- Create: `.env.example`

- [ ] **Step 1: Update evolution configs for 22-agent targets**

Update `src/evolution/textgrad_config.py` to target the correct agents:

```python
TEXTGRAD_CONFIG = {
    "target_agents": [
        "RiskModelerAgent", "IncomeStabilityScorerAgent", "DebtBurdenAnalyzerAgent",
        "ScoreAggregatorAgent", "IdentityFraudAgent", "ComplianceCheckerAgent",
        "DecisionMakerAgent",
    ],
    "optimization_metric": "auc_roc",
    "frequency": "weekly",
    "outcome_window_days": [30, 60, 90],
}
```

Update `src/evolution/aflow_config.py`:

```python
AFLOW_CONFIG = {
    "target": "loan_underwriting_workflow",
    "frequency": "biweekly",
    "min_outcomes": 500,
    "optimization_targets": ["parallel_groups", "skip_paths", "conditional_routing"],
}
```

Update `src/evolution/mipro_config.py`:

```python
MIPRO_CONFIG = {
    "target_agents": [
        "DocumentClassifierAgent", "OCRExtractionAgent",
        "DataNormalizerAgent", "BureauPullAgent",
    ],
    "trigger": "performance_degradation",
    "optimization_targets": ["ocr_templates", "classification_thresholds", "extraction_rules"],
}
```

- [ ] **Step 2: Update guardrails for 22-agent system**

In `src/evolution/guardrails.py`, ensure the guardrails reference the new agents and 22-agent architecture. The bias check should use the `check_bias` tool:

```python
GUARDRAIL_CONFIG = {
    "bias_check": {
        "enabled": True,
        "disparate_impact_threshold": 0.80,
        "protected_categories": ["gender", "age", "geography"],
        "action_on_violation": "auto_rollback",
    },
    "performance_floor": {
        "enabled": True,
        "metric": "auc_roc",
        "max_drop_pct": 2.0,
        "action_on_violation": "auto_rollback",
    },
    "shadow_mode": {
        "enabled": True,
        "duration_hours": 48,
        "required_before_promotion": True,
    },
    "human_signoff": {
        "dag_topology_changes": True,
        "decision_threshold_change_pct": 5.0,
        "approver_role": "CRO",
    },
}
```

- [ ] **Step 3: Create .env.example with all documented env vars**

Create `.env.example`:

```env
# Environment
ENVIRONMENT=development

# PostgreSQL
POSTGRES_USER=loan
POSTGRES_PASSWORD=loan
POSTGRES_DB=loan_underwriting
DATABASE_URL=postgresql+asyncpg://loan:loan@postgres:5432/loan_underwriting

# Redis
REDIS_URL=redis://redis:6379

# Qdrant
QDRANT_URL=http://qdrant:6333

# LiteLLM
LITELLM_BASE_URL=http://litellm:4000

# Azure AI (Opus)
AZURE_AI_API_KEY=
AZURE_AI_API_BASE=
AZURE_AI_API_VERSION=2024-12-01-preview

# Azure OpenAI (GPT-4o)
AZURE_API_KEY=
AZURE_API_BASE=
AZURE_API_VERSION=2024-12-01-preview

# Document Store (MinIO dev / Azure Blob prod)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Mem0
MEM0_API_KEY=

# Azure Document Intelligence (OCR)
AZURE_FORM_RECOGNIZER_ENDPOINT=
AZURE_FORM_RECOGNIZER_KEY=

# API
API_SECRET_KEY=change-me-in-production

# Credit Bureau APIs
CIBIL_API_KEY=
EXPERIAN_API_KEY=
CRIF_API_KEY=
EQUIFAX_API_KEY=

# KYC APIs
PAN_VERIFY_API_KEY=
AADHAAR_API_KEY=
CKYC_API_KEY=
FACE_MATCH_API_KEY=
SANCTIONS_API_KEY=

# Financial APIs
PERFIOS_API_KEY=
SETU_AA_API_KEY=
GST_VERIFY_API_KEY=
ITR_VERIFY_API_KEY=

# Employer
COMPANY_REGISTRY_API_KEY=

# Disbursement APIs
ESIGN_API_KEY=
EMANDATE_API_KEY=
NEFT_API_KEY=
PENNY_DROP_API_KEY=
CBS_API_KEY=

# Notification APIs
SMS_API_KEY=
EMAIL_API_KEY=
WHATSAPP_API_KEY=
```

- [ ] **Step 4: Run full test suite one final time**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/evolution/ src/agents/__init__.py .env.example
git commit -m "feat: update evolution engine for 22-agent system, add .env.example"
```

---

## Summary

| Task | Description | Agent Count | New Files |
|------|-------------|-------------|-----------|
| 1 | Foundation (config, DB, Docker) | 0 | 2 |
| 2 | Internal tools (eligibility, scoring, finance) | 0 | 9 |
| 3 | External API clients (bureau, KYC, disbursement) | 0 | 18 |
| 4 | Phase 1+2 agents (intake, extraction) | 10 | 10 |
| 5 | Phase 3 agents (risk, fraud) | 6 | 5 |
| 6 | Phase 4+5 agents (decision, disbursement) | 6 | 3 |
| 7 | Orchestrator + workflow DAG | 1 | 1 |
| 8 | New API routes (offers, config, audit) | 0 | 4 |
| 9 | Route/schema compatibility updates | 0 | 0 |
| 10 | Evolution engine + .env | 0 | 1 |
| **Total** | | **23 agents** | **53+ files** |
