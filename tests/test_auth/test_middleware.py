import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from src.auth.middleware import get_current_user, require_role
from src.auth.jwt_handler import create_access_token


@pytest.mark.asyncio
async def test_get_current_user_no_header():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(authorization="")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(authorization="Bearer invalid.token")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_officer_role_with_customer():
    checker = require_role("officer")
    mock_user = MagicMock()
    mock_user.role.value = "customer"
    with pytest.raises(HTTPException) as exc:
        await checker(mock_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_officer_role_with_officer():
    checker = require_role("officer")
    mock_user = MagicMock()
    mock_user.role.value = "officer"
    result = await checker(mock_user)
    assert result == mock_user
