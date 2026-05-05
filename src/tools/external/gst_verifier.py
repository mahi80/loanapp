from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class GSTVerifierClient(BaseExternalClient):
    provider_name = "gst_verifier"

    async def _call_api(self, gstin: str) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "gstin": gstin,
                "status": "Active",
                "business_name": "Mock Enterprises Pvt Ltd",
                "registration_date": "2018-07-01",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.gst.gov.in/verify",
            headers={
                "Authorization": f"Bearer {settings.gst_verify_api_key}",
                "Content-Type": "application/json",
            },
            json={"gstin": gstin},
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "gstin": data.get("gstin"),
                "status": data.get("status"),
                "business_name": data.get("business_name"),
                "registration_date": data.get("registration_date"),
            },
            raw_response=data,
        )
