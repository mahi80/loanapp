from __future__ import annotations

"""
Demo seed script for bank CTO demo.

Run with:
    python -m src.db.seed

Idempotent — skips if already seeded (checks for demo_customer_001 user).
"""

import asyncio
import uuid
from datetime import datetime, timedelta, date, timezone

from sqlalchemy import select, text

from src.db.models import (
    Base,
    User, UserRole,
    Application, ApplicationStatus, LoanType, EmploymentType,
    ApplicantProfile,
    CreditScore, RiskCategory,
    CreditDecision, DecisionEnum,
    HITLReview,
    RateCard,
    ProductRule, RuleType,
)
from src.db.session import engine, async_session_factory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now(offset_days: int = 0) -> datetime:
    """Return a timezone-aware UTC datetime shifted by offset_days."""
    return datetime.now(timezone.utc) - timedelta(days=offset_days)


def _derive_risk_flags(score: int, dti: float, amount: float) -> list[str]:
    flags: list[str] = []
    if dti > 0.50:
        flags.append("Borderline DTI")
    if score < 600:
        flags.append("Low score")
    if amount > 1_000_000:  # > 10 lakhs
        flags.append("High amt")
    return flags


# ---------------------------------------------------------------------------
# Rate-card data
# ---------------------------------------------------------------------------

RATE_CARDS: list[dict] = [
    # Personal
    {"product_type": LoanType.PERSONAL, "risk_category": RiskCategory.LOW,       "min_score": 700, "max_score": 900, "interest_rate": 10.5, "processing_fee_pct": 1.5, "insurance_pct": 0.5},
    {"product_type": LoanType.PERSONAL, "risk_category": RiskCategory.MEDIUM,    "min_score": 600, "max_score": 699, "interest_rate": 13.0, "processing_fee_pct": 2.0, "insurance_pct": 0.75},
    {"product_type": LoanType.PERSONAL, "risk_category": RiskCategory.HIGH,      "min_score": 450, "max_score": 599, "interest_rate": 16.5, "processing_fee_pct": 2.5, "insurance_pct": 1.0},
    {"product_type": LoanType.PERSONAL, "risk_category": RiskCategory.VERY_HIGH, "min_score": 300, "max_score": 449, "interest_rate": 0.0,  "processing_fee_pct": 0.0, "insurance_pct": 0.0},
    # Home
    {"product_type": LoanType.HOME, "risk_category": RiskCategory.LOW,       "min_score": 700, "max_score": 900, "interest_rate": 8.5,  "processing_fee_pct": 0.5,  "insurance_pct": 0.25},
    {"product_type": LoanType.HOME, "risk_category": RiskCategory.MEDIUM,    "min_score": 600, "max_score": 699, "interest_rate": 9.5,  "processing_fee_pct": 0.75, "insurance_pct": 0.4},
    {"product_type": LoanType.HOME, "risk_category": RiskCategory.HIGH,      "min_score": 450, "max_score": 599, "interest_rate": 11.0, "processing_fee_pct": 1.0,  "insurance_pct": 0.5},
    {"product_type": LoanType.HOME, "risk_category": RiskCategory.VERY_HIGH, "min_score": 300, "max_score": 449, "interest_rate": 0.0,  "processing_fee_pct": 0.0,  "insurance_pct": 0.0},
    # Auto
    {"product_type": LoanType.AUTO, "risk_category": RiskCategory.LOW,       "min_score": 700, "max_score": 900, "interest_rate": 9.0,  "processing_fee_pct": 1.0, "insurance_pct": 0.5},
    {"product_type": LoanType.AUTO, "risk_category": RiskCategory.MEDIUM,    "min_score": 600, "max_score": 699, "interest_rate": 11.5, "processing_fee_pct": 1.5, "insurance_pct": 0.6},
    {"product_type": LoanType.AUTO, "risk_category": RiskCategory.HIGH,      "min_score": 450, "max_score": 599, "interest_rate": 14.0, "processing_fee_pct": 2.0, "insurance_pct": 0.8},
    {"product_type": LoanType.AUTO, "risk_category": RiskCategory.VERY_HIGH, "min_score": 300, "max_score": 449, "interest_rate": 0.0,  "processing_fee_pct": 0.0, "insurance_pct": 0.0},
    # Business
    {"product_type": LoanType.BUSINESS, "risk_category": RiskCategory.LOW,       "min_score": 700, "max_score": 900, "interest_rate": 12.0, "processing_fee_pct": 2.0, "insurance_pct": 0.5},
    {"product_type": LoanType.BUSINESS, "risk_category": RiskCategory.MEDIUM,    "min_score": 600, "max_score": 699, "interest_rate": 14.5, "processing_fee_pct": 2.5, "insurance_pct": 0.75},
    {"product_type": LoanType.BUSINESS, "risk_category": RiskCategory.HIGH,      "min_score": 450, "max_score": 599, "interest_rate": 17.5, "processing_fee_pct": 3.0, "insurance_pct": 1.0},
    {"product_type": LoanType.BUSINESS, "risk_category": RiskCategory.VERY_HIGH, "min_score": 300, "max_score": 449, "interest_rate": 0.0,  "processing_fee_pct": 0.0, "insurance_pct": 0.0},
]

