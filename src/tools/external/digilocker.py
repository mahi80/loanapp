from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class DigiLockerClient(BaseExternalClient):
    provider_name = "digilocker"

    async def _call_api(self, aadhaar_linked_token: str, doc_type: str) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "doc_type": doc_type,
                "document_id": "DL-MOCK-12345",
                "status": "available",
                "issuer": "Government of India",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.digilocker.gov.in/fetch-document",
            headers={
                "Authorization": f"Bearer {settings.aadhaar_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "aadhaar_linked_token": aadhaar_linked_token,
                "doc_type": doc_type,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "doc_type": data.get("doc_type"),
                "document_id": data.get("document_id"),
                "status": data.get("status"),
                "issuer": data.get("issuer"),
            },
            raw_response=data,
        )
