from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class ExperianClient(BaseExternalClient):
    provider_name = "experian"

    async def _call_api(self, pan: str, name: str, dob: str, mobile: str) -> CreditDataResponse:
        if settings.is_development:
            mock = self._load_mock("experian_response")
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.experian.in/credit-report",
            headers={
                "Authorization": f"Bearer {settings.experian_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "pan": pan,
                "name": name,
                "dob": dob,
                "mobile": mobile,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "score": data.get("creditScore"),
                "credit_summary": data.get("creditSummary", {}),
                "delinquency_info": data.get("delinquencyInfo", {}),
                "enquiry_count": data.get("enquiryCount", 0),
            },
            raw_response=data,
        )
