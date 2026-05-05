from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CBSConnectorClient(BaseExternalClient):
    provider_name = "cbs"

    async def _call_api(
        self, borrower_id: str, loan_amount: float, interest_rate: float, tenure_months: int
    ) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "loan_account_id": "LA-MOCK-2026041300001",
                "borrower_id": borrower_id,
                "loan_amount": loan_amount,
                "interest_rate": interest_rate,
                "tenure_months": tenure_months,
                "status": "booked",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.cbs.bank.in/loan/book",
            headers={
                "Authorization": f"Bearer {settings.cbs_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "borrower_id": borrower_id,
                "loan_amount": loan_amount,
                "interest_rate": interest_rate,
                "tenure_months": tenure_months,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "loan_account_id": data.get("loan_account_id"),
                "status": data.get("status"),
                "emi_amount": data.get("emi_amount"),
            },
            raw_response=data,
        )
