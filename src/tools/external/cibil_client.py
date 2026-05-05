from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CIBILClient(BaseExternalClient):
    provider_name = "cibil"

    async def _call_api(self, pan: str, name: str, dob: str, address: str) -> CreditDataResponse:
        if settings.is_development:
            mock = self._load_mock("cibil_response")
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://apimarketplace.transunioncibil.com/credit-report",
            headers={
                "Authorization": f"Bearer {settings.cibil_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "pan": pan,
                "name": name,
                "dob": dob,
                "address": address,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "score": data.get("score"),
                "repayment_history": data.get("repaymentHistory", []),
                "active_accounts": data.get("activeAccounts", []),
                "enquiry_count": data.get("enquiryCount", 0),
                "total_outstanding": data.get("totalOutstanding", 0),
            },
            raw_response=data,
        )
