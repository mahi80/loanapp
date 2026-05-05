import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.auth.google_sso import build_google_auth_url, exchange_code_for_user_info


def test_build_google_auth_url():
    url = build_google_auth_url()
    assert "accounts.google.com" in url
    assert "client_id=" in url
    assert "redirect_uri=" in url
    assert "scope=" in url
    assert "response_type=code" in url


@pytest.mark.asyncio
async def test_exchange_code_returns_none_on_failure():
    with patch("src.auth.google_sso.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": "bad"}
        mock_client.post.return_value = mock_resp
        MockClient.return_value = mock_client
        result = await exchange_code_for_user_info("bad_code")
        assert result is None
