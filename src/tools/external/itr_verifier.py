from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class ITRVerifierClient(BaseExternalClient):
    provider_name = "itr_verifier"

    async def _call_api(self, pan: str) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "pan": pan,
                "itr_filed": True,
                "assessment_years": ["2024-25", "2023-24", "2022-23"],
                "total_income_latest": 850000,
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.incometax.gov.in/itr-verify",
            headers={
                "Authorization": f"Bearer {settings.itr_verify_api_key}",
                "Content-Type": "application/json",
            },
            json={"pan": pan},
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "pan": data.get("pan"),
                "itr_filed": data.get("itr_filed"),
                "assessment_years": data.get("assessment_years", []),
                "total_income_latest": data.get("total_income_latest"),
            },
            raw_response=data,
        )
