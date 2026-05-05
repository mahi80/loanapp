from __future__ import annotations

from src.tools.internal.eligibility_rules import check_eligibility


class TestCheckEligibility:
    """Five tests covering the eligibility gate."""

    def test_eligible_applicant(self):
        """Happy path -- all criteria met."""
        result = check_eligibility(age=30, monthly_income=50_000, city="Mumbai", loan_amount=500_000)
        assert result["eligible"] is True
        assert result["rejection_reason"] is None

    def test_rejected_age_too_young(self):
        """Applicant under 21 should be rejected."""
        result = check_eligibility(age=19, monthly_income=50_000, city="Delhi", loan_amount=100_000)
        assert result["eligible"] is False
        assert "below the minimum age" in result["rejection_reason"]

    def test_rejected_age_too_old(self):
        """Applicant over 58 should be rejected."""
        result = check_eligibility(age=60, monthly_income=80_000, city="Pune", loan_amount=200_000)
        assert result["eligible"] is False
        assert "exceeds the maximum age" in result["rejection_reason"]

    def test_rejected_low_income(self):
        """Income below 15,000 should be rejected."""
        result = check_eligibility(age=35, monthly_income=10_000, city="Chennai", loan_amount=100_000)
        assert result["eligible"] is False
        assert "below the minimum required income" in result["rejection_reason"]

    def test_rejected_loan_exceeds_multiplier(self):
        """Loan amount > 60x income should be rejected."""
        result = check_eligibility(age=35, monthly_income=20_000, city="Bengaluru", loan_amount=1_500_000)
        # 60 * 20000 = 1_200_000 < 1_500_000
        assert result["eligible"] is False
        assert "exceeds the maximum allowed" in result["rejection_reason"]
