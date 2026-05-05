from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class EMandateClient(BaseExternalClient):
    provider_name = "emandate"

    async def _call_api(
        self, account_number: str, ifsc: str, amount: float, frequency: str = "monthly"
    ) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "mandate_id": "MNDT-MOCK-99001",
                "account_number": account_number,
                "amount": amount,
                "frequency": frequency,
                "status": "registered",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.emandate.in/register",
            headers={
                "Authorization": f"Bearer {settings.emandate_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "account_number": account_number,
                "ifsc": ifsc,
                "amount": amount,
                "frequency": frequency,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "mandate_id": data.get("mandate_id"),
                "status": data.get("status"),
                "amount": data.get("amount"),
                "frequency": data.get("frequency"),
            },
            raw_response=data,
        )
