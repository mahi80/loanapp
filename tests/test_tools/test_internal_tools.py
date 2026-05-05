from __future__ import annotations

from src.tools.internal.negative_list import check_negative_list
from src.tools.internal.four_c_scorer import score_four_cs
from src.tools.internal.volatility_calculator import calculate_volatility
from src.tools.internal.hidden_debt_scanner import scan_hidden_debts
from src.tools.internal.weighted_aggregator import aggregate_scores
from src.tools.internal.rate_card_engine import lookup_rate
from src.tools.internal.emi_scheduler import generate_emi_schedule
from src.tools.internal.bias_detector import check_bias


class TestNegativeList:
    def test_hit_on_matching_entry(self):
        entries = [
            {"name": "John Doe", "type": "individual", "reason": "fraud"},
            {"name": "ACME Corp", "type": "company", "reason": "default"},
        ]
        result = check_negative_list("John Doe", list_type="individual", negative_entries=entries)
        assert result["is_negative"] is True
        assert result["matched_entry"]["name"] == "John Doe"

    def test_clear_when_no_match(self):
        entries = [{"name": "Jane Smith", "type": "individual", "reason": "fraud"}]
        result = check_negative_list("Robert Brown", list_type="individual", negative_entries=entries)
        assert result["is_negative"] is False
        assert result["matched_entry"] is None


class TestFourCScorer:
    def test_good_profile_scores(self):
        result = score_four_cs(
            bureau_score=780,
            repayment_history=0.95,
            monthly_income=100_000,
            total_obligations=20_000,
            assets_value=500_000,
            savings_balance=200_000,
        )
        assert 0 <= result["character"] <= 100
        assert 0 <= result["capacity"] <= 100
        assert 0 <= result["capital"] <= 100
        assert result["collateral"] == 50
        # Good bureau + good repayment -> character should be high
        assert result["character"] >= 70
        # Low obligation ratio -> capacity should be high
        assert result["capacity"] >= 70


class TestVolatilityCalculator:
    def test_stable_income(self):
        incomes = [50_000, 50_000, 50_000, 50_000, 50_000, 50_000]
        result = calculate_volatility(incomes)
        assert result["coefficient_of_variation"] == 0.0
        assert result["stability_score"] == 100.0
        assert result["trend"] == "stable"
        assert result["mean_income"] == 50_000.0


class TestHiddenDebtScanner:
    def test_detects_hidden_recurring_debit(self):
        bank_debits = [
            {"amount": 5000.0, "description": "EMI HDFC"},
            {"amount": 5000.0, "description": "EMI HDFC"},
            {"amount": 5000.0, "description": "EMI HDFC"},
        ]
        bureau_emis = [{"amount": 8000.0, "lender": "SBI"}]
        result = scan_hidden_debts(bank_debits, bureau_emis)
        assert len(result["hidden_debts"]) == 1
        assert result["hidden_debts"][0]["amount"] == 5000.0
        assert result["total_hidden_monthly"] == 5000.0


class TestWeightedAggregator:
    def test_composite_score_scaling(self):
        scores = {"bureau": 80.0, "dti": 70.0, "stability": 90.0}
        weights = {"bureau": 0.4, "dti": 0.3, "stability": 0.3}
        result = aggregate_scores(scores, weights)
        assert 300 <= result["composite_score"] <= 900
        assert result["risk_category"] in ("low", "medium", "high", "very_high")
        assert result["confidence"] == 1.0

    def test_fraud_penalty_lowers_score(self):
        scores = {"bureau": 80.0, "dti": 70.0, "stability": 90.0}
        weights = {"bureau": 0.4, "dti": 0.3, "stability": 0.3}
        clean = aggregate_scores(scores, weights)
        flagged = aggregate_scores(scores, weights, fraud_flags=["doc_tamper"])
        assert flagged["composite_score"] < clean["composite_score"]


class TestRateCardEngine:
    def test_default_personal_low_risk(self):
        result = lookup_rate("low", loan_type="personal", score=700)
        assert result["interest_rate"] > 0
        assert result["processing_fee_pct"] > 0
        assert result["insurance_pct"] > 0


class TestEmiScheduler:
    def test_basic_schedule(self):
        result = generate_emi_schedule(
            principal=100_000,
            annual_rate=12.0,
            tenure_months=12,
            start_date="2026-01-15",
        )
        assert result["emi_amount"] > 0
        assert len(result["payments"]) == 12
        assert result["total_payment"] > 100_000
        # First payment should be on the start date
        assert result["payments"][0]["date"] == "2026-01-15"


class TestBiasDetector:
    def test_no_bias_equal_rates(self):
        decisions = [
            {"gender": "M", "approved": True},
            {"gender": "M", "approved": False},
            {"gender": "F", "approved": True},
            {"gender": "F", "approved": False},
        ]
        result = check_bias(decisions, "gender")
        assert result["disparate_impact_ratio"] == 1.0
        assert result["bias_detected"] is False

    def test_bias_detected_unequal_rates(self):
        decisions = (
            [{"gender": "M", "approved": True}] * 9
            + [{"gender": "M", "approved": False}] * 1
            + [{"gender": "F", "approved": True}] * 3
            + [{"gender": "F", "approved": False}] * 7
        )
        result = check_bias(decisions, "gender")
        # M rate = 0.9, F rate = 0.3 -> ratio = 0.3/0.9 = 0.333 < 0.8
        assert result["bias_detected"] is True
        assert result["disparate_impact_ratio"] < 0.8
