from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CKYCRegistryClient(BaseExternalClient):
    provider_name = "ckyc"

    async def _call_api(
        self, pan: str = "", aadhaar: str = "", ckyc_id: str = ""
    ) -> CreditDataResponse:
        if not pan and not aadhaar and not ckyc_id:
            return CreditDataResponse(
                success=False,
                provider=self.provider_name,
                data={},
                error="At least one of pan, aadhaar, or ckyc_id must be provided",
            )

        if settings.is_development:
            mock = {
                "ckyc_id": ckyc_id or "CKYC-MOCK-50001",
                "pan": pan,
                "aadhaar_last4": aadhaar[-4:] if aadhaar else "",
                "kyc_status": "verified",
                "name": "Raj Kumar Sharma",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        payload: dict = {}
        if pan:
            payload["pan"] = pan
        if aadhaar:
            payload["aadhaar"] = aadhaar
        if ckyc_id:
            payload["ckyc_id"] = ckyc_id

        response = await self._make_request(
            method="POST",
            url="https://api.ckyc.gov.in/search",
            headers={
                "Authorization": f"Bearer {settings.ckyc_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "ckyc_id": data.get("ckyc_id"),
                "kyc_status": data.get("kyc_status"),
                "name": data.get("name"),
            },
            raw_response=data,
        )
