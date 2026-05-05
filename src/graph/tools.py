"""LangGraph tool definitions - wraps existing internal tools as LangChain @tool functions."""
from __future__ import annotations
from langchain_core.tools import tool
from src.tools.internal.eligibility_rules import check_eligibility
from src.tools.internal.dti_calculator import calculate_dti, estimate_emi
from src.tools.internal.risk_scorer import calculate_risk_score
from src.tools.internal.four_c_scorer import score_four_cs
from src.tools.internal.rate_card_engine import lookup_rate
from src.tools.internal.emi_scheduler import generate_emi_schedule
from src.tools.internal.negative_list import check_negative_list
from src.tools.internal.weighted_aggregator import aggregate_scores
from src.tools.internal.volatility_calculator import calculate_volatility
from src.tools.internal.hidden_debt_scanner import scan_hidden_debts
from src.tools.internal.bias_detector import check_bias


# -- Customer-facing tools (render inline UI) --------------------------------

@tool
def collect_basic_info() -> dict:
    """Render an inline form to collect applicant basic information.
    Call this tool with no arguments when you need to collect: name, PAN, DOB, mobile, email,
    employment type, monthly income, employer, city.
    """
    return {"tool": "collect_basic_info", "action": "render_form"}

@tool
def collect_loan_details() -> dict:
    """Render an inline form to collect loan details (amount, tenure, type).
    Call this tool with no arguments.
    """
    return {"tool": "collect_loan_details", "action": "render_form"}

@tool
def upload_document(document_type: str, label: str) -> dict:
    """Render an inline document upload widget.
    Args:
        document_type: One of pan_card, aadhaar, bank_statement, payslip, form_16, itr, gst_certificate, selfie (applicant photo)
        label: Human-readable label for the upload widget
    """
    return {"tool": "upload_document", "document_type": document_type, "label": label}

@tool
def show_verification(document_type: str, status: str, extracted_data: dict, message: str) -> dict:
    """Show a document verification result card in the chat."""
    return {"tool": "show_verification", "document_type": document_type, "status": status,
            "extracted_data": extracted_data, "message": message}

@tool
def show_progress(step: int, total: int, label: str) -> dict:
    """Show a progress tracker in the chat."""
    return {"tool": "show_progress", "step": step, "total": total, "label": label}

@tool
def show_offer(interest_rate: float, emi_amount: float, tenure_months: int,
               processing_fee: float, total_cost: float, loan_amount: float) -> dict:
    """Show the loan offer card to the customer."""
    return {"tool": "show_offer", "interest_rate": interest_rate, "emi_amount": emi_amount,
            "tenure_months": tenure_months, "processing_fee": processing_fee,
            "total_cost": total_cost, "loan_amount": loan_amount}

@tool
def show_eligibility(eligible: bool, reasons: list[str], details: dict | None = None) -> dict:
    """Show an eligibility check result card to the customer."""
    return {"tool": "show_eligibility", "eligible": eligible, "reasons": reasons, "details": details or {}}

@tool
def show_decision(decision: str, reasons: list[str], confidence: float) -> dict:
    """Show the credit decision card to the customer."""
    return {"tool": "show_decision", "decision": decision, "reasons": reasons, "confidence": confidence}


# -- Backend computation tools -----------------------------------------------

@tool
def check_eligibility_tool(age: int, monthly_income: float, city: str, loan_amount: float) -> dict:
    """Check basic eligibility for a personal loan. Age 21-58, min income 15000, max loan 60x income."""
    return check_eligibility(age, monthly_income, city, loan_amount)

@tool
def calculate_dti_tool(monthly_income: float, existing_emis: float, proposed_emi: float,
                       credit_card_outstanding: float = 0, other_obligations: float = 0) -> dict:
    """Calculate Debt-to-Income ratio."""
    return calculate_dti(monthly_income, existing_emis, proposed_emi, credit_card_outstanding, other_obligations)

