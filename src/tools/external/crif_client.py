from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CRIFClient(BaseExternalClient):
    provider_name = "crif"

    async def _call_api(self, pan: str, name: str, dob: str) -> CreditDataResponse:
        if settings.is_development:
            mock = self._load_mock("crif_response")
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.crifhighmark.com/credit-report",
            headers={
                "Authorization": f"Bearer {settings.crif_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "pan": pan,
                "name": name,
                "dob": dob,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "score": data.get("score"),
                "mfiHistory": data.get("mfiHistory", []),
                "nbfcData": data.get("nbfcData", []),
            },
            raw_response=data,
        )
