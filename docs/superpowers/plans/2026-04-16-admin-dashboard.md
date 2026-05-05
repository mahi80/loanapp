# Admin Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full officer dashboard (4 tabs: KPIs, Review Queue, Settings, Analytics), backend APIs, seed data, and customer HITL notification for a bank CTO demo.

**Architecture:** Single-page client component at `/dashboard` with client-side tab switching. Backend adds `admin.py` routes for stats/analytics, enhances HITL queue API, and adds document-requirements config API. Agent reads doc config from DB at runtime. Seed script populates demo data.

**Tech Stack:** Next.js 16, React 19, Tailwind CSS 4, Lucide React, Recharts, DM Serif Display + DM Sans + JetBrains Mono fonts. Backend: FastAPI, SQLAlchemy async, PostgreSQL.

**Spec:** `docs/superpowers/specs/2026-04-16-admin-dashboard-design.md`

---

## File Map

### Backend — New Files
| File | Responsibility |
|---|---|
| `src/api/routes/admin.py` | Dashboard stats, recent apps, analytics endpoints |
| `src/db/seed.py` | Demo data seeder for bank demo |

### Backend — Modified Files
| File | Changes |
|---|---|
| `src/main.py` | Register `admin_router` |
| `src/api/routes/config.py` | Add document-requirements GET/POST, add officer auth |
| `src/api/routes/hitl.py` | Enhance queue to return score, flags, timestamps, names |
| `src/api/models/schemas.py` | Add HITLQueueItemEnhanced schema |
| `src/graph/nodes/doc_collection.py` | Read doc config from DB instead of hardcoded list |

### Frontend — New Files
| File | Responsibility |
|---|---|
| `frontend/src/components/officer/officer-topbar.tsx` | Sticky topbar with nav tabs, clock, bell, avatar |
| `frontend/src/components/officer/dashboard-tab.tsx` | KPIs, recent apps, agent pipeline |
| `frontend/src/components/officer/review-tab.tsx` | Queue table + inline detail + action bar |
| `frontend/src/components/officer/settings-tab.tsx` | 4 sub-tabs container |
| `frontend/src/components/officer/doc-rules-panel.tsx` | Document requirements editor |
| `frontend/src/components/officer/rate-cards-panel.tsx` | Rate card editor |
| `frontend/src/components/officer/product-rules-panel.tsx` | Product rules editor |
| `frontend/src/components/officer/agents-panel.tsx` | Agent list with toggles |
| `frontend/src/components/officer/analytics-tab.tsx` | Charts + audit trail |
| `frontend/src/components/officer/officer.css` | All CSS variables, animations, grain overlay |

### Frontend — Modified Files
| File | Changes |
|---|---|
| `frontend/src/app/dashboard/layout.tsx` | Load 3 Google Fonts, warm parchment background |
| `frontend/src/app/dashboard/page.tsx` | Full SPA with tab switching |
| `frontend/src/components/status/application-detail.tsx` | Add decision banner for HITL |
| `frontend/package.json` | Add `recharts` dependency |

### Frontend — Deleted Files
| File | Reason |
|---|---|
| `frontend/src/app/dashboard/[id]/page.tsx` | Replaced by inline review detail |
| `frontend/src/components/dashboard/review-queue.tsx` | Replaced by officer/review-tab.tsx |
| `frontend/src/components/dashboard/action-bar.tsx` | Replaced by inline action bar in review-tab |

---

## Task 1: Seed Data Script

**Files:**
- Create: `src/db/seed.py`

- [ ] **Step 1: Create the seed script**

