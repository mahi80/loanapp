from __future__ import annotations

import structlog

logger = structlog.get_logger()


def calculate_dti(
    monthly_income: float,
    existing_emis: float,
    proposed_emi: float,
    credit_card_outstanding: float = 0,
    other_obligations: float = 0,
) -> dict:
    """Calculate Debt-to-Income ratio.

    Returns DTI ratio, breakdown, and assessment.
    """
    total_obligations = existing_emis + proposed_emi + (credit_card_outstanding * 0.05) + other_obligations

    if monthly_income <= 0:
        return {
            "dti_ratio": 1.0,
            "total_obligations": total_obligations,
            "monthly_income": monthly_income,
            "assessment": "insufficient_income",
            "breakdown": {},
        }

    dti_ratio = total_obligations / monthly_income

    breakdown = {
        "existing_emis": existing_emis,
        "proposed_emi": proposed_emi,
        "credit_card_min_due": credit_card_outstanding * 0.05,
        "other_obligations": other_obligations,
        "total_obligations": total_obligations,
        "monthly_income": monthly_income,
    }

    if dti_ratio <= 0.36:
        assessment = "healthy"
    elif dti_ratio <= 0.43:
        assessment = "acceptable"
    elif dti_ratio <= 0.50:
        assessment = "stretched"
    else:
        assessment = "over_leveraged"

    logger.info("dti_calculated", dti_ratio=round(dti_ratio, 4), assessment=assessment)

    return {
        "dti_ratio": round(dti_ratio, 4),
        "total_obligations": round(total_obligations, 2),
        "monthly_income": monthly_income,
        "assessment": assessment,
        "breakdown": breakdown,
    }


def estimate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Calculate EMI using standard formula."""
    if annual_rate == 0:
        return principal / tenure_months
    monthly_rate = annual_rate / 12 / 100
    emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
    return round(emi, 2)
