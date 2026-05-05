from __future__ import annotations

import structlog

logger = structlog.get_logger()

# Default rate cards keyed by (risk_category, loan_type)
_DEFAULT_RATE_CARDS: dict[tuple[str, str], dict] = {
    ("low", "personal"):       {"interest_rate": 10.5, "processing_fee_pct": 1.0, "insurance_pct": 0.30},
    ("medium", "personal"):    {"interest_rate": 14.0, "processing_fee_pct": 1.5, "insurance_pct": 0.40},
    ("high", "personal"):      {"interest_rate": 18.0, "processing_fee_pct": 2.0, "insurance_pct": 0.50},
    ("very_high", "personal"): {"interest_rate": 22.0, "processing_fee_pct": 2.5, "insurance_pct": 0.60},
    ("low", "home"):           {"interest_rate": 8.5,  "processing_fee_pct": 0.5, "insurance_pct": 0.20},
    ("medium", "home"):        {"interest_rate": 9.5,  "processing_fee_pct": 0.75, "insurance_pct": 0.25},
    ("high", "home"):          {"interest_rate": 11.0, "processing_fee_pct": 1.0, "insurance_pct": 0.30},
    ("very_high", "home"):     {"interest_rate": 13.0, "processing_fee_pct": 1.5, "insurance_pct": 0.40},
    ("low", "auto"):           {"interest_rate": 9.0,  "processing_fee_pct": 0.75, "insurance_pct": 0.25},
    ("medium", "auto"):        {"interest_rate": 11.5, "processing_fee_pct": 1.0, "insurance_pct": 0.30},
    ("high", "auto"):          {"interest_rate": 14.0, "processing_fee_pct": 1.5, "insurance_pct": 0.40},
    ("very_high", "auto"):     {"interest_rate": 17.0, "processing_fee_pct": 2.0, "insurance_pct": 0.50},
}

# Score-based rate adjustments -- reward excellent scores with a discount
_SCORE_DISCOUNT_THRESHOLDS: list[tuple[int, float]] = [
    (850, -0.50),  # exceptional
    (800, -0.25),  # very good
    (700, 0.0),    # good -- no change
]


def lookup_rate(
    risk_category: str,
    loan_type: str = "personal",
    score: int = 0,
    db_rate_cards: dict | None = None,
) -> dict:
    """Look up pricing from a rate card.

    Parameters
    ----------
    risk_category:
        One of ``"low"``, ``"medium"``, ``"high"``, ``"very_high"``.
    loan_type:
        Product type (``"personal"``, ``"home"``, ``"auto"``).
    score:
        Composite score (300-900) for score-based adjustments.
    db_rate_cards:
        Optional override mapping ``(risk_category, loan_type)`` ->
        ``{"interest_rate", "processing_fee_pct", "insurance_pct"}``.

    Returns
    -------
    dict
        ``{"interest_rate": float, "processing_fee_pct": float,
        "insurance_pct": float}``
    """
    cards = db_rate_cards if db_rate_cards is not None else _DEFAULT_RATE_CARDS
    key = (risk_category.lower(), loan_type.lower())

    card = cards.get(key)
    if card is None:
        # Fallback: use high-risk personal as a safe default
        card = cards.get(("high", "personal"), {
            "interest_rate": 18.0,
            "processing_fee_pct": 2.0,
            "insurance_pct": 0.50,
        })
        logger.warning(
            "rate_card_fallback",
            requested_key=key,
            fallback_key=("high", "personal"),
        )

    # Copy so we don't mutate the original
    result = dict(card)

    # Apply score-based discount
    discount = 0.0
    for threshold, adj in _SCORE_DISCOUNT_THRESHOLDS:
        if score >= threshold:
            discount = adj
            break
    result["interest_rate"] = round(result["interest_rate"] + discount, 2)

    logger.info(
        "rate_looked_up",
        risk_category=risk_category,
        loan_type=loan_type,
        score=score,
        interest_rate=result["interest_rate"],
    )

    return result
