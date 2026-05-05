from __future__ import annotations

import structlog

logger = structlog.get_logger()


def score_four_cs(
    bureau_score: int,
    repayment_history: float,
    monthly_income: float,
    total_obligations: float,
    assets_value: float,
    savings_balance: float,
) -> dict:
    """Evaluate the 4-C credit framework.

    Parameters
    ----------
    bureau_score:
        Credit bureau score (typically 300-900).
    repayment_history:
        Fraction of EMIs paid on time (0.0 to 1.0).
    monthly_income:
        Gross monthly income.
    total_obligations:
        Sum of all existing monthly debt obligations.
    assets_value:
        Total value of owned assets (property, vehicles, etc.).
    savings_balance:
        Liquid savings / FD balance.

    Returns
    -------
    dict
        Keys ``character``, ``capacity``, ``capital``, ``collateral`` --
        each an int from 0 to 100.

    Scoring logic
    -------------
    * **Character** -- measures credit behavior via bureau score and
      repayment track record.  Bureau contributes 60 %, repayment
      history 40 %.
    * **Capacity** -- income headroom after obligations.
      ``(income - obligations) / income`` mapped to 0-100.
    * **Capital** -- financial cushion from assets and savings,
      evaluated as months of obligations that could be covered.
    * **Collateral** -- for unsecured personal loans this is a neutral
      50.  Could be overridden for secured products.
    """

    # --- Character (0-100) ---------------------------------------------------
    # Normalize bureau score: 300->0, 900->100
    bureau_norm = max(0.0, min(100.0, (bureau_score - 300) / 6.0))
    # Repayment history is already 0-1 -> scale to 0-100
    repayment_norm = max(0.0, min(100.0, repayment_history * 100.0))
    character = round(bureau_norm * 0.6 + repayment_norm * 0.4)
    character = max(0, min(100, character))

    # --- Capacity (0-100) ----------------------------------------------------
    if monthly_income <= 0:
        capacity = 0
    else:
        headroom = (monthly_income - total_obligations) / monthly_income
        # headroom of 1.0 (no debt) -> 100, headroom <= 0 -> 0
        capacity = round(max(0.0, min(1.0, headroom)) * 100)

    # --- Capital (0-100) -----------------------------------------------------
    # How many months of obligations can savings + liquidatable assets cover?
    combined_capital = assets_value + savings_balance
    if total_obligations > 0:
        months_covered = combined_capital / total_obligations
    else:
        # No obligations -- capital score based on absolute savings
        months_covered = min(24.0, combined_capital / max(monthly_income, 1.0) * 6)
    # Cap at 24 months of coverage -> 100
    capital = round(max(0.0, min(1.0, months_covered / 24.0)) * 100)

    # --- Collateral (neutral 50 for unsecured) --------------------------------
    collateral = 50

    logger.info(
        "four_c_scored",
        character=character,
        capacity=capacity,
        capital=capital,
        collateral=collateral,
    )

    return {
        "character": character,
        "capacity": capacity,
        "capital": capital,
        "collateral": collateral,
    }
