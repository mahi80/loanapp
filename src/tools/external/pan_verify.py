from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class PANVerifyClient(BaseExternalClient):
    provider_name = "pan_verify"

    async def _call_api(self, pan: str) -> CreditDataResponse:
        if settings.is_development:
            mock = self._load_mock("pan_verify_response")
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.surepass.io/api/v1/pan/pan",
            headers={
                "Authorization": f"Bearer {settings.pan_verify_api_key}",
                "Content-Type": "application/json",
            },
            json={"id_number": pan},
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "name": data.get("data", {}).get("full_name"),
                "pan_status": data.get("data", {}).get("pan_status"),
                "name_match_score": data.get("data", {}).get("name_match_score", 0),
                "valid": data.get("data", {}).get("valid", False),
            },
            raw_response=data,
        )