# ---------------------------------------------------------------------------
# Product eligibility rules (12 rows: 3 per loan type)
# ---------------------------------------------------------------------------

PRODUCT_RULES: list[dict] = [
    # Personal
    {"product_type": LoanType.PERSONAL, "rule_name": "min_age",         "rule_type": RuleType.ELIGIBILITY, "rule_config": {"min_age": 21, "max_age": 58}},
    {"product_type": LoanType.PERSONAL, "rule_name": "min_income",      "rule_type": RuleType.ELIGIBILITY, "rule_config": {"min_monthly_income": 15000}},
    {"product_type": LoanType.PERSONAL, "rule_name": "max_multiplier",  "rule_type": RuleType.LIMIT,       "rule_config": {"max_multiplier": 60}},
    # Home
    {"product_type": LoanType.HOME, "rule_name": "min_age",        "rule_type": RuleType.ELIGIBILITY, "rule_config": {"min_age": 23, "max_age": 60}},
    {"product_type": LoanType.HOME, "rule_name": "min_income",     "rule_type": RuleType.ELIGIBILITY, "rule_config": {"min_monthly_income": 25000}},
    {"product_type": LoanType.HOME, "rule_name": "max_multiplier", "rule_type": RuleType.LIMIT,       "rule_config": {"max_multiplier": 200}},
    # Auto
    {"product_type": LoanType.AUTO, "rule_name": "min_age",        "rule_type": RuleType.ELIGIBILITY, "rule_config": {"min_age": 21, "max_age": 60}},
    {"product_type": LoanType.AUTO, "rule_name": "min_income",     "rule_type": RuleType.ELIGIBILITY, "rule_config": {"min_monthly_income": 20000}},
    {"product_type": LoanType.AUTO, "rule_name": "max_multiplier", "rule_type": RuleType.LIMIT,       "rule_config": {"max_multiplier": 48}},
    # Business
    {"product_type": LoanType.BUSINESS, "rule_name": "min_age",        "rule_type": RuleType.ELIGIBILITY, "rule_config": {"min_age": 25, "max_age": 65}},
    {"product_type": LoanType.BUSINESS, "rule_name": "min_income",     "rule_type": RuleType.ELIGIBILITY, "rule_config": {"min_monthly_income": 30000}},
    {"product_type": LoanType.BUSINESS, "rule_name": "max_multiplier", "rule_type": RuleType.LIMIT,       "rule_config": {"max_multiplier": 100}},
]

# ---------------------------------------------------------------------------
# Document requirement configs
# ---------------------------------------------------------------------------

def _doc(name: str, key: str, description: str, tier: str, enabled: bool) -> dict:
    return {"name": name, "key": key, "description": description, "tier": tier, "enabled": enabled}


