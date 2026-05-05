from __future__ import annotations

import math

import structlog

logger = structlog.get_logger()


def calculate_volatility(monthly_incomes: list[float]) -> dict:
    """Calculate income volatility from a series of monthly incomes.

    Uses the **coefficient of variation** (std-dev / mean) to gauge how
    stable the income stream is.

    Parameters
    ----------
    monthly_incomes:
        List of monthly income values (at least 2 entries recommended).

    Returns
    -------
    dict
        - ``coefficient_of_variation`` -- CV as a decimal (0.0 = perfectly
          stable).
        - ``stability_score`` -- 0 to 100, where 100 is rock-stable.
        - ``trend`` -- ``"increasing"``, ``"decreasing"``, or ``"stable"``.
        - ``mean_income`` -- arithmetic mean of the series.
    """
    if not monthly_incomes:
        logger.warning("volatility_empty_series")
        return {
            "coefficient_of_variation": 0.0,
            "stability_score": 0.0,
            "trend": "stable",
            "mean_income": 0.0,
        }

    n = len(monthly_incomes)
    mean_income = sum(monthly_incomes) / n

    if mean_income == 0:
        logger.warning("volatility_zero_mean")
        return {
            "coefficient_of_variation": 0.0,
            "stability_score": 0.0,
            "trend": "stable",
            "mean_income": 0.0,
        }

    # Population standard deviation
    variance = sum((x - mean_income) ** 2 for x in monthly_incomes) / n
    std_dev = math.sqrt(variance)
    cv = std_dev / mean_income

    # Stability score: CV of 0 -> 100, CV >= 1 -> 0, linear mapping
    stability_score = max(0.0, min(100.0, (1.0 - cv) * 100.0))

    # Trend detection: compare mean of first half vs second half
    if n >= 2:
        mid = n // 2
        first_half_mean = sum(monthly_incomes[:mid]) / mid
        second_half_mean = sum(monthly_incomes[mid:]) / (n - mid)
        diff_pct = (second_half_mean - first_half_mean) / max(first_half_mean, 1.0)
        if diff_pct > 0.05:
            trend = "increasing"
        elif diff_pct < -0.05:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"

    logger.info(
        "volatility_calculated",
        cv=round(cv, 4),
        stability_score=round(stability_score, 2),
        trend=trend,
        mean_income=round(mean_income, 2),
    )

    return {
        "coefficient_of_variation": round(cv, 4),
        "stability_score": round(stability_score, 2),
        "trend": trend,
        "mean_income": round(mean_income, 2),
    }
