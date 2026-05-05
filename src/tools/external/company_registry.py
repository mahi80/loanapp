from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class CompanyRegistryClient(BaseExternalClient):
    provider_name = "company_registry"

    async def _call_api(self, company_name: str, cin: str | None = None) -> CreditDataResponse:
        if settings.is_development:
            mock = {"registered": True, "category": "MNC"}
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        payload: dict = {"company_name": company_name}
        if cin:
            payload["cin"] = cin

        response = await self._make_request(
            method="POST",
            url="https://api.mca.gov.in/company-lookup",
            headers={
                "Authorization": f"Bearer {settings.company_registry_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "registered": data.get("registered"),
                "category": data.get("category"),
                "cin": data.get("cin"),
                "status": data.get("status"),
            },
            raw_response=data,
        )
