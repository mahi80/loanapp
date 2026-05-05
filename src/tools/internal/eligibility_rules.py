from __future__ import annotations

import structlog

logger = structlog.get_logger()

MIN_AGE = 21
MAX_AGE = 58
MIN_MONTHLY_INCOME = 15_000
MAX_LOAN_INCOME_MULTIPLIER = 60


def check_eligibility(
    age: int,
    monthly_income: float,
    city: str,
    loan_amount: float,
) -> dict:
    """Check basic eligibility for a personal loan.

    Rules:
      - Age must be between 21 and 58 (inclusive).
      - Minimum monthly income of 15,000.
      - Maximum loan amount is 60x monthly income.

    Returns dict with ``eligible`` (bool) and ``rejection_reason`` (str | None).
    """
    if age < MIN_AGE:
        reason = f"Applicant age {age} is below the minimum age of {MIN_AGE}"
        logger.info("eligibility_rejected", reason=reason, age=age)
        return {"eligible": False, "rejection_reason": reason}

    if age > MAX_AGE:
        reason = f"Applicant age {age} exceeds the maximum age of {MAX_AGE}"
        logger.info("eligibility_rejected", reason=reason, age=age)
        return {"eligible": False, "rejection_reason": reason}

    if monthly_income < MIN_MONTHLY_INCOME:
        reason = (
            f"Monthly income {monthly_income} is below the minimum "
            f"required income of {MIN_MONTHLY_INCOME}"
        )
        logger.info("eligibility_rejected", reason=reason, monthly_income=monthly_income)
        return {"eligible": False, "rejection_reason": reason}

    max_loan = monthly_income * MAX_LOAN_INCOME_MULTIPLIER
    if loan_amount > max_loan:
        reason = (
            f"Requested loan amount {loan_amount} exceeds the maximum "
            f"allowed {max_loan} (60x monthly income)"
        )
        logger.info(
            "eligibility_rejected",
            reason=reason,
            loan_amount=loan_amount,
            max_loan=max_loan,
        )
        return {"eligible": False, "rejection_reason": reason}

    logger.info(
        "eligibility_approved",
        age=age,
        monthly_income=monthly_income,
        city=city,
        loan_amount=loan_amount,
    )
    return {"eligible": True, "rejection_reason": None}