PERSONAL_DOC_CONFIG = {
    "groups": [
        {
            "group": "all",
            "label": "All Applicants",
            "icon": "user",
            "description": "Required for all personal loan applicants",
            "documents": [
                _doc("PAN Card",         "pan_card",       "Permanent Account Number card",          "mandatory",    True),
                _doc("Aadhaar Card",     "aadhaar",        "Aadhaar 12-digit UID card",               "mandatory",    True),
                _doc("Selfie",           "selfie",         "Live selfie for face-match",              "mandatory",    True),
                _doc("Bank Statement",   "bank_statement", "Last 6 months bank statement",           "mandatory",    True),
                _doc("Address Proof",    "address_proof",  "Utility bill / rent agreement",          "optional",     True),
            ],
        },
        {
            "group": "salaried",
            "label": "Salaried Employees",
            "icon": "briefcase",
            "description": "Additional documents for salaried applicants",
            "documents": [
                _doc("Latest Payslip",         "payslip",              "Last 3 months salary slips",         "mandatory",    True),
                _doc("Form 16",                "form_16",              "Annual tax form from employer",       "recommended",  True),
                _doc("Employment Letter",      "employment_letter",    "Employer confirmation letter",        "recommended",  True),
                _doc("Salary Certificate",     "salary_certificate",   "Certified salary certificate",       "optional",     False),
            ],
        },
        {
            "group": "self_employed",
            "label": "Self-Employed / Business Owners",
            "icon": "building",
            "description": "Additional documents for self-employed applicants",
            "documents": [
                _doc("ITR (2 years)",          "itr",                  "Income Tax Returns last 2 years",    "mandatory",    True),
                _doc("GST Certificate",        "gst_certificate",      "GST registration certificate",       "recommended",  True),
                _doc("Business Registration",  "business_registration","Shop/firm registration doc",         "recommended",  True),
                _doc("P&L Statement",          "pl_statement",         "Profit & Loss statement",            "optional",     False),
                _doc("Balance Sheet",          "balance_sheet",        "Latest audited balance sheet",       "optional",     False),
            ],
        },
    ]
}

HOME_DOC_CONFIG = {
    "groups": [
        {
            "group": "all",
            "label": "All Applicants",
            "icon": "user",
            "description": "Required for all home loan applicants",
            "documents": [
                _doc("PAN Card",         "pan_card",       "Permanent Account Number card",          "mandatory",    True),
                _doc("Aadhaar Card",     "aadhaar",        "Aadhaar 12-digit UID card",               "mandatory",    True),
                _doc("Selfie",           "selfie",         "Live selfie for face-match",              "mandatory",    True),
                _doc("Bank Statement",   "bank_statement", "Last 12 months bank statement",          "mandatory",    True),
                _doc("Property Documents","property_docs", "Title deed / property card",             "mandatory",    True),
                _doc("Sale Agreement",   "sale_agreement", "Draft sale / purchase agreement",        "mandatory",    True),
                _doc("Address Proof",    "address_proof",  "Utility bill / rent agreement",          "optional",     True),
            ],
        },
        {
            "group": "salaried",
            "label": "Salaried Employees",
            "icon": "briefcase",
            "description": "Additional documents for salaried applicants",
            "documents": [
                _doc("Latest Payslip",         "payslip",              "Last 3 months salary slips",         "mandatory",    True),
                _doc("Form 16",                "form_16",              "Annual tax form from employer",       "mandatory",    True),
                _doc("Employment Letter",      "employment_letter",    "Employer confirmation letter",        "recommended",  True),
                _doc("Salary Certificate",     "salary_certificate",   "Certified salary certificate",       "optional",     False),
            ],
        },
        {
            "group": "self_employed",
            "label": "Self-Employed / Business Owners",
            "icon": "building",
            "description": "Additional documents for self-employed applicants",
            "documents": [
                _doc("ITR (3 years)",          "itr",                  "Income Tax Returns last 3 years",    "mandatory",    True),
                _doc("GST Certificate",        "gst_certificate",      "GST registration certificate",       "mandatory",    True),
                _doc("Business Registration",  "business_registration","Shop/firm registration doc",         "recommended",  True),
                _doc("P&L Statement",          "pl_statement",         "Profit & Loss statement",            "recommended",  True),
                _doc("Balance Sheet",          "balance_sheet",        "Latest audited balance sheet",       "optional",     False),
            ],
        },
    ]
}

