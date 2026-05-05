from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class PennyDropClient(BaseExternalClient):
    provider_name = "penny_drop"

    async def _call_api(self, account_number: str, ifsc: str) -> CreditDataResponse:
        if settings.is_development:
            mock = {"account_active": True, "name_match": True}
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.pennydrop.in/verify",
            headers={
                "Authorization": f"Bearer {settings.penny_drop_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "account_number": account_number,
                "ifsc": ifsc,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "account_active": data.get("account_active"),
                "name_match": data.get("name_match"),
                "account_holder_name": data.get("account_holder_name"),
            },
            raw_response=data,
        )
