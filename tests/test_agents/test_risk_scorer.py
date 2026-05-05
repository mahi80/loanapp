from __future__ import annotations

from src.tools.internal.risk_scorer import calculate_risk_score


class TestRiskScorer:
    def test_low_risk_salaried(self):
        result = calculate_risk_score(
            bureau_score=780,
            dti_ratio=0.30,
            income_stability=0.95,
            employment_type="salaried",
            loan_amount=500000,
            existing_obligations=15000,
            enquiry_count=1,
            delinquency_count=0,
        )
        assert result["risk_category"] == "low"
        assert result["score"] >= 75
        assert result["confidence"] == 0.9

    def test_high_risk_unemployed(self):
        result = calculate_risk_score(
            bureau_score=450,
            dti_ratio=0.70,
            income_stability=0.2,
            employment_type="unemployed",
            loan_amount=1000000,
            existing_obligations=50000,
            enquiry_count=8,
            delinquency_count=3,
        )
        assert result["risk_category"] in ("high", "very_high")
        assert result["score"] < 40

    def test_medium_risk_gig_worker(self):
        result = calculate_risk_score(
            bureau_score=650,
            dti_ratio=0.42,
            income_stability=0.6,
            employment_type="gig_worker",
            loan_amount=300000,
            existing_obligations=20000,
            enquiry_count=4,
            delinquency_count=0,
        )
        assert result["risk_category"] in ("medium", "high")
        assert 30 < result["score"] < 75

    def test_thin_file_no_bureau(self):
        result = calculate_risk_score(
            bureau_score=None,
            dti_ratio=0.35,
            income_stability=0.8,
            employment_type="salaried",
            loan_amount=200000,
            existing_obligations=10000,
        )
        assert result["confidence"] == 0.6  # Lower confidence for thin file
        assert result["factors"]["bureau_score"]["value"] is None

    def test_score_boundaries(self):
        # Perfect applicant
        result = calculate_risk_score(
            bureau_score=900, dti_ratio=0.0, income_stability=1.0,
            employment_type="salaried", loan_amount=100000,
            existing_obligations=0, enquiry_count=0, delinquency_count=0,
        )
        assert result["score"] <= 100
        assert result["risk_category"] == "low"

        # Worst applicant
        result = calculate_risk_score(
            bureau_score=300, dti_ratio=1.0, income_stability=0.0,
            employment_type="unemployed", loan_amount=10000000,
            existing_obligations=500000, enquiry_count=20, delinquency_count=10,
        )
        assert result["score"] >= 0
        assert result["risk_category"] == "very_high"

    def test_factor_weights_sum_to_one(self):
        result = calculate_risk_score(
            bureau_score=700, dti_ratio=0.4, income_stability=0.7,
            employment_type="salaried", loan_amount=500000,
            existing_obligations=20000,
        )
        total_weight = sum(f["weight"] for f in result["factors"].values())
        assert abs(total_weight - 1.0) < 0.001
