from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache


class Settings(BaseSettings):
    # Environment
    environment: str = "development"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://loan:loan@postgres:5432/loan_underwriting"

    # Redis
    redis_url: str = "redis://redis:6379"

    # Qdrant
    qdrant_url: str = "http://qdrant:6333"

    # LiteLLM
    litellm_base_url: str = "http://litellm:4000"

    # Azure AI (Opus - Sweden Central)
    azure_ai_api_key: str = ""
    azure_ai_api_base: str = ""
    azure_ai_chat_deployment: str = "claude-opus-4-6"
    azure_ai_api_version: str = "2024-12-01-preview"

    # Azure OpenAI (GPT-4o fallback - East US 2)
    azure_api_key: str = ""
    azure_api_base: str = ""
    azure_api_version: str = "2024-12-01-preview"
    azure_chat_deployment: str = "gpt-4o"
    azure_embed_deployment: str = "text-embedding-3-large"
    azure_embed_api_version: str = "2024-02-01"

    # Google SSO
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/api/auth/google/callback"

    # JWT — no defaults: deployment MUST set these via .env
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Azure Document Intelligence
    azure_doc_intelligence_endpoint: str = ""
    azure_doc_intelligence_key: str = ""

    # Azure Blob Storage
    azure_blob_connection_string: str = ""
    azure_blob_container: str = "loan-documents"

    # Officer auto-assign (comma-separated emails)
    officer_emails: str = "kmsb80@gmail.com,officer@demo.bank,hemantrawat246@gmail.com"

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = ""
    api_rate_limit: str = "100/minute"

    # Credit Bureau APIs
    cibil_api_key: str = ""
    experian_api_key: str = ""
    crif_api_key: str = ""
    equifax_api_key: str = ""

    # KYC APIs
    pan_verify_api_key: str = ""
    aadhaar_api_key: str = ""
    ckyc_api_key: str = ""
    face_match_api_key: str = ""
    sanctions_api_key: str = ""

    # Financial APIs
    perfios_api_key: str = ""
    setu_aa_api_key: str = ""
    gst_verify_api_key: str = ""
    itr_verify_api_key: str = ""

    # Employer
    company_registry_api_key: str = ""

    # Disbursement APIs
    esign_api_key: str = ""
    emandate_api_key: str = ""
    neft_api_key: str = ""
    penny_drop_api_key: str = ""
    cbs_api_key: str = ""

    # Notification APIs
    sms_api_key: str = ""
    email_api_key: str = ""
    whatsapp_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _validate_secrets(self):
        weak = {"", "change-me-in-production"}
        if self.jwt_secret_key in weak:
            raise ValueError("JWT_SECRET_KEY must be set in .env — refusing to start with empty/default secret")
        if self.api_secret_key in weak:
            raise ValueError("API_SECRET_KEY must be set in .env — refusing to start with empty/default secret")
        return self

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
