from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class AccountAggregatorClient(BaseExternalClient):
    provider_name = "setu_aa"

    async def _call_api(self, consent_id: str, fi_data_range_from: str, fi_data_range_to: str) -> CreditDataResponse:
        if settings.is_development:
            mock = self._load_mock("account_aggregator_response")
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://aa.setu.co/v2/data/fetch",
            headers={
                "Authorization": f"Bearer {settings.setu_aa_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "consentId": consent_id,
                "DataRange": {
                    "from": fi_data_range_from,
                    "to": fi_data_range_to,
                },
                "format": "json",
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "accounts": data.get("accounts", []),
                "deposits": data.get("deposits", []),
                "recurring_transactions": data.get("recurringTransactions", []),
                "transaction_summary": data.get("transactionSummary", {}),
            },
            raw_response=data,
        )
