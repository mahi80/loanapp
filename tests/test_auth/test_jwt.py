import uuid
from src.auth.jwt_handler import create_access_token, decode_access_token


def test_create_and_decode_token():
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id=user_id, email="test@example.com", role="customer")
    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "customer"


def test_decode_invalid_token():
    payload = decode_access_token("invalid.token.here")
    assert payload is None


def test_token_contains_expiry():
    token = create_access_token(user_id="123", email="a@b.com", role="customer")
    payload = decode_access_token(token)
    assert "exp" in payload
