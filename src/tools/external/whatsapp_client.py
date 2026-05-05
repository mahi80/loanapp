from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class WhatsAppClient(BaseExternalClient):
    provider_name = "whatsapp"

    async def _call_api(
        self, mobile: str, template_name: str, params: dict | None = None
    ) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "message_id": "WA-MOCK-33221",
                "mobile": mobile,
                "template_name": template_name,
                "status": "sent",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        payload: dict = {"mobile": mobile, "template_name": template_name}
        if params:
            payload["params"] = params

        response = await self._make_request(
            method="POST",
            url="https://api.whatsapp.business.in/send",
            headers={
                "Authorization": f"Bearer {settings.whatsapp_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "message_id": data.get("message_id"),
                "status": data.get("status"),
            },
            raw_response=data,
        )
