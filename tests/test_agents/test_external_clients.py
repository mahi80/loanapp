from __future__ import annotations

import os
import pytest
import pytest_asyncio

os.environ["ENVIRONMENT"] = "development"

from src.tools.external.cibil_client import CIBILClient
from src.tools.external.experian_client import ExperianClient
from src.tools.external.pan_verify import PANVerifyClient
from src.tools.external.aadhaar_ekyc import AadhaarEKYCClient
from src.tools.external.bank_statement_analyzer import BankStatementAnalyzerClient
from src.tools.external.account_aggregator import AccountAggregatorClient
from src.tools.external.base_client import CircuitBreaker, CircuitState
from src.tools.external.crif_client import CRIFClient
from src.tools.external.equifax_client import EquifaxClient
from src.tools.external.face_match import FaceMatchClient
from src.tools.external.company_registry import CompanyRegistryClient
from src.tools.external.sanctions_checker import SanctionsClient
from src.tools.external.sms_gateway import SMSGatewayClient
from src.tools.external.email_client import EmailClient
from src.tools.external.penny_drop import PennyDropClient


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute()

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, window_seconds=60)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert not cb.can_execute()

    def test_success_resets(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert len(cb.failures) == 0

    def test_stays_closed_under_threshold(self):
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute()


@pytest.mark.asyncio
class TestCIBILClient:
    async def test_mock_returns_score(self):
        client = CIBILClient()
        result = await client.execute(
            pan="ABCDE1234F", name="Raj Kumar",
            dob="1990-05-15", address="Mumbai",
        )
        assert result.success is True
        assert result.provider == "cibil"
        assert result.data["score"] == 742
        assert len(result.data["repaymentHistory"]) > 0
        await client.close()

    async def test_latency_tracked(self):
        client = CIBILClient()
        result = await client.execute(
            pan="ABCDE1234F", name="Test", dob="2000-01-01", address="Delhi",
        )
        assert result.latency_ms >= 0
        await client.close()


@pytest.mark.asyncio
class TestExperianClient:
    async def test_mock_returns_data(self):
        client = ExperianClient()
        result = await client.execute(
            pan="ABCDE1234F", name="Raj Kumar",
            dob="1990-05-15", mobile="9876543210",
        )
        assert result.success is True
        assert result.provider == "experian"
        assert result.data["creditScore"] == 735
        await client.close()


@pytest.mark.asyncio
class TestPANVerifyClient:
    async def test_mock_pan_valid(self):
        client = PANVerifyClient()
        result = await client.execute(pan="ABCDE1234F")
        assert result.success is True
        assert result.provider == "pan_verify"
        # Mock returns raw fixture with nested "data" key
        data = result.data.get("data", result.data)
        assert data.get("pan_status") == "VALID" or data.get("valid") is True
        await client.close()


@pytest.mark.asyncio
class TestAadhaarEKYCClient:
    async def test_mock_aadhaar_verified(self):
        client = AadhaarEKYCClient()
        result = await client.execute(
            aadhaar_number="123456789012", otp="123456", consent=True,
        )
        assert result.success is True
        # Mock returns raw fixture with nested "data" key
        data = result.data.get("data", result.data)
        assert data.get("full_name") == "Raj Kumar Sharma" or data.get("name") == "Raj Kumar Sharma"
        await client.close()

    async def test_no_consent_fails(self):
        client = AadhaarEKYCClient()
        result = await client.execute(
            aadhaar_number="123456789012", otp="123456", consent=False,
        )
        assert result.success is False
        assert "Consent" in result.error
        await client.close()


@pytest.mark.asyncio
class TestBankStatementAnalyzer:
    async def test_mock_statement(self):
        client = BankStatementAnalyzerClient()
        result = await client.execute(document_url="mock://statement.pdf")
        assert result.success is True
        assert result.data["averageBalance"] == 125000
        assert len(result.data["monthlyIncome"]) == 3
        assert result.data["bouncedCheques"] == 0
        await client.close()


@pytest.mark.asyncio
class TestAccountAggregator:
    async def test_mock_aa_data(self):
        client = AccountAggregatorClient()
        result = await client.execute(
            consent_id="consent-123",
            fi_data_range_from="2026-01-01",
            fi_data_range_to="2026-03-31",
        )
        assert result.success is True
        assert len(result.data["accounts"]) >= 1
        assert result.data["accounts"][0]["bank"] == "HDFC Bank"
        await client.close()


@pytest.mark.asyncio
class TestCRIFClient:
    async def test_mock_returns_data(self):
        client = CRIFClient()
        result = await client.execute(pan="ABCDE1234F", name="Raj Kumar", dob="1990-05-15")
        assert result.success is True
        assert result.provider == "crif"
        assert result.data["score"] == 710
        await client.close()


@pytest.mark.asyncio
class TestEquifaxClient:
    async def test_mock_returns_data(self):
        client = EquifaxClient()
        result = await client.execute(pan="ABCDE1234F", name="Raj Kumar", dob="1990-05-15")
        assert result.success is True
        assert result.provider == "equifax"
        assert result.data["score"] == 725
        await client.close()


@pytest.mark.asyncio
class TestFaceMatchClient:
    async def test_mock_returns_match(self):
        client = FaceMatchClient()
        result = await client.execute(selfie_path="/tmp/selfie.jpg", id_photo_path="/tmp/id.jpg")
        assert result.success is True
        assert result.provider == "face_match"
        assert result.data["match_confidence"] == 92.5
        assert result.data["is_match"] is True
        await client.close()


@pytest.mark.asyncio
class TestCompanyRegistryClient:
    async def test_mock_returns_registered(self):
        client = CompanyRegistryClient()
        result = await client.execute(company_name="Infosys Limited", cin="L85110KA1981PLC013115")
        assert result.success is True
        assert result.provider == "company_registry"
        assert result.data["registered"] is True
        assert result.data["category"] == "MNC"
        await client.close()


@pytest.mark.asyncio
class TestSanctionsClient:
    async def test_mock_returns_clean(self):
        client = SanctionsClient()
        result = await client.execute(name="Raj Kumar", dob="1990-05-15")
        assert result.success is True
        assert result.provider == "sanctions"
        assert result.data["pep_match"] is False
        assert result.data["sanctions_match"] is False
        await client.close()


@pytest.mark.asyncio
class TestSMSGatewayClient:
    async def test_mock_sends_sms(self):
        client = SMSGatewayClient()
        result = await client.execute(mobile="9876543210", message="Your OTP is 123456")
        assert result.success is True
        assert result.provider == "sms_gateway"
        assert result.data["status"] == "sent"
        await client.close()


@pytest.mark.asyncio
class TestEmailClient:
    async def test_mock_sends_email(self):
        client = EmailClient()
        result = await client.execute(
            to="raj@example.com", subject="Loan Approved", body="Congratulations!"
        )
        assert result.success is True
        assert result.provider == "email"
        assert result.data["status"] == "delivered"
        await client.close()


@pytest.mark.asyncio
class TestPennyDropClient:
    async def test_mock_verifies_account(self):
        client = PennyDropClient()
        result = await client.execute(account_number="1234567890", ifsc="HDFC0001234")
        assert result.success is True
        assert result.provider == "penny_drop"
        assert result.data["account_active"] is True
        assert result.data["name_match"] is True
        await client.close()