```python
"""Seed the database with realistic demo data for bank CTO demo.
Run: python -m src.db.seed
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, date, UTC
from sqlalchemy import select

from src.db.session import engine, async_session_factory
from src.db.models import (
    Base, User, UserRole, Application, ApplicationStatus, LoanType, EmploymentType,
    ApplicantProfile, CreditDecision, DecisionEnum, CreditScore, RiskCategory,
    HITLReview, RateCard, ProductRule, RuleType,
)


DEMO_APPS = [
    {"name": "Raj Kumar", "pan": "ABCPK1234A", "loan_type": "personal", "amount": 500000, "emp": "salaried", "status": "decided", "decision": "approved", "score": 780, "dti": 0.35, "risk": "low", "confidence": 0.92},
    {"name": "Priya Sharma", "pan": "DEFPS5678B", "loan_type": "personal", "amount": 350000, "emp": "salaried", "status": "decided", "decision": "escalated", "score": 612, "dti": 0.52, "risk": "medium", "confidence": 0.58},
    {"name": "Amit Patel", "pan": "GHIAP9012C", "loan_type": "home", "amount": 3500000, "emp": "salaried", "status": "decided", "decision": "denied", "score": 420, "dti": 0.68, "risk": "very_high", "confidence": 0.88},
    {"name": "Neha Gupta", "pan": "JKLNG3456D", "loan_type": "auto", "amount": 800000, "emp": "salaried", "status": "decided", "decision": "approved", "score": 745, "dti": 0.38, "risk": "low", "confidence": 0.90},
    {"name": "Suresh Iyer", "pan": "MNOSI7890E", "loan_type": "personal", "amount": 1200000, "emp": "self_employed", "status": "decided", "decision": "escalated", "score": 580, "dti": 0.55, "risk": "high", "confidence": 0.52},
    {"name": "Kavita Reddy", "pan": "PQRKR1234F", "loan_type": "personal", "amount": 600000, "emp": "salaried", "status": "decided", "decision": "escalated", "score": 645, "dti": 0.48, "risk": "medium", "confidence": 0.61},
    {"name": "Vikram Singh", "pan": "STUVS5678G", "loan_type": "personal", "amount": 250000, "emp": "salaried", "status": "decided", "decision": "approved", "score": 810, "dti": 0.28, "risk": "low", "confidence": 0.95},
    {"name": "Ananya Joshi", "pan": "WXYAJ9012H", "loan_type": "personal", "amount": 450000, "emp": "salaried", "status": "decided", "decision": "approved", "score": 720, "dti": 0.42, "risk": "low", "confidence": 0.85},
    {"name": "Deepak Nair", "pan": "BCADN3456I", "loan_type": "home", "amount": 5000000, "emp": "salaried", "status": "decided", "decision": "approved", "score": 760, "dti": 0.40, "risk": "low", "confidence": 0.89},
    {"name": "Meena Bose", "pan": "EFGMB7890J", "loan_type": "personal", "amount": 300000, "emp": "self_employed", "status": "decided", "decision": "denied", "score": 385, "dti": 0.72, "risk": "very_high", "confidence": 0.91},
    {"name": "Rohit Malhotra", "pan": "HIJRM1234K", "loan_type": "business", "amount": 2000000, "emp": "self_employed", "status": "decided", "decision": "conditional", "score": 660, "dti": 0.46, "risk": "medium", "confidence": 0.73},
    {"name": "Swati Kapoor", "pan": "KLMSK5678L", "loan_type": "auto", "amount": 650000, "emp": "salaried", "status": "processing", "decision": None, "score": None, "dti": None, "risk": None, "confidence": None},
    {"name": "Arjun Rao", "pan": "NOPAR9012M", "loan_type": "personal", "amount": 400000, "emp": "salaried", "status": "processing", "decision": None, "score": None, "dti": None, "risk": None, "confidence": None},
    {"name": "Lakshmi Menon", "pan": "QRSLM3456N", "loan_type": "home", "amount": 4500000, "emp": "salaried", "status": "processing", "decision": None, "score": None, "dti": None, "risk": None, "confidence": None},
    {"name": "Nikhil Das", "pan": "TUVND7890O", "loan_type": "business", "amount": 1500000, "emp": "self_employed", "status": "processing", "decision": None, "score": None, "dti": None, "risk": None, "confidence": None},
    {"name": "Pooja Agarwal", "pan": "WXYPA1234P", "loan_type": "personal", "amount": 200000, "emp": "salaried", "status": "lead", "decision": None, "score": None, "dti": None, "risk": None, "confidence": None},
    {"name": "Manish Tiwari", "pan": "ABCMT5678Q", "loan_type": "personal", "amount": 550000, "emp": "salaried", "status": "lead", "decision": None, "score": None, "dti": None, "risk": None, "confidence": None},
    {"name": "Ritu Verma", "pan": "DEFRV9012R", "loan_type": "auto", "amount": 900000, "emp": "self_employed", "status": "lead", "decision": None, "score": None, "dti": None, "risk": None, "confidence": None},
]

PERSONAL_DOC_CONFIG = {
    "loan_type": "personal",
    "groups": [
        {
            "group": "all", "label": "All Applicants", "icon": "user",
            "description": "Required regardless of employment",
            "documents": [
                {"name": "PAN Card", "key": "pan_card", "description": "Tax ID verification", "tier": "mandatory", "enabled": True},
                {"name": "Aadhaar Card", "key": "aadhaar", "description": "KYC identity proof", "tier": "mandatory", "enabled": True},
                {"name": "Applicant Photo", "key": "selfie", "description": "Face match verification", "tier": "mandatory", "enabled": True},
                {"name": "Bank Statement", "key": "bank_statement", "description": "6 months, income & cash flow", "tier": "mandatory", "enabled": True},
                {"name": "Address Proof", "key": "address_proof", "description": "If different from Aadhaar", "tier": "optional", "enabled": True},
            ],
        },
        {
            "group": "salaried", "label": "Salaried", "icon": "briefcase",
            "description": "Additional for salaried employees",
            "documents": [
                {"name": "Payslips (3 months)", "key": "payslip", "description": "Salary verification", "tier": "mandatory", "enabled": True},
                {"name": "Form 16", "key": "form_16", "description": "TDS confirmation", "tier": "recommended", "enabled": True},
                {"name": "Employment Letter", "key": "employment_letter", "description": "Employer verification", "tier": "recommended", "enabled": True},
                {"name": "Salary Certificate", "key": "salary_certificate", "description": "Government employees", "tier": "optional", "enabled": False},
            ],
        },
        {
            "group": "self_employed", "label": "Self-Employed", "icon": "store",
            "description": "Additional for business owners",
            "documents": [
                {"name": "ITR (2 years)", "key": "itr", "description": "Income declaration", "tier": "mandatory", "enabled": True},
                {"name": "GST Certificate", "key": "gst_certificate", "description": "Business legitimacy", "tier": "recommended", "enabled": True},
                {"name": "Business Registration", "key": "business_registration", "description": "Udyam / Shop license", "tier": "recommended", "enabled": True},
                {"name": "P&L Statement", "key": "pl_statement", "description": "Business financials", "tier": "optional", "enabled": False},
                {"name": "Balance Sheet", "key": "balance_sheet", "description": "Audited net worth", "tier": "optional", "enabled": False},
            ],
        },
    ],
}

HOME_DOC_CONFIG = {
    "loan_type": "home",
    "groups": [
        {
            "group": "all", "label": "All Applicants", "icon": "user",
            "description": "Required regardless of employment",
            "documents": [
                {"name": "PAN Card", "key": "pan_card", "description": "Tax ID verification", "tier": "mandatory", "enabled": True},
                {"name": "Aadhaar Card", "key": "aadhaar", "description": "KYC identity proof", "tier": "mandatory", "enabled": True},
                {"name": "Applicant Photo", "key": "selfie", "description": "Face match verification", "tier": "mandatory", "enabled": True},
                {"name": "Bank Statement", "key": "bank_statement", "description": "6 months, income & cash flow", "tier": "mandatory", "enabled": True},
                {"name": "Address Proof", "key": "address_proof", "description": "If different from Aadhaar", "tier": "optional", "enabled": True},
                {"name": "Property Documents", "key": "property_docs", "description": "Title deed, ownership proof", "tier": "mandatory", "enabled": True},
                {"name": "Sale Agreement", "key": "sale_agreement", "description": "Purchase agreement copy", "tier": "mandatory", "enabled": True},
                {"name": "Property Valuation", "key": "property_valuation", "description": "Third-party valuation report", "tier": "recommended", "enabled": True},
            ],
        },
        {
            "group": "salaried", "label": "Salaried", "icon": "briefcase",
            "description": "Additional for salaried employees",
            "documents": [
                {"name": "Payslips (6 months)", "key": "payslip", "description": "Salary verification", "tier": "mandatory", "enabled": True},
                {"name": "Form 16", "key": "form_16", "description": "TDS confirmation", "tier": "mandatory", "enabled": True},
                {"name": "Employment Letter", "key": "employment_letter", "description": "Employer verification", "tier": "recommended", "enabled": True},
            ],
        },
        {
            "group": "self_employed", "label": "Self-Employed", "icon": "store",
            "description": "Additional for business owners",
            "documents": [
                {"name": "ITR (3 years)", "key": "itr", "description": "Income declaration", "tier": "mandatory", "enabled": True},
                {"name": "GST Certificate", "key": "gst_certificate", "description": "Business legitimacy", "tier": "mandatory", "enabled": True},
                {"name": "Business Registration", "key": "business_registration", "description": "Udyam / Shop license", "tier": "recommended", "enabled": True},
                {"name": "P&L Statement", "key": "pl_statement", "description": "Business financials", "tier": "recommended", "enabled": True},
                {"name": "Balance Sheet", "key": "balance_sheet", "description": "Audited net worth", "tier": "recommended", "enabled": True},
            ],
        },
    ],
}

AUTO_DOC_CONFIG = {
    "loan_type": "auto",
    "groups": [
        {
            "group": "all", "label": "All Applicants", "icon": "user",
            "description": "Required regardless of employment",
            "documents": [
                {"name": "PAN Card", "key": "pan_card", "description": "Tax ID verification", "tier": "mandatory", "enabled": True},
                {"name": "Aadhaar Card", "key": "aadhaar", "description": "KYC identity proof", "tier": "mandatory", "enabled": True},
                {"name": "Applicant Photo", "key": "selfie", "description": "Face match verification", "tier": "mandatory", "enabled": True},
                {"name": "Bank Statement", "key": "bank_statement", "description": "6 months, income & cash flow", "tier": "mandatory", "enabled": True},
                {"name": "Address Proof", "key": "address_proof", "description": "If different from Aadhaar", "tier": "optional", "enabled": True},
                {"name": "Quotation / Proforma Invoice", "key": "vehicle_quotation", "description": "Dealer quotation for vehicle", "tier": "mandatory", "enabled": True},
                {"name": "Existing Vehicle RC", "key": "vehicle_rc", "description": "If trade-in applicable", "tier": "optional", "enabled": False},
            ],
        },
        {
            "group": "salaried", "label": "Salaried", "icon": "briefcase",
            "description": "Additional for salaried employees",
            "documents": [
                {"name": "Payslips (3 months)", "key": "payslip", "description": "Salary verification", "tier": "mandatory", "enabled": True},
                {"name": "Form 16", "key": "form_16", "description": "TDS confirmation", "tier": "recommended", "enabled": True},
            ],
        },
        {
            "group": "self_employed", "label": "Self-Employed", "icon": "store",
            "description": "Additional for business owners",
            "documents": [
                {"name": "ITR (2 years)", "key": "itr", "description": "Income declaration", "tier": "mandatory", "enabled": True},
                {"name": "GST Certificate", "key": "gst_certificate", "description": "Business legitimacy", "tier": "recommended", "enabled": True},
            ],
        },
    ],
}

BUSINESS_DOC_CONFIG = {
    "loan_type": "business",
    "groups": [
        {
            "group": "all", "label": "All Applicants", "icon": "user",
            "description": "Required for all business loan applicants",
            "documents": [
                {"name": "PAN Card", "key": "pan_card", "description": "Tax ID verification", "tier": "mandatory", "enabled": True},
                {"name": "Aadhaar Card", "key": "aadhaar", "description": "KYC identity proof", "tier": "mandatory", "enabled": True},
                {"name": "Applicant Photo", "key": "selfie", "description": "Face match verification", "tier": "mandatory", "enabled": True},
                {"name": "Bank Statement (12 months)", "key": "bank_statement", "description": "Business account cash flow", "tier": "mandatory", "enabled": True},
                {"name": "Address Proof", "key": "address_proof", "description": "Business or personal", "tier": "optional", "enabled": True},
                {"name": "ITR (3 years)", "key": "itr", "description": "Income declaration", "tier": "mandatory", "enabled": True},
                {"name": "GST Certificate", "key": "gst_certificate", "description": "Business legitimacy", "tier": "mandatory", "enabled": True},
                {"name": "Business Registration", "key": "business_registration", "description": "Udyam / Shop license / CoI", "tier": "mandatory", "enabled": True},
                {"name": "P&L Statement (2 years)", "key": "pl_statement", "description": "Business financials", "tier": "mandatory", "enabled": True},
                {"name": "Balance Sheet (2 years)", "key": "balance_sheet", "description": "Audited net worth", "tier": "mandatory", "enabled": True},
                {"name": "Partnership Deed / MOA", "key": "partnership_deed", "description": "Entity structure", "tier": "recommended", "enabled": True},
                {"name": "Office Proof", "key": "office_proof", "description": "Lease or ownership", "tier": "recommended", "enabled": True},
            ],
        },
    ],
}

RATE_CARDS = [
    # Personal
    ("personal", "low", 700, 900, 10.5, 1.5, 0.5),
    ("personal", "medium", 600, 699, 13.0, 2.0, 0.75),
    ("personal", "high", 450, 599, 16.5, 2.5, 1.0),
    ("personal", "very_high", 300, 449, 0, 0, 0),
    # Home
    ("home", "low", 700, 900, 8.5, 0.5, 0.25),
    ("home", "medium", 600, 699, 9.5, 0.75, 0.4),
    ("home", "high", 450, 599, 11.0, 1.0, 0.5),
    ("home", "very_high", 300, 449, 0, 0, 0),
    # Auto
    ("auto", "low", 700, 900, 9.0, 1.0, 0.5),
    ("auto", "medium", 600, 699, 11.5, 1.5, 0.6),
    ("auto", "high", 450, 599, 14.0, 2.0, 0.8),
    ("auto", "very_high", 300, 449, 0, 0, 0),
    # Business
    ("business", "low", 700, 900, 12.0, 2.0, 0.5),
    ("business", "medium", 600, 699, 14.5, 2.5, 0.75),
    ("business", "high", 450, 599, 17.5, 3.0, 1.0),
    ("business", "very_high", 300, 449, 0, 0, 0),
]

PRODUCT_RULES = [
    ("personal", "min_age", {"min_age": 21, "max_age": 58}),
    ("personal", "min_income", {"min_monthly_income": 15000}),
    ("personal", "max_multiplier", {"max_loan_income_multiplier": 60}),
    ("home", "min_age", {"min_age": 23, "max_age": 60}),
    ("home", "min_income", {"min_monthly_income": 25000}),
    ("home", "max_multiplier", {"max_loan_income_multiplier": 200}),
    ("auto", "min_age", {"min_age": 21, "max_age": 60}),
    ("auto", "min_income", {"min_monthly_income": 20000}),
    ("auto", "max_multiplier", {"max_loan_income_multiplier": 48}),
    ("business", "min_age", {"min_age": 25, "max_age": 65}),
    ("business", "min_income", {"min_monthly_income": 30000}),
    ("business", "max_multiplier", {"max_loan_income_multiplier": 100}),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Check if already seeded
        existing = await db.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        now = datetime.now(UTC)

        # Users
        customer = User(
            google_id="demo_customer_001", email="customer@demo.bank",
            name="Demo Customer", role=UserRole.CUSTOMER,
        )
        officer = User(
            google_id="demo_officer_001", email="officer@demo.bank",
            name="Hemant Rawat", role=UserRole.OFFICER,
        )
        db.add_all([customer, officer])
        await db.flush()

        # Applications
        for i, app_data in enumerate(DEMO_APPS):
            hours_ago = (len(DEMO_APPS) - i) * 3  # Spread over time
            ref = f"LN-{uuid.uuid4().hex[:8].upper()}"
            emp = EmploymentType(app_data["emp"]) if app_data["emp"] else None
            status = ApplicationStatus(app_data["status"])

            app = Application(
                applicant_name=app_data["name"],
                pan_number=app_data["pan"],
                loan_amount=app_data["amount"],
                loan_type=LoanType(app_data["loan_type"]),
                employment_type=emp,
                status=status,
                user_id=customer.id,
                reference_number=ref,
                phase_history=[{"phase": "intake", "completed_at": (now - timedelta(hours=hours_ago)).isoformat()}],
            )
            db.add(app)
            await db.flush()

            # Profile
            profile = ApplicantProfile(
                application_id=app.id,
                income=app_data["amount"] / 20,
                employer="TCS" if app_data["emp"] == "salaried" else "Self",
                employment_type=emp,
                city="Mumbai",
            )
            db.add(profile)

            # Credit Score + Decision for decided/escalated apps
            if app_data["score"] is not None:
                cs = CreditScore(
                    application_id=app.id,
                    composite_score=app_data["score"],
                    dti_ratio=app_data["dti"],
                    risk_category=RiskCategory(app_data["risk"]),
                    confidence=app_data["confidence"],
                    four_c_scores={"character": 70, "capacity": 65, "capital": 60, "collateral": 50},
                    stability_score=0.75,
                )
                db.add(cs)

            if app_data["decision"]:
                cd = CreditDecision(
                    application_id=app.id,
                    decision=DecisionEnum(app_data["decision"]),
                    confidence=app_data["confidence"] or 0.5,
                    rationale=f"Composite score {app_data['score']}, DTI {app_data['dti']}",
                    conditions={"flags": _derive_flags(app_data)},
                )
                db.add(cd)

        # HITL Reviews (2 — for the first two escalated apps)
        escalated_apps = [a for a in DEMO_APPS if a["decision"] == "escalated"]
        # We'll add reviews for Priya (override: approved) after flushing
        await db.flush()

        # Find Priya's app for override demo
        priya_result = await db.execute(
            select(Application).where(Application.pan_number == "DEFPS5678B")
        )
        priya_app = priya_result.scalar_one_or_none()
        if priya_app:
            hitl1 = HITLReview(
                application_id=priya_app.id,
                officer_id=str(officer.id),
                officer_decision=DecisionEnum.APPROVED,
                notes="Strong employer (TCS), borderline DTI acceptable for stable income",
            )
            db.add(hitl1)

        # Rate Cards
        for lt, rc, min_s, max_s, rate, fee, ins in RATE_CARDS:
            card = RateCard(
                product_type=LoanType(lt),
                risk_category=RiskCategory(rc),
                min_score=min_s, max_score=max_s,
                interest_rate=rate, processing_fee_pct=fee, insurance_pct=ins,
                effective_from=date(2026, 1, 1), active=True,
            )
            db.add(card)

        # Product Rules
        for lt, name, config in PRODUCT_RULES:
            rule = ProductRule(
                product_type=LoanType(lt),
                rule_name=name, rule_type=RuleType.ELIGIBILITY,
                rule_config=config, active=True,
            )
            db.add(rule)

        # Document Requirements (4 loan types)
        for doc_config in [PERSONAL_DOC_CONFIG, HOME_DOC_CONFIG, AUTO_DOC_CONFIG, BUSINESS_DOC_CONFIG]:
            rule = ProductRule(
                product_type=LoanType(doc_config["loan_type"]),
                rule_name="document_requirements",
                rule_type=RuleType.POLICY,
                rule_config=doc_config, active=True,
            )
            db.add(rule)

        await db.commit()
        print(f"Seeded: {len(DEMO_APPS)} applications, 2 users, {len(RATE_CARDS)} rate cards, {len(PRODUCT_RULES)} product rules, 4 doc configs")


def _derive_flags(app_data: dict) -> list[str]:
    flags = []
    if app_data.get("dti") and app_data["dti"] > 0.50:
        flags.append("Borderline DTI")
    if app_data.get("score") and app_data["score"] < 600:
        flags.append("Low score")
    if app_data.get("amount") and app_data["amount"] > 1000000:
        flags.append("High amt")
    return flags


if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 2: Test the seed script runs without errors**

Run: `cd /Users/hemantrawat/Documents/ACP_framework/sub-agents/Loan_origination_Agent && .venv/bin/python -m src.db.seed`

Expected: "Seeded: 18 applications, 2 users, 16 rate cards, 12 product rules, 4 doc configs" (requires running PostgreSQL)

- [ ] **Step 3: Commit**

```bash
git add src/db/seed.py
git commit -m "feat: add demo seed script for bank CTO demo"
```

---

## Task 2: Backend Admin APIs + HITL Enhancement

**Files:**
- Create: `src/api/routes/admin.py`
- Modify: `src/main.py`
- Modify: `src/api/routes/hitl.py`
- Modify: `src/api/routes/config.py`
- Modify: `src/api/models/schemas.py`

- [ ] **Step 1: Create admin.py with stats, recent-apps, and analytics endpoints**

```python
"""Admin dashboard API endpoints — officer role required."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, UTC

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import (
    Application, ApplicationStatus, CreditDecision, DecisionEnum,
    CreditScore, HITLReview, User,
)
from src.auth.middleware import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
officer_required = Depends(require_role("officer"))


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Dashboard KPI aggregates."""
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    prev_month_start = now - timedelta(days=60)
    prev_month_end = now - timedelta(days=30)

    # Total applications
    total_result = await db.execute(select(func.count(Application.id)))
    total = total_result.scalar() or 0

    # Weekly count
    weekly_result = await db.execute(
        select(func.count(Application.id)).where(Application.created_at >= week_ago)
    )
    weekly = weekly_result.scalar() or 0

    # Monthly count
    monthly_result = await db.execute(
        select(func.count(Application.id)).where(Application.created_at >= month_ago)
    )
    monthly = monthly_result.scalar() or 0

    # Previous period counts for trend calculation
    prev_week = now - timedelta(days=14)
    prev_weekly_result = await db.execute(
        select(func.count(Application.id)).where(
            Application.created_at >= prev_week,
            Application.created_at < week_ago,
        )
    )
    prev_weekly = prev_weekly_result.scalar() or 1  # avoid div by zero

    prev_monthly_result = await db.execute(
        select(func.count(Application.id)).where(
            Application.created_at >= prev_month_start,
            Application.created_at < prev_month_end,
        )
    )
    prev_monthly = prev_monthly_result.scalar() or 1

    weekly_change = round(((weekly - prev_weekly) / prev_weekly) * 100, 1) if prev_weekly else 0
    monthly_change = round(((monthly - prev_monthly) / prev_monthly) * 100, 1) if prev_monthly else 0

    # Decision breakdown
    breakdown_result = await db.execute(
        select(CreditDecision.decision, func.count(CreditDecision.id))
        .group_by(CreditDecision.decision)
    )
    breakdown = {row[0].value: row[1] for row in breakdown_result.all()}

    # AI confidence (average from CreditScore)
    conf_result = await db.execute(select(func.avg(CreditScore.confidence)))
    avg_confidence = round((conf_result.scalar() or 0.85) * 100, 1)

    # Override rate
    total_decisions = await db.execute(select(func.count(CreditDecision.id)))
    total_dec_count = total_decisions.scalar() or 1
    override_result = await db.execute(select(func.count(HITLReview.id)))
    override_count = override_result.scalar() or 0
    override_rate = round((override_count / total_dec_count) * 100, 1)

    # Avg processing time (hours between created_at and decided_at for decided apps)
    decided_apps = await db.execute(
        select(Application.created_at, CreditDecision.decided_at)
        .join(CreditDecision, CreditDecision.application_id == Application.id)
    )
    durations = []
    for app_created, dec_decided in decided_apps.all():
        if app_created and dec_decided:
            durations.append((dec_decided - app_created).total_seconds() / 3600)
    avg_hours = round(sum(durations) / len(durations), 1) if durations else 4.2

    # Pending review count
    pending_result = await db.execute(
        select(func.count(Application.id))
        .join(CreditDecision, CreditDecision.application_id == Application.id)
        .where(CreditDecision.decision == DecisionEnum.ESCALATED)
        .outerjoin(HITLReview, HITLReview.application_id == Application.id)
        .where(HITLReview.id.is_(None))
    )
    pending_count = pending_result.scalar() or 0

    # Oldest pending
    oldest_result = await db.execute(
        select(func.min(CreditDecision.decided_at))
        .where(CreditDecision.decision == DecisionEnum.ESCALATED)
        .outerjoin(HITLReview, HITLReview.application_id == CreditDecision.application_id)
        .where(HITLReview.id.is_(None))
    )
    oldest_ts = oldest_result.scalar()
    oldest_minutes = int((now - oldest_ts).total_seconds() / 60) if oldest_ts else 0

    return {
        "total_applications": total,
        "weekly_change_pct": weekly_change,
        "monthly_change_pct": monthly_change,
        "decision_breakdown": {
            "approved": breakdown.get("approved", 0),
            "denied": breakdown.get("denied", 0),
            "escalated": breakdown.get("escalated", 0),
            "conditional": breakdown.get("conditional", 0),
        },
        "ai_confidence_pct": avg_confidence,
        "override_rate_pct": override_rate,
        "avg_processing_hours": avg_hours,
        "processing_change_pct": -22.0,  # Hardcoded for demo; real computation needs 2+ months of data
        "pending_review_count": pending_count,
        "oldest_pending_minutes": oldest_minutes,
    }


