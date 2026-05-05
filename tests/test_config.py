import os
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///test.db")

from src.config import get_settings


def test_settings_has_google_sso_fields():
    s = get_settings()
    assert hasattr(s, "google_client_id")
    assert hasattr(s, "google_client_secret")
    assert hasattr(s, "google_redirect_uri")


def test_settings_has_jwt_fields():
    s = get_settings()
    assert hasattr(s, "jwt_secret_key")
    assert hasattr(s, "jwt_algorithm")
    assert hasattr(s, "jwt_expire_minutes")


def test_settings_has_doc_intelligence_fields():
    s = get_settings()
    assert hasattr(s, "azure_doc_intelligence_endpoint")
    assert hasattr(s, "azure_doc_intelligence_key")


def test_settings_has_blob_storage_fields():
    s = get_settings()
    assert hasattr(s, "azure_blob_connection_string")
    assert hasattr(s, "azure_blob_container")