AUTO_DOC_CONFIG = {
    "groups": [
        {
            "group": "all",
            "label": "All Applicants",
            "icon": "user",
            "description": "Required for all auto loan applicants",
            "documents": [
                _doc("PAN Card",          "pan_card",          "Permanent Account Number card",       "mandatory",    True),
                _doc("Aadhaar Card",      "aadhaar",           "Aadhaar 12-digit UID card",            "mandatory",    True),
                _doc("Selfie",            "selfie",            "Live selfie for face-match",           "mandatory",    True),
                _doc("Bank Statement",    "bank_statement",    "Last 6 months bank statement",        "mandatory",    True),
                _doc("Vehicle Quotation", "vehicle_quotation", "Dealer quotation / pro-forma invoice", "mandatory",    True),
                _doc("Address Proof",     "address_proof",     "Utility bill / rent agreement",       "optional",     True),
            ],
        },
        {
            "group": "salaried",
            "label": "Salaried Employees",
            "icon": "briefcase",
            "description": "Additional documents for salaried applicants",
            "documents": [
                _doc("Latest Payslip",     "payslip",           "Last 3 months salary slips",         "mandatory",    True),
                _doc("Form 16",            "form_16",           "Annual tax form from employer",       "recommended",  True),
                _doc("Employment Letter",  "employment_letter", "Employer confirmation letter",        "optional",     True),
            ],
        },
        {
            "group": "self_employed",
            "label": "Self-Employed / Business Owners",
            "icon": "building",
            "description": "Additional documents for self-employed applicants",
            "documents": [
                _doc("ITR (2 years)",         "itr",                  "Income Tax Returns last 2 years", "mandatory",    True),
                _doc("GST Certificate",       "gst_certificate",      "GST registration certificate",    "recommended",  True),
                _doc("Business Registration", "business_registration","Shop/firm registration doc",       "optional",     True),
                _doc("P&L Statement",         "pl_statement",         "Profit & Loss statement",          "optional",     False),
            ],
        },
    ]
}

BUSINESS_DOC_CONFIG = {
    "groups": [
        {
            "group": "all",
            "label": "All Applicants",
            "icon": "user",
            "description": "Required for all business loan applicants",
            "documents": [
                _doc("PAN Card",           "pan_card",          "Permanent Account Number card",      "mandatory",    True),
                _doc("Aadhaar Card",       "aadhaar",           "Aadhaar 12-digit UID card",           "mandatory",    True),
                _doc("Selfie",             "selfie",            "Live selfie for face-match",          "mandatory",    True),
                _doc("Bank Statement",     "bank_statement",    "Last 12 months business bank stmt",  "mandatory",    True),
                _doc("Business PAN",       "business_pan",      "Entity / firm PAN card",             "mandatory",    True),
                _doc("Address Proof",      "address_proof",     "Registered office address proof",    "mandatory",    True),
            ],
        },
        {
            "group": "salaried",
            "label": "Directors / Salaried Partners",
            "icon": "briefcase",
            "description": "Additional documents for directors and salaried partners",
            "documents": [
                _doc("Latest Payslip",     "payslip",           "Last 3 months salary slips",         "mandatory",    True),
                _doc("Form 16",            "form_16",           "Annual tax form",                    "recommended",  True),
            ],
        },
        {
            "group": "self_employed",
            "label": "Self-Employed / Proprietors",
            "icon": "building",
            "description": "Additional documents for self-employed and proprietors",
            "documents": [
                _doc("ITR (3 years)",          "itr",                  "Income Tax Returns last 3 years", "mandatory",    True),
                _doc("GST Certificate",        "gst_certificate",      "GST registration certificate",    "mandatory",    True),
                _doc("Business Registration",  "business_registration","Company / firm registration doc",  "mandatory",    True),
                _doc("P&L Statement",          "pl_statement",         "Audited P&L statement",            "mandatory",    True),
                _doc("Balance Sheet",          "balance_sheet",        "Latest audited balance sheet",     "mandatory",    True),
                _doc("MoA / AoA",             "moa_aoa",              "Memorandum / Articles of Assoc",   "recommended",  True),
                _doc("Partnership Deed",       "partnership_deed",     "Partnership deed (if applicable)", "optional",     False),
            ],
        },
    ]
}

DOC_REQUIREMENT_RULES: list[dict] = [
    {"product_type": LoanType.PERSONAL, "rule_name": "document_requirements", "rule_type": RuleType.POLICY, "rule_config": PERSONAL_DOC_CONFIG},
    {"product_type": LoanType.HOME,     "rule_name": "document_requirements", "rule_type": RuleType.POLICY, "rule_config": HOME_DOC_CONFIG},
    {"product_type": LoanType.AUTO,     "rule_name": "document_requirements", "rule_type": RuleType.POLICY, "rule_config": AUTO_DOC_CONFIG},
    {"product_type": LoanType.BUSINESS, "rule_name": "document_requirements", "rule_type": RuleType.POLICY, "rule_config": BUSINESS_DOC_CONFIG},
]

# ---------------------------------------------------------------------------
# Application data
# Format per entry:
#   (name, pan, mobile, amount, loan_type, emp_type, status, tenure, hours_ago,
#    income, employer, city,
#    score, dti, risk,  # None if no CreditScore
#    decision, dec_confidence, rationale)  # None if no decision
# ---------------------------------------------------------------------------

