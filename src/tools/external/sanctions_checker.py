from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class SanctionsClient(BaseExternalClient):
    provider_name = "sanctions"

    async def _call_api(self, name: str, dob: str) -> CreditDataResponse:
        if settings.is_development:
            mock = {"pep_match": False, "sanctions_match": False}
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.sanctions-screening.in/check",
            headers={
                "Authorization": f"Bearer {settings.sanctions_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "name": name,
                "dob": dob,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "pep_match": data.get("pep_match", False),
                "sanctions_match": data.get("sanctions_match", False),
                "watchlist_hits": data.get("watchlist_hits", []),
            },
            raw_response=data,
        )
