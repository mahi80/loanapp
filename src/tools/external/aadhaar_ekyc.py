from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class AadhaarEKYCClient(BaseExternalClient):
    provider_name = "aadhaar_ekyc"

    async def _call_api(self, aadhaar_number: str, otp: str, consent: bool = True) -> CreditDataResponse:
        if not consent:
            return CreditDataResponse(
                success=False, provider=self.provider_name, data={}, error="Consent not provided"
            )

        if settings.is_development:
            mock = self._load_mock("aadhaar_ekyc_response")
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.surepass.io/api/v1/aadhaar-v2/submit-otp",
            headers={
                "Authorization": f"Bearer {settings.aadhaar_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "client_id": aadhaar_number,
                "otp": otp,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "name": data.get("data", {}).get("full_name"),
                "dob": data.get("data", {}).get("dob"),
                "address": data.get("data", {}).get("address", {}),
                "photo_base64": data.get("data", {}).get("photo_link"),
                "verified": True,
            },
            raw_response=data,
        )
