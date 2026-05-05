from __future__ import annotations

import structlog

logger = structlog.get_logger()

# The 4/5ths (80 %) rule threshold from EEOC Uniform Guidelines.
_FOUR_FIFTHS_THRESHOLD = 0.8


def check_bias(
    decisions: list[dict],
    protected_field: str,
) -> dict:
    """Perform a disparate-impact (4/5ths rule) check on lending decisions.

    Parameters
    ----------
    decisions:
        List of decision dicts, each containing at least an ``"approved"``
        boolean and the *protected_field* key (e.g. ``"gender"``,
        ``"ethnicity"``).
    protected_field:
        The key in each decision dict that identifies the protected
        attribute to test.

    Returns
    -------
    dict
        ``disparate_impact_ratio`` (float), ``bias_detected`` (bool),
        and ``approval_rates`` (dict mapping each group value to its
        approval rate).

    Notes
    -----
    The **4/5ths rule** states that if the approval rate for any group
    is less than 80 % of the highest group's approval rate, disparate
    impact is indicated.
    """
    if not decisions:
        logger.warning("bias_check_empty_decisions")
        return {
            "disparate_impact_ratio": 1.0,
            "bias_detected": False,
            "approval_rates": {},
        }

    # Bucket decisions by group
    group_counts: dict[str, int] = {}
    group_approvals: dict[str, int] = {}

    for dec in decisions:
        group = str(dec.get(protected_field, "unknown"))
        group_counts[group] = group_counts.get(group, 0) + 1
        if dec.get("approved"):
            group_approvals[group] = group_approvals.get(group, 0) + 1

    # Compute per-group approval rates
    approval_rates: dict[str, float] = {}
    for group, count in group_counts.items():
        approvals = group_approvals.get(group, 0)
        approval_rates[group] = round(approvals / count, 4) if count > 0 else 0.0

    if not approval_rates:
        return {
            "disparate_impact_ratio": 1.0,
            "bias_detected": False,
            "approval_rates": {},
        }

    max_rate = max(approval_rates.values())
    if max_rate == 0:
        # No approvals at all -- cannot compute ratio meaningfully
        disparate_impact_ratio = 1.0
    else:
        min_rate = min(approval_rates.values())
        disparate_impact_ratio = round(min_rate / max_rate, 4)

    bias_detected = disparate_impact_ratio < _FOUR_FIFTHS_THRESHOLD

    if bias_detected:
        logger.warning(
            "bias_detected",
            protected_field=protected_field,
            disparate_impact_ratio=disparate_impact_ratio,
            approval_rates=approval_rates,
        )
    else:
        logger.info(
            "bias_check_passed",
            protected_field=protected_field,
            disparate_impact_ratio=disparate_impact_ratio,
        )

    return {
        "disparate_impact_ratio": disparate_impact_ratio,
        "bias_detected": bias_detected,
        "approval_rates": approval_rates,
    }
