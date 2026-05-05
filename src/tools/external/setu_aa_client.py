from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class SetuAAClient(BaseExternalClient):
    provider_name = "setu_aa"

    async def _call_api(self, consent_id: str, aa_handle: str) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "consent_id": consent_id,
                "aa_handle": aa_handle,
                "status": "ACTIVE",
                "fi_data": [
                    {"account_type": "SAVINGS", "balance": 245000, "bank": "HDFC Bank"},
                ],
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.setu.co/aa/fi-fetch",
            headers={
                "Authorization": f"Bearer {settings.setu_aa_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "consent_id": consent_id,
                "aa_handle": aa_handle,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "consent_id": data.get("consent_id"),
                "status": data.get("status"),
                "fi_data": data.get("fi_data", []),
            },
            raw_response=data,
        )