@router.get("/recent-applications")
async def get_recent_applications(
    limit: int = Query(4, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Recent applications for dashboard list."""
    result = await db.execute(
        select(Application)
        .order_by(Application.created_at.desc())
        .limit(limit)
    )
    apps = result.scalars().all()

    items = []
    for app in apps:
        # Get decision if exists
        dec_result = await db.execute(
            select(CreditDecision).where(CreditDecision.application_id == app.id)
        )
        decision = dec_result.scalar_one_or_none()

        items.append({
            "id": str(app.id),
            "applicant_name": app.applicant_name,
            "reference_number": app.reference_number or "",
            "loan_type": app.loan_type.value,
            "loan_amount": float(app.loan_amount),
            "status": app.status.value,
            "decision": decision.decision.value if decision else None,
            "created_at": app.created_at.isoformat(),
        })

    return items


@router.get("/analytics/trends")
async def get_approval_trends(
    weeks: int = Query(8, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Weekly decision trends for chart."""
    now = datetime.now(UTC)
    result = []
    for w in range(weeks - 1, -1, -1):
        week_start = now - timedelta(weeks=w + 1)
        week_end = now - timedelta(weeks=w)
        for decision_type in ["approved", "denied", "escalated", "conditional"]:
            count_result = await db.execute(
                select(func.count(CreditDecision.id))
                .where(
                    CreditDecision.decision == DecisionEnum(decision_type),
                    CreditDecision.decided_at >= week_start,
                    CreditDecision.decided_at < week_end,
                )
            )
            count = count_result.scalar() or 0
            # Find or create week entry
            week_label = week_start.strftime("%Y-W%V")
            existing = next((r for r in result if r["week"] == week_label), None)
            if not existing:
                existing = {"week": week_label, "approved": 0, "denied": 0, "escalated": 0, "conditional": 0}
                result.append(existing)
            existing[decision_type] = count

    return {"weeks": result}


@router.get("/analytics/risk-distribution")
async def get_risk_distribution(
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Score distribution buckets for chart."""
    buckets = [
        ("700-900", "low", 700, 900),
        ("600-699", "medium", 600, 699),
        ("450-599", "high", 450, 599),
        ("300-449", "very_high", 300, 449),
    ]
    result = []
    for label, category, min_s, max_s in buckets:
        count_result = await db.execute(
            select(func.count(CreditScore.id)).where(
                CreditScore.composite_score >= min_s,
                CreditScore.composite_score <= max_s,
            )
        )
        result.append({
            "range": label,
            "category": category,
            "count": count_result.scalar() or 0,
        })
    return {"buckets": result}


@router.get("/analytics/audit-trail")
async def get_audit_trail(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _officer: User = officer_required,
):
    """Decision audit trail with override detection."""
    result = await db.execute(
        select(CreditDecision, Application, HITLReview)
        .join(Application, Application.id == CreditDecision.application_id)
        .outerjoin(HITLReview, HITLReview.application_id == Application.id)
        .order_by(CreditDecision.decided_at.desc())
        .limit(limit)
    )
    rows = result.all()

    items = []
    for decision, app, review in rows:
        is_override = review is not None and review.officer_decision != decision.decision
        items.append({
            "application_id": str(app.id),
            "applicant_name": app.applicant_name,
            "ai_decision": decision.decision.value,
            "officer_decision": review.officer_decision.value if review else None,
            "is_override": is_override,
            "confidence": decision.confidence,
            "notes": review.notes if review else None,
            "decided_at": decision.decided_at.isoformat(),
        })

    return items
```

- [ ] **Step 2: Register admin router in main.py**

Add to `src/main.py` imports:
```python
from src.api.routes.admin import router as admin_router
```

Add after existing router includes:
```python
app.include_router(admin_router)
```

- [ ] **Step 3: Enhance HITL queue API in hitl.py**

Replace the `get_hitl_queue` function in `src/api/routes/hitl.py` to return enhanced data:

The existing function returns hardcoded `escalation_reason`. Replace the items loop to query `CreditScore` and compute real risk flags, include `applicant_name`, `reference_number`, `composite_score`, and `waiting_since`.

- [ ] **Step 4: Add document-requirements endpoints to config.py**

Add `GET /api/v1/config/document-requirements` and `POST /api/v1/config/document-requirements` to `src/api/routes/config.py`. Add officer auth to existing rate-card and product-rule endpoints.

- [ ] **Step 5: Run existing tests to verify nothing broke**

Run: `.venv/bin/python -m pytest tests/ -x -q`
Expected: 140 passed

- [ ] **Step 6: Commit**

```bash
git add src/api/routes/admin.py src/main.py src/api/routes/hitl.py src/api/routes/config.py src/api/models/schemas.py
git commit -m "feat: add admin dashboard APIs — stats, recent apps, analytics, doc config"
```

---

## Task 3: Agent Reads Doc Config from DB

**Files:**
- Modify: `src/graph/nodes/doc_collection.py`

- [ ] **Step 1: Replace hardcoded document list with DB query**

Replace the hardcoded `required` list in `doc_collection_node` with a DB query that reads from `product_rules` table where `rule_name == "document_requirements"`. Keep the existing hardcoded list as fallback if no DB rule found.

Also filter documents by the applicant's `employment_type` from state — include "all" group docs always, plus the matching employment group.

- [ ] **Step 2: Run tests**

Run: `.venv/bin/python -m pytest tests/test_graph/ -x -q`
Expected: all graph tests pass

- [ ] **Step 3: Commit**

```bash
git add src/graph/nodes/doc_collection.py
git commit -m "feat: agent reads document requirements from DB config"
```

---

## Task 4: Frontend Setup — Fonts, Dependencies, Layout, CSS

**Files:**
- Modify: `frontend/package.json` (add recharts)
- Create: `frontend/src/components/officer/officer.css`
- Modify: `frontend/src/app/dashboard/layout.tsx`
- Delete: `frontend/src/app/dashboard/[id]/page.tsx`
- Delete: `frontend/src/components/dashboard/review-queue.tsx`
- Delete: `frontend/src/components/dashboard/action-bar.tsx`

- [ ] **Step 1: Install recharts**

Run: `cd frontend && npm install recharts`

- [ ] **Step 2: Create officer.css with all CSS variables and animations**

Create `frontend/src/components/officer/officer.css` containing all the design system CSS variables, animation keyframes (`slideDown`, `fadeUp`, `barGrow`, `ringFill`, `nodeIn`, `pulse`, `shimmer`), grain overlay, card styles, and hover transitions. Copy exact values from the mockup HTML `<style>` block, adapted for the React component structure.

- [ ] **Step 3: Rewrite dashboard layout.tsx with Google Fonts**

Replace `frontend/src/app/dashboard/layout.tsx` to load DM Serif Display, DM Sans, JetBrains Mono via `next/font/google`. Set warm parchment background (`#E8E2D6`). Import `officer.css`. Keep auth check and redirect.

- [ ] **Step 4: Delete old files**

```bash
rm frontend/src/app/dashboard/\[id\]/page.tsx
rm frontend/src/components/dashboard/review-queue.tsx
rm frontend/src/components/dashboard/action-bar.tsx
rmdir frontend/src/app/dashboard/\[id\]
rmdir frontend/src/components/dashboard
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: dashboard layout with Google Fonts, CSS design system, cleanup old files"
```

---

## Task 5: Officer Topbar + Dashboard Page Shell

**Files:**
- Create: `frontend/src/components/officer/officer-topbar.tsx`
- Rewrite: `frontend/src/app/dashboard/page.tsx`

- [ ] **Step 1: Build OfficerTopbar component**

Create `officer-topbar.tsx` with:
- Logo (navy square + landmark icon + "LoanAI" text)
- 4-tab pill navigation with icons, active state (navy bg), and `onTabChange` callback
- Review tab badge with `pendingCount` prop (red pulsing circle)
- Right side: live clock (useEffect + setInterval), settings gear button, bell with red dot, avatar with initials from session user name
- `slideDown` animation on mount

- [ ] **Step 2: Build dashboard page.tsx as SPA shell**

Rewrite `frontend/src/app/dashboard/page.tsx` as `"use client"` component with:
- `activeTab` state (dashboard | review | settings | analytics)
- Fetch stats on mount for topbar badge count
- Render `OfficerTopbar` + tab content wrapper with `key={activeTab}` for animation re-trigger
- Empty `<div className="content">Tab name here</div>` for each tab (Tasks 6-10 replace these with real components)

- [ ] **Step 3: Verify it renders in browser**

Run: `cd frontend && npm run dev`
Navigate to `http://localhost:3000/dashboard` — should show topbar with 4 tabs, clicking tabs switches content area.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/officer/officer-topbar.tsx frontend/src/app/dashboard/page.tsx
git commit -m "feat: officer topbar with tab navigation and dashboard page shell"
```

---

## Task 6: Dashboard Tab — KPI Cards

**Files:**
- Create: `frontend/src/components/officer/dashboard-tab.tsx`

- [ ] **Step 1: Build DashboardTab component**

Create `dashboard-tab.tsx` with:
- Fetch `GET /api/v1/admin/stats` on mount
- 12-column CSS grid layout
- **Row 1:** Total Applications card (span 4), Decision Breakdown bar chart (span 5), AI Confidence donut (span 3, gold gradient)
- **Row 2:** Avg Processing navy card (span 3), Pending Reviews alert card (span 3), Recent Applications list (span 6)
- **Row 3:** Agent Pipeline visualization (span 12)
- All cards with staggered `fadeUp` animation via CSS `animation-delay`
- `onSwitchTab` prop for "View All" and "Review Now" buttons

Implement inline:
- `StatBarChart`: 4 vertical bars with gradient fills, `barGrow` animation
- `DonutChart`: SVG with animated `ringFill`, shimmer overlay
- `RecentAppsList`: 4 rows with avatar, name, ref, amount (₹ lakh format), status badge
- `PipelineViz`: 8 nodes with icons, latency, success rate, arrow separators, `nodeIn` animation

Indian currency formatter: `new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })`

- [ ] **Step 2: Wire into dashboard page.tsx**

Import `DashboardTab` and render when `activeTab === "dashboard"`.

- [ ] **Step 3: Verify in browser**

Expected: Full KPI dashboard matching the mockup with animations, real data from seeded DB.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/officer/dashboard-tab.tsx frontend/src/app/dashboard/page.tsx
git commit -m "feat: dashboard tab with KPI cards, charts, pipeline visualization"
```

---

## Task 7: Review Queue Tab

**Files:**
- Create: `frontend/src/components/officer/review-tab.tsx`

- [ ] **Step 1: Build ReviewTab component**

Create `review-tab.tsx` with:
- Header: "Review Queue" + subtitle
- Fetch `GET /api/v1/hitl/queue` on mount
- Premium table matching mockup: Applicant (avatar+name), Reference (mono), Amount (serif), AI Score (mono), Risk Flags (colored badges), Waiting (mono, amber if >2h), Review button
- Inline detail panel: when "Review" is clicked, expand below the row showing:
  - Fetch `GET /api/v1/hitl/{id}` for full details
  - Application card + AI Recommendation card (2-column grid)
  - Agent Outputs (collapsible)
  - Action bar: Approve (green) / Deny (red) / Conditional (blue) buttons + notes textarea
  - Submit calls `POST /api/v1/hitl/{id}/review`, then refreshes queue

- [ ] **Step 2: Wire into dashboard page.tsx**

Import `ReviewTab` and render when `activeTab === "review"`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/officer/review-tab.tsx frontend/src/app/dashboard/page.tsx
git commit -m "feat: review queue tab with premium table and inline detail/action"
```

---

## Task 8: Settings Tab — Document Rules

**Files:**
- Create: `frontend/src/components/officer/settings-tab.tsx`
- Create: `frontend/src/components/officer/doc-rules-panel.tsx`

- [ ] **Step 1: Build SettingsTab container**

Create `settings-tab.tsx` with:
- Header: "Settings" + subtitle
- Level 1 tabs (pill style): Document Rules | Rate Cards | Product Rules | Agents
- Active sub-tab state, renders matching panel component

- [ ] **Step 2: Build DocRulesPanel**

Create `doc-rules-panel.tsx` with:
- Level 2 tabs: Personal Loan | Home Loan | Auto Loan | Business
- Fetch `GET /api/v1/config/document-requirements?loan_type={selected}`
- 3-column grid (span 4 each): All Applicants / Salaried / Self-Employed
- Each document row: name, description, tier badge (MANDATORY red / RECOMMENDED amber / OPTIONAL green), toggle switch
- Toggle switches: 38×22px, animated, green ON / grey OFF
- Footer bar: navy background, info text + "Save & Update Agent" gold button
- Save: POST config, show success toast

- [ ] **Step 3: Wire into dashboard page.tsx**

Import `SettingsTab` and render when `activeTab === "settings"`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/officer/settings-tab.tsx frontend/src/components/officer/doc-rules-panel.tsx frontend/src/app/dashboard/page.tsx
git commit -m "feat: settings tab with document rules editor"
```

---

## Task 9: Settings Tab — Rate Cards, Product Rules, Agents Panels

**Files:**
- Create: `frontend/src/components/officer/rate-cards-panel.tsx`
- Create: `frontend/src/components/officer/product-rules-panel.tsx`
- Create: `frontend/src/components/officer/agents-panel.tsx`

- [ ] **Step 1: Build RateCardsPanel**

Create `rate-cards-panel.tsx` with:
- Fetch `GET /api/v1/config/rate-cards`
- Table: Risk Category, Score Range, Interest Rate, Processing Fee %, Insurance %, Edit button
- Inline edit mode: fields become inputs, save calls `PUT /api/v1/config/rate-cards/{id}`

- [ ] **Step 2: Build ProductRulesPanel**

Create `product-rules-panel.tsx` with:
- Fetch `GET /api/v1/config/product-rules`
- Group by loan type, show editable fields: Min Age, Max Age, Min Income, Max Multiplier
- Save calls `PUT /api/v1/config/product-rules/{id}`

- [ ] **Step 3: Build AgentsPanel**

Create `agents-panel.tsx` with:
- Hardcoded list of 13 agent nodes with icons, names, descriptions
- Each row: icon, name, description, avg latency, success rate, enabled/disabled toggle
- Toggle is visual only (does not affect graph)

- [ ] **Step 4: Wire all three into SettingsTab**

Import and render based on active sub-tab.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/officer/rate-cards-panel.tsx frontend/src/components/officer/product-rules-panel.tsx frontend/src/components/officer/agents-panel.tsx frontend/src/components/officer/settings-tab.tsx
git commit -m "feat: rate cards, product rules, and agents settings panels"
```

---

## Task 10: Analytics Tab

**Files:**
- Create: `frontend/src/components/officer/analytics-tab.tsx`

- [ ] **Step 1: Build AnalyticsTab component**

Create `analytics-tab.tsx` with:
- Header: "Analytics" + subtitle
- Row 1 (2 cards, span 6 each, 260px height):
  - Approval Trends: `recharts` `BarChart` with stacked bars (approved green, denied red, escalated amber, conditional blue). Fetch `GET /api/v1/admin/analytics/trends?weeks=8`.
  - Risk Distribution: `recharts` horizontal `BarChart` with 4 buckets color-coded by risk category. Fetch `GET /api/v1/admin/analytics/risk-distribution`.
- Row 2 (span 12):
  - Decision Audit Trail table: Date, Applicant, AI Decision, Officer Decision, Override? (amber highlight), Confidence, Notes. Fetch `GET /api/v1/admin/analytics/audit-trail?limit=20`.

- [ ] **Step 2: Wire into dashboard page.tsx**

Import `AnalyticsTab` and render when `activeTab === "analytics"`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/officer/analytics-tab.tsx frontend/src/app/dashboard/page.tsx
git commit -m "feat: analytics tab with recharts and audit trail"
```

---

## Task 11: Customer-Side HITL Decision Banner

**Files:**
- Modify: `frontend/src/components/status/application-detail.tsx`

- [ ] **Step 1: Add decision banner to status detail page**

In `application-detail.tsx`, after fetching the application data, check if `status === "decided"`. If so, render a banner at the top:
- Approved: green background, check-circle icon, "Your loan has been approved!"
- Denied: red background, x-circle icon, "Your application was not approved"
- Conditional: blue background, info icon, "Your loan is conditionally approved"
- Include "View Chat" link to `/chat/{conversation_id}`

Fetch the decision from the existing status API response.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/status/application-detail.tsx
git commit -m "feat: customer status page shows HITL decision banner"
```

---

## Task 12: Integration Testing + Final Polish

**Files:**
- Modify: various (bug fixes found during testing)

- [ ] **Step 1: Run backend tests**

Run: `.venv/bin/python -m pytest tests/ -x -q`
Expected: all pass

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && npm run build`
Expected: no TypeScript errors, no build failures

- [ ] **Step 3: Manual browser walkthrough**

With Docker running (`docker compose up`):
1. Sign in as officer → `/dashboard` loads with KPIs from seeded data
2. Click each tab — Dashboard, Review, Settings, Analytics — animations work
3. Settings > Document Rules: toggle a doc, save, verify API call succeeds
4. Settings > Rate Cards: edit a rate, save
5. Review tab: click Review on escalated app, approve, verify queue updates
6. Sign in as customer → `/status` shows decision banner for reviewed app
7. `/chat` shows injected decision message

- [ ] **Step 4: Push and create PR**

```bash
git push origin feature/admin-dashboard
gh pr create --title "feat: Officer Command Center — full admin dashboard" --body "..."
```
