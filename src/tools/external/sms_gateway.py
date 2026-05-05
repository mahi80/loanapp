from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class SMSGatewayClient(BaseExternalClient):
    provider_name = "sms_gateway"

    async def _call_api(self, mobile: str, message: str, template_id: str = "") -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "message_id": "SMS-MOCK-78901",
                "mobile": mobile,
                "status": "sent",
                "template_id": template_id,
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        payload: dict = {"mobile": mobile, "message": message}
        if template_id:
            payload["template_id"] = template_id

        response = await self._make_request(
            method="POST",
            url="https://api.smsgateway.in/send",
            headers={
                "Authorization": f"Bearer {settings.sms_api_key}",
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
