from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class ESignClient(BaseExternalClient):
    provider_name = "esign"

    async def _call_api(self, document_id: str, signer_name: str, signer_email: str) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "document_id": document_id,
                "signer_name": signer_name,
                "status": "sent",
                "signing_url": f"https://esign.mock.in/sign/{document_id}",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.esign.in/initiate",
            headers={
                "Authorization": f"Bearer {settings.esign_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "document_id": document_id,
                "signer_name": signer_name,
                "signer_email": signer_email,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "document_id": data.get("document_id"),
                "status": data.get("status"),
                "signing_url": data.get("signing_url"),
            },
            raw_response=data,
        )
