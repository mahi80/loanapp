from __future__ import annotations

import structlog
from src.db.models import RiskCategory

logger = structlog.get_logger()


def calculate_risk_score(
    bureau_score: int | None,
    dti_ratio: float,
    income_stability: float,
    employment_type: str,
    loan_amount: float,
    existing_obligations: float,
    enquiry_count: int = 0,
    delinquency_count: int = 0,
) -> dict:
    """Calculate a composite risk score from multiple factors.

    Returns a dict with score (0-100), risk_category, and factor breakdown.
    Higher score = lower risk (better).
    """
    factors = {}

    # Bureau score component (30% weight)
    if bureau_score is not None:
        bureau_normalized = max(0, min(100, (bureau_score - 300) / 6))
    else:
        bureau_normalized = 30  # Thin file default
    factors["bureau_score"] = {"value": bureau_score, "normalized": bureau_normalized, "weight": 0.30}

    # DTI component (25% weight) - lower DTI is better
    dti_normalized = max(0, min(100, (1 - dti_ratio) * 100))
    factors["dti_ratio"] = {"value": dti_ratio, "normalized": dti_normalized, "weight": 0.25}

    # Income stability (20% weight)
    stability_normalized = income_stability * 100
    factors["income_stability"] = {"value": income_stability, "normalized": stability_normalized, "weight": 0.20}

    # Employment type (10% weight)
    emp_scores = {
        "salaried": 85,
        "self_employed": 65,
        "gig_worker": 45,
        "retired": 70,
        "student": 30,
        "unemployed": 10,
    }
    emp_normalized = emp_scores.get(employment_type, 50)
    factors["employment_type"] = {"value": employment_type, "normalized": emp_normalized, "weight": 0.10}

    # Credit behavior (15% weight)
    enquiry_penalty = min(30, enquiry_count * 5)
    delinquency_penalty = min(50, delinquency_count * 15)
    behavior_normalized = max(0, 100 - enquiry_penalty - delinquency_penalty)
    factors["credit_behavior"] = {
        "value": {"enquiries": enquiry_count, "delinquencies": delinquency_count},
        "normalized": behavior_normalized,
        "weight": 0.15,
    }

    # Weighted composite
    composite = sum(f["normalized"] * f["weight"] for f in factors.values())
    composite = round(composite, 2)

    # Map to risk category
    if composite >= 75:
        category = RiskCategory.LOW
    elif composite >= 55:
        category = RiskCategory.MEDIUM
    elif composite >= 35:
        category = RiskCategory.HIGH
    else:
        category = RiskCategory.VERY_HIGH

    logger.info("risk_score_calculated", composite=composite, category=category.value)

    return {
        "score": composite,
        "risk_category": category.value,
        "factors": factors,
        "confidence": _calculate_confidence(bureau_score is not None, factors),
    }


def _calculate_confidence(has_bureau: bool, factors: dict) -> float:
    """Calculate confidence level based on data completeness."""
    if has_bureau:
        return 0.9
    # Thin file - lower confidence
    return 0.6
