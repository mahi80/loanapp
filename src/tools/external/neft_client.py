from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class NEFTClient(BaseExternalClient):
    provider_name = "neft"

    async def _call_api(
        self, beneficiary_account: str, beneficiary_ifsc: str, amount: float, narration: str = ""
    ) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "transaction_id": "NEFT-MOCK-TX-20260413",
                "beneficiary_account": beneficiary_account,
                "amount": amount,
                "status": "completed",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.bank.in/neft/transfer",
            headers={
                "Authorization": f"Bearer {settings.neft_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "beneficiary_account": beneficiary_account,
                "beneficiary_ifsc": beneficiary_ifsc,
                "amount": amount,
                "narration": narration,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "transaction_id": data.get("transaction_id"),
                "status": data.get("status"),
                "amount": data.get("amount"),
            },
            raw_response=data,
        )