@tool
def estimate_emi_tool(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Calculate EMI using standard formula."""
    return estimate_emi(principal, annual_rate, tenure_months)

@tool
def calculate_risk_score_tool(bureau_score: int | None, dti_ratio: float, income_stability: float,
                               employment_type: str, loan_amount: float, existing_obligations: float,
                               enquiry_count: int = 0, delinquency_count: int = 0) -> dict:
    """Calculate composite risk score from multiple factors."""
    return calculate_risk_score(bureau_score, dti_ratio, income_stability, employment_type,
                                loan_amount, existing_obligations, enquiry_count, delinquency_count)

@tool
def score_four_cs_tool(bureau_score: int, repayment_history: float, monthly_income: float,
                       total_obligations: float, assets_value: float, savings_balance: float) -> dict:
    """Evaluate the 4-C credit framework."""
    return score_four_cs(bureau_score, repayment_history, monthly_income, total_obligations,
                         assets_value, savings_balance)

@tool
def lookup_rate_tool(risk_category: str, loan_type: str = "personal", score: int = 0) -> dict:
    """Look up interest rate, processing fee, insurance from rate card."""
    return lookup_rate(risk_category, loan_type, score)

@tool
def generate_emi_schedule_tool(principal: float, annual_rate: float, tenure_months: int,
                                start_date: str | None = None) -> dict:
    """Generate full amortization EMI schedule."""
    return generate_emi_schedule(principal, annual_rate, tenure_months, start_date)

@tool
def check_negative_list_tool(entity_name: str, list_type: str = "individual") -> dict:
    """Check whether entity appears in negative/blacklist."""
    return check_negative_list(entity_name, list_type)

@tool
def aggregate_scores_tool(scores: dict, weights: dict, fraud_flags: list[str] | None = None) -> dict:
    """Produce composite score 300-900 from weighted components."""
    return aggregate_scores(scores, weights, fraud_flags)

@tool
def calculate_volatility_tool(monthly_incomes: list[float]) -> dict:
    """Calculate income volatility from monthly income series."""
    return calculate_volatility(monthly_incomes)

@tool
def scan_hidden_debts_tool(bank_debits: list[dict], bureau_emis: list[dict]) -> dict:
    """Identify recurring EMI-like debits not in bureau report."""
    return scan_hidden_debts(bank_debits, bureau_emis)

@tool
def check_bias_tool(decisions: list[dict], protected_field: str) -> dict:
    """Perform disparate-impact 4/5ths rule check on lending decisions."""
    return check_bias(decisions, protected_field)


@tool
async def extract_document_tool(document_url: str, document_type: str) -> dict:
    """Extract structured data from an uploaded document using Azure Document Intelligence.

    Args:
        document_url: URL of the document (Azure Blob SAS URL)
        document_type: One of pan_card, aadhaar, bank_statement, payslip, form_16, itr, gst_certificate
    """
    from src.tools.internal.ocr_tool import extract_document_data
    return await extract_document_data(document_url, document_type)


@tool
def cross_validate_documents(documents: dict) -> dict:
    """Cross-validate extracted data across multiple documents.

    Checks for name mismatches, DOB inconsistencies, and other discrepancies
    between PAN, Aadhaar, bank statements, and payslips.

    Args:
        documents: Dict mapping document_type to extracted_data
    """
    issues = []
    names = {}
    dobs = {}

    for doc_type, data in documents.items():
        kvp = data.get("key_value_pairs", {})

        # Collect names
        for key in ["Name", "Account Holder", "Employee Name"]:
            if key in kvp:
                names[doc_type] = kvp[key].strip().upper()

        # Collect DOBs
        for key in ["Date of Birth", "DOB"]:
            if key in kvp:
                dobs[doc_type] = kvp[key]

    # Check name consistency
    unique_names = set(names.values())
    if len(unique_names) > 1:
        issues.append({
            "type": "name_mismatch",
            "severity": "high",
            "details": {doc: name for doc, name in names.items()},
            "message": f"Name mismatch across documents: {dict(names)}",
        })

    # Check DOB consistency
    unique_dobs = set(dobs.values())
    if len(unique_dobs) > 1:
        issues.append({
            "type": "dob_mismatch",
            "severity": "high",
            "details": {doc: dob for doc, dob in dobs.items()},
            "message": f"DOB mismatch across documents: {dict(dobs)}",
        })

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "documents_checked": list(documents.keys()),
    }


CUSTOMER_FACING_TOOLS = [
    collect_basic_info, collect_loan_details, upload_document,
    show_verification, show_progress, show_eligibility, show_offer, show_decision,
]

BACKEND_TOOLS = [
    check_eligibility_tool, calculate_dti_tool, estimate_emi_tool,
    calculate_risk_score_tool, score_four_cs_tool, lookup_rate_tool,
    generate_emi_schedule_tool, check_negative_list_tool, aggregate_scores_tool,
    calculate_volatility_tool, scan_hidden_debts_tool, check_bias_tool,
    extract_document_tool, cross_validate_documents,
]
