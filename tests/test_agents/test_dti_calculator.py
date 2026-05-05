from __future__ import annotations

import pytest
from src.tools.internal.dti_calculator import calculate_dti, estimate_emi


class TestEMICalculation:
    def test_standard_emi(self):
        emi = estimate_emi(principal=500000, annual_rate=12.0, tenure_months=36)
        assert 16000 < emi < 17000  # ~16,607

    def test_zero_rate(self):
        emi = estimate_emi(principal=120000, annual_rate=0.0, tenure_months=12)
        assert emi == 10000.0

    def test_high_rate(self):
        emi = estimate_emi(principal=100000, annual_rate=24.0, tenure_months=12)
        assert emi > 9000  # Higher monthly payment due to interest

    def test_long_tenure(self):
        emi_short = estimate_emi(principal=1000000, annual_rate=10.0, tenure_months=60)
        emi_long = estimate_emi(principal=1000000, annual_rate=10.0, tenure_months=240)
        assert emi_long < emi_short  # Longer tenure = lower EMI


class TestDTICalculator:
    def test_healthy_dti(self):
        result = calculate_dti(
            monthly_income=100000,
            existing_emis=10000,
            proposed_emi=15000,
            credit_card_outstanding=0,
            other_obligations=0,
        )
        assert result["assessment"] == "healthy"
        assert result["dti_ratio"] == 0.25

    def test_acceptable_dti(self):
        result = calculate_dti(
            monthly_income=100000,
            existing_emis=20000,
            proposed_emi=18000,
        )
        assert result["assessment"] == "acceptable"
        assert 0.36 < result["dti_ratio"] <= 0.43

    def test_stretched_dti(self):
        result = calculate_dti(
            monthly_income=100000,
            existing_emis=25000,
            proposed_emi=20000,
        )
        assert result["assessment"] == "stretched"

    def test_over_leveraged_dti(self):
        result = calculate_dti(
            monthly_income=50000,
            existing_emis=20000,
            proposed_emi=15000,
            credit_card_outstanding=100000,
        )
        assert result["assessment"] == "over_leveraged"
        assert result["dti_ratio"] > 0.50

    def test_zero_income(self):
        result = calculate_dti(
            monthly_income=0,
            existing_emis=10000,
            proposed_emi=5000,
        )
        assert result["dti_ratio"] == 1.0
        assert result["assessment"] == "insufficient_income"

    def test_credit_card_minimum_due(self):
        """Credit card outstanding uses 5% as minimum due obligation."""
        result = calculate_dti(
            monthly_income=100000,
            existing_emis=0,
            proposed_emi=10000,
            credit_card_outstanding=200000,
        )
        # 10000 + (200000 * 0.05) = 20000
        assert result["breakdown"]["credit_card_min_due"] == 10000.0
        assert result["total_obligations"] == 20000.0

    def test_breakdown_completeness(self):
        result = calculate_dti(
            monthly_income=80000,
            existing_emis=15000,
            proposed_emi=12000,
            credit_card_outstanding=50000,
            other_obligations=3000,
        )
        b = result["breakdown"]
        assert b["existing_emis"] == 15000
        assert b["proposed_emi"] == 12000
        assert b["credit_card_min_due"] == 2500.0
        assert b["other_obligations"] == 3000
        assert b["monthly_income"] == 80000
        expected_total = 15000 + 12000 + 2500 + 3000
        assert b["total_obligations"] == expected_total
