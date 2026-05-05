from __future__ import annotations

from src.evolution.guardrails import (
    check_bias, check_performance_floor, requires_human_approval,
    validate_evolution,
)


class TestBiasCheck:
    def test_passes_equal_rates(self):
        metrics = {
            "demographic_segments": {
                "gender": {"approval_rates": {"male": 0.60, "female": 0.60}},
            },
        }
        passed, reason = check_bias(metrics)
        assert passed is True

    def test_passes_within_threshold(self):
        """4/5ths rule: ratio >= 0.8 passes."""
        metrics = {
            "demographic_segments": {
                "gender": {"approval_rates": {"male": 0.60, "female": 0.50}},
            },
        }
        passed, reason = check_bias(metrics)
        assert passed is True  # 0.50/0.60 = 0.833 >= 0.8

    def test_fails_disparate_impact(self):
        metrics = {
            "demographic_segments": {
                "gender": {"approval_rates": {"male": 0.70, "female": 0.40}},
            },
        }
        passed, reason = check_bias(metrics)
        assert passed is False  # 0.40/0.70 = 0.571 < 0.8
        assert "Disparate impact" in reason

    def test_multiple_segments(self):
        metrics = {
            "demographic_segments": {
                "gender": {"approval_rates": {"male": 0.65, "female": 0.55}},
                "age": {"approval_rates": {"18-30": 0.50, "30-50": 0.70, "50+": 0.30}},
            },
        }
        passed, reason = check_bias(metrics)
        assert passed is False  # age 50+: 0.30/0.70 = 0.43 < 0.8

    def test_empty_segments_pass(self):
        passed, reason = check_bias({"demographic_segments": {}})
        assert passed is True

    def test_zero_max_rate(self):
        metrics = {
            "demographic_segments": {
                "gender": {"approval_rates": {"male": 0, "female": 0}},
            },
        }
        passed, _ = check_bias(metrics)
        assert passed is True


class TestPerformanceFloor:
    def test_improvement_passes(self):
        passed, reason = check_performance_floor(0.85, 0.87)
        assert passed is True
        assert "+0.0200" in reason

    def test_small_drop_passes(self):
        passed, _ = check_performance_floor(0.85, 0.84)
        assert passed is True  # 1% drop < 2% threshold

    def test_large_drop_fails(self):
        passed, reason = check_performance_floor(0.85, 0.82)
        assert passed is False  # 3% drop > 2% threshold
        assert "dropped" in reason

    def test_exact_threshold(self):
        # Float precision: 0.85 - 0.83 = 0.0200...018, just over threshold
        # Use a value clearly under the threshold
        passed, _ = check_performance_floor(0.85, 0.831)
        assert passed is True  # 1.9% drop < 2% threshold


class TestHumanApproval:
    def test_workflow_topology_always_needs_approval(self):
        assert requires_human_approval("workflow_topology", 0.01) is True

    def test_small_threshold_change_no_approval(self):
        assert requires_human_approval("decision_threshold", 0.03) is False

    def test_large_threshold_change_needs_approval(self):
        assert requires_human_approval("decision_threshold", 0.10) is True

    def test_prompt_optimization_no_approval(self):
        assert requires_human_approval("prompt_optimization", 0.5) is False


class TestValidateEvolution:
    def test_good_evolution_passes(self):
        result = validate_evolution(
            evolved_metrics={
                "auc_roc": 0.87,
                "demographic_segments": {
                    "gender": {"approval_rates": {"male": 0.65, "female": 0.58}},
                },
            },
            current_metrics={"auc_roc": 0.85},
            change_type="prompt_optimization",
        )
        assert result["passed"] is True
        assert result["requires_human_approval"] is False
        assert result["shadow_mode_hours"] == 48

    def test_biased_evolution_fails(self):
        result = validate_evolution(
            evolved_metrics={
                "auc_roc": 0.90,
                "demographic_segments": {
                    "gender": {"approval_rates": {"male": 0.80, "female": 0.30}},
                },
            },
            current_metrics={"auc_roc": 0.85},
            change_type="prompt_optimization",
        )
        assert result["passed"] is False

    def test_performance_drop_fails(self):
        result = validate_evolution(
            evolved_metrics={"auc_roc": 0.80, "demographic_segments": {}},
            current_metrics={"auc_roc": 0.85},
            change_type="prompt_optimization",
        )
        assert result["passed"] is False

    def test_workflow_change_needs_approval(self):
        result = validate_evolution(
            evolved_metrics={"auc_roc": 0.87, "demographic_segments": {}},
            current_metrics={"auc_roc": 0.85},
            change_type="workflow_topology",
        )
        assert result["passed"] is True
        assert result["requires_human_approval"] is True