APPLICATIONS = [
    # ------------------------------------------------------------------ APPROVED (5)
    {
        "name": "Arjun Mehta",
        "pan": "ABCPM1234A",
        "mobile": "9812345601",
        "amount": 500_000,
        "loan_type": LoanType.PERSONAL,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 36,
        "days_ago": 2,
        "income": 75_000,
        "employer": "Infosys Ltd",
        "city": "Bengaluru",
        "score": 782,
        "dti": 0.31,
        "risk": RiskCategory.LOW,
        "decision": DecisionEnum.APPROVED,
        "dec_confidence": 0.94,
        "rationale": "Strong credit profile with stable employment at Infosys. Low DTI and high score well within approval band.",
    },
    {
        "name": "Vikram Nair",
        "pan": "BCDVN2345B",
        "mobile": "9823456702",
        "amount": 1_500_000,
        "loan_type": LoanType.HOME,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 240,
        "days_ago": 8,
        "income": 120_000,
        "employer": "Tata Consultancy Services",
        "city": "Mumbai",
        "score": 810,
        "dti": 0.35,
        "risk": RiskCategory.LOW,
        "decision": DecisionEnum.APPROVED,
        "dec_confidence": 0.96,
        "rationale": "Excellent CIBIL score. Income comfortably supports EMI. Property documentation complete and verified.",
    },
    {
        "name": "Sunita Krishnamurthy",
        "pan": "CDPSK3456C",
        "mobile": "9834567803",
        "amount": 800_000,
        "loan_type": LoanType.PERSONAL,
        "emp_type": EmploymentType.SELF_EMPLOYED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 48,
        "days_ago": 15,
        "income": 95_000,
        "employer": "SK Enterprises (Proprietorship)",
        "city": "Hyderabad",
        "score": 745,
        "dti": 0.28,
        "risk": RiskCategory.LOW,
        "decision": DecisionEnum.APPROVED,
        "dec_confidence": 0.91,
        "rationale": "Self-employed with 7 years business vintage. ITR shows steady income growth. Low DTI and good bureau score.",
    },
    {
        "name": "Rahul Gupta",
        "pan": "DEPGR4567D",
        "mobile": "9845678904",
        "amount": 600_000,
        "loan_type": LoanType.AUTO,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 60,
        "days_ago": 22,
        "income": 65_000,
        "employer": "HDFC Bank",
        "city": "Delhi",
        "score": 769,
        "dti": 0.38,
        "risk": RiskCategory.LOW,
        "decision": DecisionEnum.APPROVED,
        "dec_confidence": 0.92,
        "rationale": "Bank employee with confirmed salary. Auto loan within eligible limits. Clean bureau record.",
    },
    {
        "name": "Meera Iyer",
        "pan": "EFQMI5678E",
        "mobile": "9856789005",
        "amount": 3_000_000,
        "loan_type": LoanType.BUSINESS,
        "emp_type": EmploymentType.SELF_EMPLOYED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 84,
        "days_ago": 28,
        "income": 250_000,
        "employer": "Iyer Tech Solutions Pvt Ltd",
        "city": "Chennai",
        "score": 835,
        "dti": 0.42,
        "risk": RiskCategory.LOW,
        "decision": DecisionEnum.APPROVED,
        "dec_confidence": 0.97,
        "rationale": "High income, premium CIBIL score. Business financials audited and verified. Strong collateral position.",
    },
    # ------------------------------------------------------------------ DENIED (2)
    {
        "name": "Suresh Patel",
        "pan": "FGRSP6789F",
        "mobile": "9867890106",
        "amount": 300_000,
        "loan_type": LoanType.PERSONAL,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 24,
        "days_ago": 35,
        "income": 22_000,
        "employer": "Daily Needs Retail",
        "city": "Ahmedabad",
        "score": 395,
        "dti": 0.71,
        "risk": RiskCategory.VERY_HIGH,
        "decision": DecisionEnum.DENIED,
        "dec_confidence": 0.97,
        "rationale": "Very low credit score (395). Multiple loan defaults in bureau history. DTI at 71% far exceeds policy limit of 55%.",
    },
    {
        "name": "Kavya Reddy",
        "pan": "GHSKR7890G",
        "mobile": "9878901207",
        "amount": 450_000,
        "loan_type": LoanType.PERSONAL,
        "emp_type": EmploymentType.SELF_EMPLOYED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 36,
        "days_ago": 38,
        "income": 18_000,
        "employer": "Freelance Consultant",
        "city": "Pune",
        "score": 408,
        "dti": 0.69,
        "risk": RiskCategory.VERY_HIGH,
        "decision": DecisionEnum.DENIED,
        "dec_confidence": 0.95,
        "rationale": "Score below minimum threshold (408 vs 450 cutoff). Income irregular with high DTI. Insufficient ITR compliance.",
    },
    # ------------------------------------------------------------------ CONDITIONAL (1)
    {
        "name": "Anand Sharma",
        "pan": "HITAS8901H",
        "mobile": "9889012308",
        "amount": 700_000,
        "loan_type": LoanType.HOME,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 180,
        "days_ago": 42,
        "income": 55_000,
        "employer": "State Bank of India",
        "city": "Jaipur",
        "score": 660,
        "dti": 0.46,
        "risk": RiskCategory.MEDIUM,
        "decision": DecisionEnum.CONDITIONAL,
        "dec_confidence": 0.76,
        "rationale": "Score in medium band. Approval conditional on submission of NOC from existing lender and co-applicant income proof.",
    },
    # ------------------------------------------------------------------ ESCALATED (3) — appear in review queue
    {
        "name": "Priya Sharma",
        "pan": "IJUPS9012I",
        "mobile": "9890123409",
        "amount": 1_200_000,
        "loan_type": LoanType.HOME,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 120,
        "days_ago": 5,
        "income": 85_000,
        "employer": "Wipro Technologies",
        "city": "Bengaluru",
        "score": 615,
        "dti": 0.52,
        "risk": RiskCategory.MEDIUM,
        "decision": DecisionEnum.ESCALATED,
        "dec_confidence": 0.62,
        "rationale": "Score borderline (615). Loan amount > 10L triggers manual review. DTI slightly elevated at 52%. Escalated for officer assessment.",
    },
    {
        "name": "Ravi Kumar",
        "pan": "JKQRK0123J",
        "mobile": "9801234510",
        "amount": 400_000,
        "loan_type": LoanType.PERSONAL,
        "emp_type": EmploymentType.SELF_EMPLOYED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 24,
        "days_ago": 10,
        "income": 32_000,
        "employer": "Kumar General Stores",
        "city": "Lucknow",
        "score": 582,
        "dti": 0.55,
        "risk": RiskCategory.HIGH,
        "decision": DecisionEnum.ESCALATED,
        "dec_confidence": 0.58,
        "rationale": "Self-employed with inconsistent ITR. Score at 582 in high-risk band. Borderline DTI at 55%. Requires officer review.",
    },
    {
        "name": "Deepa Menon",
        "pan": "KLRSM1234K",
        "mobile": "9812345611",
        "amount": 550_000,
        "loan_type": LoanType.AUTO,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.DECIDED,
        "tenure": 48,
        "days_ago": 18,
        "income": 45_000,
        "employer": "Reliance Industries",
        "city": "Mumbai",
        "score": 644,
        "dti": 0.48,
        "risk": RiskCategory.MEDIUM,
        "decision": DecisionEnum.ESCALATED,
        "dec_confidence": 0.65,
        "rationale": "Score in medium band with 2 credit enquiries in last 6 months. DTI at 48%. Escalated for enhanced due diligence.",
    },
    # ------------------------------------------------------------------ PROCESSING (4)
    {
        "name": "Aditya Singh",
        "pan": "LMTAS2345L",
        "mobile": "9823456712",
        "amount": 250_000,
        "loan_type": LoanType.PERSONAL,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.PROCESSING,
        "tenure": 24,
        "days_ago": 1,
        "income": 40_000,
        "employer": "Cognizant Technology",
        "city": "Pune",
        "score": None,
        "dti": None,
        "risk": None,
        "decision": None,
        "dec_confidence": None,
        "rationale": None,
    },
    {
        "name": "Nisha Bansal",
        "pan": "MNUBN3456M",
        "mobile": "9834567813",
        "amount": 2_500_000,
        "loan_type": LoanType.HOME,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.PROCESSING,
        "tenure": 300,
        "days_ago": 3,
        "income": 180_000,
        "employer": "Deloitte India",
        "city": "Gurugram",
        "score": None,
        "dti": None,
        "risk": None,
        "decision": None,
        "dec_confidence": None,
        "rationale": None,
    },
    {
        "name": "Sanjay Joshi",
        "pan": "NOVJS4567N",
        "mobile": "9845678914",
        "amount": 350_000,
        "loan_type": LoanType.AUTO,
        "emp_type": EmploymentType.SELF_EMPLOYED,
        "status": ApplicationStatus.PROCESSING,
        "tenure": 36,
        "days_ago": 4,
        "income": 55_000,
        "employer": "Joshi Motors",
        "city": "Indore",
        "score": None,
        "dti": None,
        "risk": None,
        "decision": None,
        "dec_confidence": None,
        "rationale": None,
    },
    {
        "name": "Pooja Verma",
        "pan": "OPWPV5678O",
        "mobile": "9856789015",
        "amount": 5_000_000,
        "loan_type": LoanType.BUSINESS,
        "emp_type": EmploymentType.SELF_EMPLOYED,
        "status": ApplicationStatus.PROCESSING,
        "tenure": 60,
        "days_ago": 6,
        "income": 400_000,
        "employer": "Verma Exports Pvt Ltd",
        "city": "Surat",
        "score": None,
        "dti": None,
        "risk": None,
        "decision": None,
        "dec_confidence": None,
        "rationale": None,
    },
    # ------------------------------------------------------------------ LEADS (3)
    {
        "name": "Kiran Rao",
        "pan": "PQXKR6789P",
        "mobile": "9867890116",
        "amount": 100_000,
        "loan_type": LoanType.PERSONAL,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.LEAD,
        "tenure": 12,
        "days_ago": 0,
        "income": None,
        "employer": None,
        "city": None,
        "score": None,
        "dti": None,
        "risk": None,
        "decision": None,
        "dec_confidence": None,
        "rationale": None,
    },
    {
        "name": "Divya Nambiar",
        "pan": "QRYDN7890Q",
        "mobile": "9878901217",
        "amount": 750_000,
        "loan_type": LoanType.HOME,
        "emp_type": EmploymentType.SALARIED,
        "status": ApplicationStatus.LEAD,
        "tenure": 180,
        "days_ago": 0,
        "income": None,
        "employer": None,
        "city": None,
        "score": None,
        "dti": None,
        "risk": None,
        "decision": None,
        "dec_confidence": None,
        "rationale": None,
    },
    {
        "name": "Mohan Das",
        "pan": "RSZMD8901R",
        "mobile": "9889012318",
        "amount": 200_000,
        "loan_type": LoanType.PERSONAL,
        "emp_type": EmploymentType.SELF_EMPLOYED,
        "status": ApplicationStatus.LEAD,
        "tenure": 18,
        "days_ago": 0,
        "income": None,
        "employer": None,
        "city": None,
        "score": None,
        "dti": None,
        "risk": None,
        "decision": None,
        "dec_confidence": None,
        "rationale": None,
    },
]

# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

async def seed() -> None:
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Idempotency check
        existing = await db.execute(
            select(User).where(User.google_id == "demo_customer_001")
        )
        if existing.scalar_one_or_none():
            print("Seed data already present — skipping.")
            return

        print("Seeding demo data...")

        # ------------------------------------------------------------------ Users
        customer = User(
            google_id="demo_customer_001",
            email="customer@demo.bank",
            name="Demo Customer",
            role=UserRole.CUSTOMER,
        )
        officer = User(
            google_id="demo_officer_001",
            email="officer@demo.bank",
            name="Hemant Rawat",
            role=UserRole.OFFICER,
        )
        db.add_all([customer, officer])
        await db.flush()
        print(f"  Created users: {customer.email}, {officer.email}")

        # ------------------------------------------------------------------ Applications + related records
        app_objects: list[Application] = []
        ref_idx = 1

        for idx, data in enumerate(APPLICATIONS):
            ref_num = f"LN{2024_0001 + ref_idx:08d}"
            ref_idx += 1

            created_at = _now(data["days_ago"])
            app = Application(
                applicant_name=data["name"],
                pan_number=data["pan"],
                mobile=data["mobile"],
                loan_amount=data["amount"],
                loan_type=data["loan_type"],
                tenure_months=data["tenure"],
                employment_type=data["emp_type"],
                status=data["status"],
                user_id=customer.id,
                reference_number=ref_num,
                created_at=created_at,
                updated_at=created_at + timedelta(hours=4),
            )
            db.add(app)
            await db.flush()

            # ApplicantProfile (if we have profile data)
            if data.get("income") or data.get("employer") or data.get("city"):
                profile = ApplicantProfile(
                    application_id=app.id,
                    income=data.get("income"),
                    employer=data.get("employer"),
                    employment_type=data["emp_type"],
                    city=data.get("city"),
                )
                db.add(profile)

            # CreditScore
            if data["score"] is not None:
                four_c = {
                    "character":  round(data["score"] * 0.30),
                    "capacity":   round(data["score"] * 0.25),
                    "capital":    round(data["score"] * 0.25),
                    "collateral": round(data["score"] * 0.20),
                }
                cs = CreditScore(
                    application_id=app.id,
                    composite_score=data["score"],
                    dti_ratio=data["dti"],
                    risk_category=data["risk"],
                    four_c_scores=four_c,
                    stability_score=round(0.95 - data["dti"] * 0.5, 2),
                    confidence=data["dec_confidence"] if data["dec_confidence"] else 0.80,
                )
                db.add(cs)

            # CreditDecision — set decided_at a few hours after created_at for realistic processing time
            if data["decision"] is not None:
                risk_flags = _derive_risk_flags(data["score"], data["dti"], data["amount"])
                processing_hours = 2 + (idx % 5)  # 2-6 hours processing time
                cd = CreditDecision(
                    application_id=app.id,
                    decision=data["decision"],
                    confidence=data["dec_confidence"],
                    rationale=data["rationale"],
                    decided_at=created_at + timedelta(hours=processing_hours),
                    conditions={
                        "risk_flags": risk_flags,
                        "approved_amount": data["amount"] if data["decision"] == DecisionEnum.APPROVED else None,
                        "notes": "Conditional on receipt of additional documents." if data["decision"] == DecisionEnum.CONDITIONAL else None,
                    },
                )
                db.add(cd)

            app_objects.append(app)

        await db.flush()
        print(f"  Created {len(app_objects)} applications with profiles/scores/decisions")

        # ------------------------------------------------------------------ HITL Review (Priya Sharma — first escalated, index 8)
        priya_app = app_objects[8]  # 0-based: indices 0-4 approved, 5-6 denied, 7 conditional, 8 first escalated
        hitl = HITLReview(
            application_id=priya_app.id,
            officer_id=str(officer.id),
            officer_decision=DecisionEnum.APPROVED,
            notes="Reviewed full bureau history. Employment at Wipro verified independently. Property valuation report satisfactory. Recommending approval with standard conditions.",
            override_reason="AI escalated due to borderline DTI (52%) and score (615). Officer assessment confirms ability to repay based on 4-year employment stability and Wipro salary confirmation letter.",
        )
        db.add(hitl)
        print(f"  Created HITL review for {priya_app.applicant_name}")

        # ------------------------------------------------------------------ HITL Review (Ravi Kumar — second escalated, index 9)
        ravi_app = app_objects[9]  # index 9: Ravi Kumar (second escalated)
        hitl2 = HITLReview(
            application_id=ravi_app.id,
            officer_id=str(officer.id),
            officer_decision=DecisionEnum.DENIED,
            notes="High loan amount relative to income, thin credit file",
        )
        db.add(hitl2)
        print(f"  Created HITL review for {ravi_app.applicant_name}")

        # ------------------------------------------------------------------ Rate Cards (16)
        today = date.today()
        for rc_data in RATE_CARDS:
            rc = RateCard(
                product_type=rc_data["product_type"],
                risk_category=rc_data["risk_category"],
                min_score=rc_data["min_score"],
                max_score=rc_data["max_score"],
                interest_rate=rc_data["interest_rate"],
                processing_fee_pct=rc_data["processing_fee_pct"],
                insurance_pct=rc_data["insurance_pct"],
                effective_from=today,
                effective_to=None,
                active=True,
            )
            db.add(rc)
        print(f"  Created {len(RATE_CARDS)} rate card rows")

        # ------------------------------------------------------------------ Product Rules (12 eligibility/limit + 4 doc config = 16)
        all_rules = PRODUCT_RULES + DOC_REQUIREMENT_RULES
        for pr_data in all_rules:
            pr = ProductRule(
                product_type=pr_data["product_type"],
                rule_name=pr_data["rule_name"],
                rule_type=pr_data["rule_type"],
                rule_config=pr_data["rule_config"],
                active=True,
            )
            db.add(pr)
        print(f"  Created {len(PRODUCT_RULES)} eligibility/limit rules + {len(DOC_REQUIREMENT_RULES)} document requirement rules")

        # ------------------------------------------------------------------ Commit
        await db.commit()
        print("Seed complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(seed())
