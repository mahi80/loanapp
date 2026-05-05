from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class EmailClient(BaseExternalClient):
    provider_name = "email"

    async def _call_api(
        self, to: str, subject: str, body: str, from_email: str = "noreply@loanapp.com"
    ) -> CreditDataResponse:
        if settings.is_development:
            mock = {
                "message_id": "EMAIL-MOCK-45678",
                "to": to,
                "subject": subject,
                "status": "delivered",
            }
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.emailservice.in/send",
            headers={
                "Authorization": f"Bearer {settings.email_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "to": to,
                "from": from_email,
                "subject": subject,
                "body": body,
            },
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
