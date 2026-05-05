from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class BankStatementAnalyzerClient(BaseExternalClient):
    provider_name = "perfios"

    async def _call_api(self, document_url: str, document_type: str = "bank_statement") -> CreditDataResponse:
        if settings.is_development:
            mock = self._load_mock("bank_statement_response")
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.perfios.com/v2/statement/upload",
            headers={
                "Authorization": f"Bearer {settings.perfios_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "documentUrl": document_url,
                "documentType": document_type,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "monthly_income": data.get("monthlyIncome", []),
                "salary_credits": data.get("salaryCredits", []),
                "recurring_debits": data.get("recurringDebits", []),
                "average_balance": data.get("averageBalance", 0),
                "cash_flow_summary": data.get("cashFlowSummary", {}),
                "bounced_cheques": data.get("bouncedCheques", 0),
            },
            raw_response=data,
        )
