from __future__ import annotations

from src.config import get_settings
from src.tools.external.base_client import BaseExternalClient, CreditDataResponse

settings = get_settings()


class FaceMatchClient(BaseExternalClient):
    provider_name = "face_match"

    async def _call_api(self, selfie_path: str, id_photo_path: str) -> CreditDataResponse:
        if settings.is_development:
            mock = {"match_confidence": 92.5, "is_match": True}
            return CreditDataResponse(success=True, provider=self.provider_name, data=mock, raw_response=mock)

        response = await self._make_request(
            method="POST",
            url="https://api.facematch.in/verify",
            headers={
                "Authorization": f"Bearer {settings.face_match_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "selfie_path": selfie_path,
                "id_photo_path": id_photo_path,
            },
        )
        data = response.json()
        return CreditDataResponse(
            success=True,
            provider=self.provider_name,
            data={
                "match_confidence": data.get("match_confidence"),
                "is_match": data.get("is_match"),
            },
            raw_response=data,
        )
