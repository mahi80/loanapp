from __future__ import annotations

import structlog

logger = structlog.get_logger()

# Output scale: 300 (worst) to 900 (best)
_SCALE_MIN = 300
_SCALE_MAX = 900

# Fraud penalty: each flag reduces the composite by this many points
_FRAUD_PENALTY_PER_FLAG = 50


def aggregate_scores(
    scores: dict[str, float],
    weights: dict[str, float],
    fraud_flags: list[str] | None = None,
) -> dict:
    """Produce a single composite score from individually weighted components.

    Parameters
    ----------
    scores:
        Mapping of component name -> raw score (each expected in
        0-100 range).
    weights:
        Mapping of component name -> weight (will be normalised so
        they sum to 1).
    fraud_flags:
        Optional list of fraud-flag identifiers.  Each flag applies a
        penalty to the final composite.

    Returns
    -------
    dict
        ``composite_score`` (int, 300-900), ``risk_category`` (str),
        ``confidence`` (float).
    """
    if fraud_flags is None:
        fraud_flags = []

    # Normalise weights
    total_weight = sum(weights.get(k, 0) for k in scores)
    if total_weight == 0:
        logger.warning("aggregator_zero_weights")
        return {
            "composite_score": _SCALE_MIN,
            "risk_category": "very_high",
            "confidence": 0.0,
        }

    # Weighted average in 0-100 space
    weighted_sum = 0.0
    for key, score in scores.items():
        w = weights.get(key, 0)
        weighted_sum += score * (w / total_weight)

    # Clamp to 0-100
    weighted_sum = max(0.0, min(100.0, weighted_sum))

    # Map from 0-100 -> 300-900
    composite = _SCALE_MIN + (weighted_sum / 100.0) * (_SCALE_MAX - _SCALE_MIN)

    # Apply fraud penalties
    penalty = len(fraud_flags) * _FRAUD_PENALTY_PER_FLAG
    composite = max(_SCALE_MIN, composite - penalty)
    composite = int(round(composite))

    # Risk category
    if composite >= 750:
        risk_category = "low"
    elif composite >= 600:
        risk_category = "medium"
    elif composite >= 450:
        risk_category = "high"
    else:
        risk_category = "very_high"

    # Confidence: proportion of score keys that have a matching weight
    matched = sum(1 for k in scores if k in weights)
    confidence = round(matched / max(len(scores), 1), 2)

    logger.info(
        "scores_aggregated",
        composite_score=composite,
        risk_category=risk_category,
        fraud_flags_count=len(fraud_flags),
        confidence=confidence,
    )

    return {
        "composite_score": composite,
        "risk_category": risk_category,
        "confidence": confidence,
    }
