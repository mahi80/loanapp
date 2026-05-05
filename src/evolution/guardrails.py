"""Evolution safety guardrails.

Ensures all evolved versions meet fairness, performance, and approval requirements
before being promoted to production.
"""

import structlog

logger = structlog.get_logger()


DISPARATE_IMPACT_THRESHOLD = 0.8  # 4/5ths rule
PERFORMANCE_FLOOR_DROP = 0.02     # Max 2% AUC-ROC drop allowed
SHADOW_MODE_HOURS = 48            # Hours in shadow mode before promotion
THRESHOLD_CHANGE_LIMIT = 0.05     # >5% threshold change requires human approval


def check_bias(metrics: dict) -> tuple[bool, str]:
    """Check fairness across demographic segments using 4/5ths rule.

    Returns (passed, reason).
    """
    segments = metrics.get("demographic_segments", {})

    for segment_name, segment_data in segments.items():
        approval_rates = segment_data.get("approval_rates", {})
        if not approval_rates:
            continue

        rates = list(approval_rates.values())
        if not rates:
            continue

        max_rate = max(rates)
        if max_rate == 0:
            continue

        for group, rate in approval_rates.items():
            ratio = rate / max_rate
            if ratio < DISPARATE_IMPACT_THRESHOLD:
                reason = (
                    f"Disparate impact detected in {segment_name}: "
                    f"group '{group}' has ratio {ratio:.3f} (threshold: {DISPARATE_IMPACT_THRESHOLD})"
                )
                logger.warning("bias_check_failed", segment=segment_name, group=group, ratio=ratio)
                return False, reason

    return True, "All segments pass 4/5ths rule"


def check_performance_floor(current_auc: float, evolved_auc: float) -> tuple[bool, str]:
    """Ensure evolved version doesn't drop AUC-ROC by more than 2%."""
    drop = current_auc - evolved_auc
    if drop > PERFORMANCE_FLOOR_DROP:
        reason = f"AUC-ROC dropped by {drop:.4f} (max allowed: {PERFORMANCE_FLOOR_DROP})"
        logger.warning("performance_floor_breach", current=current_auc, evolved=evolved_auc, drop=drop)
        return False, reason
    return True, f"AUC-ROC change: {-drop:+.4f}"


def requires_human_approval(change_type: str, change_magnitude: float) -> bool:
    """Determine if human sign-off is required."""
    if change_type == "workflow_topology":
        return True  # AFlow changes always need approval
    if change_type == "decision_threshold" and abs(change_magnitude) > THRESHOLD_CHANGE_LIMIT:
        return True
    return False


def validate_evolution(
    evolved_metrics: dict,
    current_metrics: dict,
    change_type: str,
) -> dict:
    """Run all guardrail checks on an evolved version.

    Returns validation result with pass/fail and reasons.
    """
    results = {"passed": True, "checks": [], "requires_human_approval": False}

    # Bias check
    bias_passed, bias_reason = check_bias(evolved_metrics)
    results["checks"].append({"name": "bias", "passed": bias_passed, "reason": bias_reason})
    if not bias_passed:
        results["passed"] = False

    # Performance floor
    current_auc = current_metrics.get("auc_roc", 0)
    evolved_auc = evolved_metrics.get("auc_roc", 0)
    perf_passed, perf_reason = check_performance_floor(current_auc, evolved_auc)
    results["checks"].append({"name": "performance", "passed": perf_passed, "reason": perf_reason})
    if not perf_passed:
        results["passed"] = False

    # Human approval check
    change_magnitude = abs(evolved_auc - current_auc)
    if requires_human_approval(change_type, change_magnitude):
        results["requires_human_approval"] = True

    # Shadow mode requirement
    results["shadow_mode_hours"] = SHADOW_MODE_HOURS

    logger.info(
        "evolution_validation",
        passed=results["passed"],
        requires_approval=results["requires_human_approval"],
        checks=[c["name"] + ":" + str(c["passed"]) for c in results["checks"]],
    )

    return results
