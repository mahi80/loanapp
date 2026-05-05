from __future__ import annotations

import uuid
import pytest
from pydantic import ValidationError

from src.api.models.schemas import (
    ApplicantInfoCreate, LoanDetails, ApplicationCreate,
    WebhookCreate, HITLReviewCreate,
)
from src.db.models import LoanType, EmploymentType, DecisionEnum


class TestApplicantInfoCreate:
    def test_valid_pan(self):
        info = ApplicantInfoCreate(
            name="Raj Kumar", pan_number="ABCDE1234F", income=75000,
        )
        assert info.pan_number == "ABCDE1234F"

    def test_invalid_pan_rejected(self):
        with pytest.raises(ValidationError):
            ApplicantInfoCreate(name="Test", pan_number="INVALID123")

    def test_invalid_pan_lowercase(self):
        with pytest.raises(ValidationError):
            ApplicantInfoCreate(name="Test", pan_number="abcde1234f")

    def test_optional_fields(self):
        info = ApplicantInfoCreate(name="Test", pan_number="ABCDE1234F")
        assert info.income is None
        assert info.employer is None
        assert info.employment_type is None


class TestLoanDetails:
    def test_valid_loan(self):
        loan = LoanDetails(amount=500000, loan_type=LoanType.PERSONAL)
        assert loan.amount == 500000

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            LoanDetails(amount=0, loan_type=LoanType.PERSONAL)

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            LoanDetails(amount=-100000, loan_type=LoanType.HOME)


class TestApplicationCreate:
    def test_full_application(self):
        app = ApplicationCreate(
            applicant_info=ApplicantInfoCreate(
                name="Raj Kumar Sharma",
                pan_number="ABCDE1234F",
                income=75000,
                employer="TCS Ltd",
                employment_type=EmploymentType.SALARIED,
                mobile="9876543210",
            ),
            loan_details=LoanDetails(amount=500000, loan_type=LoanType.PERSONAL),
        )
        assert app.applicant_info.name == "Raj Kumar Sharma"
        assert app.loan_details.amount == 500000


class TestWebhookCreate:
    def test_valid_webhook(self):
        wh = WebhookCreate(url="https://example.com/hook", events=["decision.made"])
        assert wh.url == "https://example.com/hook"
        assert len(wh.events) == 1


class TestHITLReviewCreate:
    def test_approve_review(self):
        review = HITLReviewCreate(
            decision=DecisionEnum.APPROVED,
            officer_notes="Looks good after manual review",
        )
        assert review.decision == DecisionEnum.APPROVED

    def test_deny_with_reason(self):
        review = HITLReviewCreate(
            decision=DecisionEnum.DENIED,
            officer_notes="Income cannot be verified",
            override_reason="Insufficient documentation",
        )
        assert review.override_reason == "Insufficient documentation"
