# V4 Backend Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace EvoAgentX with LangGraph, add Google SSO auth, build SSE streaming chat endpoint, fix data model issues — producing a fully functional backend that the frontend plan will connect to.

**Architecture:** FastAPI backend with LangGraph StateGraph (13 nodes, PostgreSQL checkpointing), Google SSO → JWT auth, SSE streaming endpoint that emits Vercel AI SDK-compatible data stream protocol events. All existing tools (DTI calculator, risk scorer, etc.) are bound as LangGraph tools.

**Tech Stack:** Python 3.12, FastAPI, LangGraph, langchain-openai, PostgreSQL (Azure), Redis (Azure), python-jose (JWT), authlib (Google OAuth), structlog

**Spec:** `docs/superpowers/specs/2026-04-16-v4-langgraph-sso-frontend-design.md`

---

## Phase A: Foundation

### Task 1: Update Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Update requirements.txt**

Replace the full contents of `requirements.txt`:

```text
# LangGraph & LLM
langgraph>=0.4.0
langgraph-checkpoint-postgres>=2.0.0
langchain-openai>=0.3.0
langchain-core>=0.3.0

# Web Framework
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-multipart>=0.0.12

# Database
sqlalchemy[asyncio]>=2.0.35
asyncpg>=0.30.0
alembic>=1.14.0
psycopg2-binary>=2.9.10
psycopg[binary]>=3.2.0

# Cache
redis>=5.2.0

# Vector Store
qdrant-client>=1.12.0

# Data Validation
pydantic>=2.10.0
pydantic-settings>=2.6.0

# HTTP Client
httpx>=0.28.0

# Document Storage
azure-storage-blob>=12.24.0

# OCR / Document Intelligence
azure-ai-documentintelligence>=1.0.0

# Auth
authlib>=1.4.0
python-jose[cryptography]>=3.3.0

# Monitoring
prometheus-client>=0.21.0
prometheus-fastapi-instrumentator>=7.0.0

# Utilities
eval_type_backport>=0.2.0
python-dotenv>=1.0.1
tenacity>=9.0.0
structlog>=24.4.0
orjson>=3.10.0

# PDF Generation
reportlab>=4.1.0

# Document forensics
pikepdf>=8.0.0
Pillow>=10.4.0

# Testing
pytest>=8.3.0
pytest-asyncio>=0.24.0
pytest-cov>=6.0.0
httpx>=0.28.0
factory-boy>=3.3.0
aiosqlite>=0.20.0
```

- [ ] **Step 2: Install new dependencies**

Run: `pip install -r requirements.txt`

- [ ] **Step 3: Verify imports work**

Run: `python -c "from langgraph.graph import StateGraph; from langchain_openai import AzureChatOpenAI; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: swap evoagentx for langgraph, clean up dependencies"
```

---

### Task 2: Update Config with New Settings

**Files:**
- Modify: `src/config.py`

- [ ] **Step 1: Write test for new config fields**

Create `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — missing attributes

- [ ] **Step 3: Update config.py with new fields**

Add these fields to the `Settings` class in `src/config.py`, after the existing API fields (line ~92):

```python
    # Google SSO
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/api/auth/google/callback"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Azure Document Intelligence
    azure_doc_intelligence_endpoint: str = ""
    azure_doc_intelligence_key: str = ""

    # Azure Blob Storage
    azure_blob_connection_string: str = ""
    azure_blob_container: str = "loan-documents"

    # Frontend
    frontend_url: str = "http://localhost:3000"
```

Also remove these obsolete fields:
- `azure_form_recognizer_endpoint`
- `azure_form_recognizer_key`
- `document_store_endpoint`
- `document_store_type`
- `minio_access_key`
- `minio_secret_key`
- `mem0_api_key`
- `mem0_project_name`
- `mem0_vector_store`
- `mem0_collection_name`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: add Google SSO, JWT, Doc Intelligence, Blob Storage config fields"
```

---

### Task 3: Data Model — New Tables + Fixes

**Files:**
- Modify: `src/db/models.py`
- Create: `tests/test_db/test_new_models.py`

- [ ] **Step 1: Write tests for new models**

Create `tests/test_db/test_new_models.py`:

```python
import uuid
from datetime import datetime

from src.db.models import User, Conversation, ChatMessage, UserRole


def test_user_model_fields():
    user = User(
        google_id="google_123",
        email="test@example.com",
        name="Test User",
        role=UserRole.CUSTOMER,
    )
    assert user.google_id == "google_123"
    assert user.role == UserRole.CUSTOMER


def test_conversation_model_fields():
    conv = Conversation(
        user_id=uuid.uuid4(),
        status="active",
        current_phase="intake",
        langgraph_thread_id="thread_abc",
    )
    assert conv.status == "active"
    assert conv.langgraph_thread_id == "thread_abc"


def test_chat_message_model_fields():
    msg = ChatMessage(
        conversation_id=uuid.uuid4(),
        role="assistant",
        content="Hello",
        tool_name=None,
        tool_data=None,
    )
    assert msg.role == "assistant"
    assert msg.content == "Hello"


def test_user_role_enum():
    assert UserRole.CUSTOMER.value == "customer"
    assert UserRole.OFFICER.value == "officer"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db/test_new_models.py -v`
Expected: FAIL — `User`, `Conversation`, `ChatMessage`, `UserRole` not found

- [ ] **Step 3: Add new models and enums to src/db/models.py**

Add `UserRole` enum after the existing enums section (~line 130):

```python
class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    OFFICER = "officer"


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
```

Add `User` model after the `Base` class and enums:

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id: Mapped[str] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    applications: Mapped[list["Application"]] = relationship(back_populates="user")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
```

Add `Conversation` model:

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    langgraph_thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="conversations")
    application: Mapped[Optional["Application"]] = relationship()
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
```

Add `ChatMessage` model:

```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id")
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
```

Add `user_id` FK and `reference_number` to `Application`:

```python
# In Application class, add after existing fields:
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reference_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="applications")
```

Change all money-related `Float` columns to use `Numeric`:

```python
from sqlalchemy import Numeric

# Application.loan_amount:
    loan_amount: Mapped[float] = mapped_column(Numeric(15, 2))

# CreditDecision fields:
    interest_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    processing_fee: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    emi_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)

# Offer.total_cost:
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)

# Disbursement.amount:
    amount: Mapped[float] = mapped_column(Numeric(15, 2))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db/test_new_models.py -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to check nothing broke**

Run: `pytest tests/ -v --tb=short -x`
Expected: All existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add src/db/models.py tests/test_db/test_new_models.py
git commit -m "feat: add User, Conversation, ChatMessage models; fix Float→Numeric for money"
```

---

### Task 4: Alembic Initial Migration

**Files:**
- Modify: `alembic/env.py`
- Create: `alembic/versions/001_v4_initial.py`

- [ ] **Step 1: Verify alembic env.py imports our models**

Read `alembic/env.py` and ensure it has:
```python
from src.db.models import Base
target_metadata = Base.metadata
```

If not, update it.

- [ ] **Step 2: Update alembic.ini sqlalchemy.url**

The `alembic.ini` should use the sync database URL. Verify the `sqlalchemy.url` line points to the correct database or is overridden by `env.py`.

- [ ] **Step 3: Generate migration**

Run: `alembic revision --autogenerate -m "v4 initial schema with users conversations chat_messages"`

- [ ] **Step 4: Review the generated migration file**

Read the generated file in `alembic/versions/` and verify it creates:
- `users` table
- `conversations` table
- `chat_messages` table
- Adds `user_id` and `reference_number` to `applications`
- Changes `Float` → `Numeric` columns

- [ ] **Step 5: Commit**

```bash
git add alembic/
git commit -m "feat: add alembic migration for v4 schema"
```

---

## Phase B: Authentication

### Task 5: JWT Handler

**Files:**
- Create: `src/auth/__init__.py`
- Create: `src/auth/jwt_handler.py`
- Create: `tests/test_auth/__init__.py`
- Create: `tests/test_auth/test_jwt.py`

- [ ] **Step 1: Write tests for JWT handler**

Create `tests/test_auth/__init__.py` (empty).

Create `tests/test_auth/test_jwt.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_auth/test_jwt.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement JWT handler**

Create `src/auth/__init__.py` (empty).

Create `src/auth/jwt_handler.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, UTC

from jose import jwt, JWTError
import structlog

from src.config import get_settings

logger = structlog.get_logger()


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Create a JWT access token with user claims."""
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns claims dict or None if invalid."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        logger.warning("jwt_decode_failed")
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_auth/test_jwt.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auth/ tests/test_auth/
git commit -m "feat: add JWT token creation and validation"
```

---

### Task 6: Google SSO Backend

**Files:**
- Create: `src/auth/google_sso.py`
- Create: `src/api/routes/auth.py`
- Create: `tests/test_auth/test_google_sso.py`

- [ ] **Step 1: Write tests for Google SSO utilities**

Create `tests/test_auth/test_google_sso.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
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
        mock_client.post.return_value = AsyncMock(status_code=400, json=lambda: {"error": "bad"})
        MockClient.return_value = mock_client

        result = await exchange_code_for_user_info("bad_code")
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_auth/test_google_sso.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement Google SSO utility**

Create `src/auth/google_sso.py`:

```python
from __future__ import annotations

from urllib.parse import urlencode

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def build_google_auth_url() -> str:
    """Build the Google OAuth2 authorization URL."""
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_user_info(code: str) -> dict | None:
    """Exchange authorization code for Google user info.

    Returns dict with keys: google_id, email, name, picture or None on failure.
    """
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            logger.error("google_token_exchange_failed", status=token_resp.status_code)
            return None

        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            logger.error("google_no_access_token")
            return None

        # Fetch user info
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            logger.error("google_userinfo_failed", status=userinfo_resp.status_code)
            return None

        data = userinfo_resp.json()
        return {
            "google_id": data["id"],
            "email": data["email"],
            "name": data.get("name", ""),
            "picture": data.get("picture"),
        }
```

- [ ] **Step 4: Implement auth route**

Create `src/api/routes/auth.py`:

```python
from __future__ import annotations

from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import User, UserRole
from src.auth.google_sso import build_google_auth_url, exchange_code_for_user_info
from src.auth.jwt_handler import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/google")
async def google_login():
    """Redirect to Google OAuth consent screen."""
    return RedirectResponse(url=build_google_auth_url())


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback. Creates user if needed, returns JWT."""
    user_info = await exchange_code_for_user_info(code)
    if user_info is None:
        raise HTTPException(status_code=401, detail="Google authentication failed")

    # Find or create user
    result = await db.execute(
        select(User).where(User.google_id == user_info["google_id"])
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            google_id=user_info["google_id"],
            email=user_info["email"],
            name=user_info["name"],
            picture_url=user_info.get("picture"),
            role=UserRole.CUSTOMER,
        )
        db.add(user)
        await db.flush()

    user.last_login_at = datetime.now(UTC)

    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )

    # Redirect to frontend with token
    from src.config import get_settings
    settings = get_settings()
    return RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback?token={token}"
    )


@router.get("/me")
async def get_current_user(user=Depends(get_current_user_dep)):
    """Get current authenticated user info."""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "picture_url": user.picture_url,
    }


async def get_current_user_dep(
    authorization: str = "",
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: extract and validate JWT, return User."""
    from src.auth.jwt_handler import decode_access_token
    from fastapi import Header

    # This will be wired properly in the middleware task
    raise HTTPException(status_code=401, detail="Not implemented yet")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_auth/test_google_sso.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/auth/google_sso.py src/api/routes/auth.py tests/test_auth/test_google_sso.py
git commit -m "feat: add Google SSO login flow and auth routes"
```

---

### Task 7: Auth Middleware

**Files:**
- Create: `src/auth/middleware.py`
- Create: `tests/test_auth/test_middleware.py`

- [ ] **Step 1: Write tests for auth dependency**

Create `tests/test_auth/test_middleware.py`:

```python
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


def test_require_officer_role_with_customer():
    checker = require_role("officer")
    mock_user = MagicMock()
    mock_user.role.value = "customer"
    with pytest.raises(HTTPException) as exc:
        checker(mock_user)
    assert exc.value.status_code == 403


def test_require_officer_role_with_officer():
    checker = require_role("officer")
    mock_user = MagicMock()
    mock_user.role.value = "officer"
    result = checker(mock_user)
    assert result == mock_user
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_auth/test_middleware.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement auth middleware**

Create `src/auth/middleware.py`:

```python
from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import User
from src.auth.jwt_handler import decode_access_token


async def get_current_user(
    authorization: str = Header(""),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract JWT from Authorization header, validate, return User."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_role(role: str):
    """Returns a dependency that checks the user has the required role."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value != role:
            raise HTTPException(status_code=403, detail=f"Requires {role} role")
        return user
    return checker
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_auth/test_middleware.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auth/middleware.py tests/test_auth/test_middleware.py
git commit -m "feat: add JWT auth middleware with role-based access control"
```

---

## Phase C: LangGraph Core

### Task 8: LangGraph State Schema

**Files:**
- Create: `src/graph/__init__.py`
- Create: `src/graph/state.py`
- Create: `tests/test_graph/__init__.py`
- Create: `tests/test_graph/test_state.py`

- [ ] **Step 1: Write tests for state schema**

Create `tests/test_graph/__init__.py` (empty).

Create `tests/test_graph/test_state.py`:

```python
from src.graph.state import LoanApplicationState


def test_state_has_required_keys():
    state = LoanApplicationState(
        messages=[],
        user_id="u1",
        application_id="",
        reference_number="",
        current_phase="intake",
        conversation_complete=False,
        needs_human_review=False,
    )
    assert state["user_id"] == "u1"
    assert state["current_phase"] == "intake"
    assert state["messages"] == []


def test_state_has_document_tracking():
    state = LoanApplicationState(
        messages=[],
        user_id="u1",
        application_id="",
        reference_number="",
        current_phase="intake",
        conversation_complete=False,
        needs_human_review=False,
        documents_uploaded={},
        documents_required=[],
        documents_pending=[],
    )
    assert state["documents_uploaded"] == {}
    assert state["documents_required"] == []


def test_state_has_scoring_fields():
    state = LoanApplicationState(
        messages=[],
        user_id="u1",
        application_id="",
        reference_number="",
        current_phase="intake",
        conversation_complete=False,
        needs_human_review=False,
        composite_score=0,
        risk_category="",
    )
    assert state["composite_score"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph/test_state.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement state schema**

Create `src/graph/__init__.py` (empty).

Create `src/graph/state.py`:

```python
from __future__ import annotations

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class LoanApplicationState(TypedDict, total=False):
    """Full state for the loan application LangGraph.

    Uses ``total=False`` so only required fields must be set at init.
    The ``messages`` field uses LangGraph's ``add_messages`` reducer
    to automatically merge message lists.
    """

    # Chat history (reducer: append-merge)
    messages: Annotated[list, add_messages]

    # Identifiers
    user_id: str
    application_id: str
    reference_number: str

    # Applicant info
    applicant_name: str
    pan_number: str
    dob: str
    mobile: str
    email: str
    employment_type: str
    monthly_income: float
    employer: str
    city: str
    state: str
    loan_amount: float
    loan_type: str
    tenure_months: int

    # Documents
    documents_uploaded: dict       # {doc_type: {path, extracted_data, verified}}
    documents_required: list[str]
    documents_pending: list[str]

    # Verification results
    pan_verified: bool
    aadhaar_verified: bool
    face_match_score: float
    bureau_reports: dict
    income_verified: dict
    employer_verified: bool

    # Scoring
    four_c_scores: dict
    dti_ratio: float
    stability_score: float
    fraud_flags: list[str]
    composite_score: int
    risk_category: str

    # Decision
    compliance_status: str
    pricing: dict
    decision: str
    decision_rationale: str
    confidence: float
    offer: dict

    # Flow control
    current_phase: str
    needs_human_review: bool
    officer_decision: str
    conversation_complete: bool
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph/test_state.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/graph/ tests/test_graph/
git commit -m "feat: add LangGraph LoanApplicationState schema"
```

---

### Task 9: Dynamic Prompt Builder

**Files:**
- Create: `src/graph/prompts/__init__.py`
- Create: `src/graph/prompts/builder.py`
- Create: `tests/test_graph/test_prompts.py`

- [ ] **Step 1: Write tests for prompt builder**

Create `tests/test_graph/test_prompts.py`:

```python
from src.graph.prompts.builder import build_prompt


def test_intake_prompt_contains_role():
    prompt = build_prompt("intake", {})
    assert "loan application" in prompt.lower()


def test_intake_prompt_with_applicant_context():
    state = {"applicant_name": "Raj Kumar", "employment_type": "salaried"}
    prompt = build_prompt("intake", state)
    assert "Raj Kumar" in prompt
    assert "salaried" in prompt


def test_doc_collection_prompt_includes_required_docs():
    state = {"employment_type": "salaried", "documents_required": ["pan_card", "aadhaar", "payslip"]}
    prompt = build_prompt("doc_collection", state)
    assert "pan_card" in prompt or "PAN" in prompt


def test_unknown_phase_returns_generic():
    prompt = build_prompt("unknown_phase", {})
    assert len(prompt) > 0


def test_risk_assessment_prompt_includes_bureau():
    state = {"bureau_reports": {"cibil": {"score": 750}}}
    prompt = build_prompt("risk_assessment", state)
    assert "750" in prompt or "bureau" in prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph/test_prompts.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement prompt builder**

Create `src/graph/prompts/__init__.py` (empty).

Create `src/graph/prompts/builder.py`:

```python
from __future__ import annotations

import json


_BASE_PROMPTS: dict[str, str] = {
    "intake": (
        "You are a friendly, professional loan officer at a leading Indian bank. "
        "Guide the customer through their personal loan application. Be warm but efficient.\n\n"
        "Your job in this phase:\n"
        "1. Greet the customer and explain the process briefly.\n"
        "2. Collect basic information by calling the collect_basic_info tool.\n"
        "3. Once info is collected, run the eligibility check.\n"
        "4. If eligible, ask for loan details (amount, tenure) via collect_loan_details tool.\n"
        "5. If not eligible, explain why clearly and end the conversation.\n"
    ),
    "doc_collection": (
        "You are a loan officer helping the customer upload required documents.\n\n"
        "Your job in this phase:\n"
        "1. Tell the customer which documents are needed based on their profile.\n"
        "2. Ask for one document at a time using the upload_document tool.\n"
        "3. After each upload, confirm receipt and move to the next document.\n"
        "4. Once all required documents are uploaded, transition to verification.\n"
    ),
    "doc_verification": (
        "You are verifying uploaded documents using Azure Document Intelligence.\n\n"
        "Your job:\n"
        "1. Extract data from each uploaded document.\n"
        "2. Cross-validate names, dates, and IDs across documents.\n"
        "3. If a document is unreadable or has issues, ask the customer to re-upload.\n"
        "4. Show the customer a verification summary for each document.\n"
    ),
    "bureau_pull": (
        "You are a credit bureau specialist.\n"
        "Pull reports from CIBIL, Experian, CRIF, and Equifax.\n"
        "Consolidate the scores and report data.\n"
        "This phase runs in the background — no customer interaction needed.\n"
    ),
    "income_verification": (
        "You are an income verification specialist.\n"
        "Verify income from bank statements, payslips, and employer data.\n"
        "For salaried: cross-check salary credits with payslip amounts.\n"
        "For self-employed: estimate income from bank statement patterns and ITR/GST.\n"
        "Verify the employer exists via company registry.\n"
        "This phase runs in the background — no customer interaction needed.\n"
    ),
    "risk_assessment": (
        "You are a credit risk analyst using the 4Cs framework.\n"
        "Evaluate Character (repayment behavior), Capacity (income vs obligations), "
        "Capital (assets/savings), and Collateral (neutral 50 for unsecured).\n"
        "Calculate DTI ratio and income stability score.\n"
        "Scan for hidden debts not in bureau report.\n"
    ),
    "fraud_detection": (
        "You are a fraud detection specialist.\n"
        "Check for identity fraud: PAN-name mismatch, Aadhaar-face mismatch, "
        "duplicate PAN, age inconsistencies across documents.\n"
        "Check for document tampering: metadata anomalies, font inconsistencies.\n"
        "Calculate fraud risk score 0-100.\n"
    ),
    "score_aggregation": (
        "You are the score aggregation engine.\n"
        "Combine 4C scores, income stability, debt burden, and fraud flags "
        "into a composite credit score (300-900).\n"
        "Apply fraud penalties. Determine risk category.\n"
    ),
    "compliance": (
        "You are a regulatory compliance specialist for Indian lending.\n"
        "Validate against RBI guidelines, fair lending rules.\n"
        "Apply the 4/5ths rule for disparate impact.\n"
        "Verify KYC requirements are met.\n"
        "Check interest rate is within RBI regulatory limits.\n"
    ),
    "pricing": (
        "You are a loan pricing specialist.\n"
        "Look up base interest rate from rate card using risk category.\n"
        "Apply customer segment adjustments.\n"
        "Calculate processing fee, insurance premium, total cost, and EMI.\n"
    ),
    "decision": (
        "You are the final credit decision maker.\n"
        "Rules:\n"
        "- APPROVED: score >= 700, DTI <= 0.50, compliance pass, no fraud, confidence >= 0.8\n"
        "- CONDITIONAL: score 600-699, or minor compliance conditions\n"
        "- DENIED: score < 450, OR DTI > 0.65, OR compliance fail, OR fraud detected\n"
        "- ESCALATED: score 450-599 with low confidence, OR compliance review needed\n\n"
        "Provide decision with full reasoning and confidence level.\n"
    ),
    "offer_generation": (
        "You are generating the loan offer for the customer.\n"
        "Present the offer terms clearly: interest rate, EMI amount, tenure, "
        "processing fee, total cost of credit.\n"
        "Use the show_offer tool to render a beautiful offer card.\n"
    ),
    "human_review": (
        "The application has been escalated for human review.\n"
        "Inform the customer that their application is under review by the credit team.\n"
        "Provide the application reference number and expected timeline (2-3 business days).\n"
    ),
}


def build_prompt(phase: str, state: dict) -> str:
    """Assemble a dynamic prompt from base role + current application context."""
    base = _BASE_PROMPTS.get(phase, f"You are a loan processing specialist handling the {phase} phase.\n")

    context_parts: list[str] = []

    # Add applicant context if available
    if state.get("applicant_name"):
        context_parts.append(f"Applicant: {state['applicant_name']}")
    if state.get("employment_type"):
        context_parts.append(f"Employment: {state['employment_type']}")
    if state.get("monthly_income"):
        context_parts.append(f"Monthly Income: {state['monthly_income']}")
    if state.get("loan_amount"):
        context_parts.append(f"Loan Amount: {state['loan_amount']}")
    if state.get("tenure_months"):
        context_parts.append(f"Tenure: {state['tenure_months']} months")

    # Add document status
    if state.get("documents_required"):
        context_parts.append(f"Required Documents: {', '.join(state['documents_required'])}")
    if state.get("documents_pending"):
        context_parts.append(f"Pending Documents: {', '.join(state['documents_pending'])}")
    if state.get("documents_uploaded"):
        uploaded = list(state["documents_uploaded"].keys())
        context_parts.append(f"Uploaded Documents: {', '.join(uploaded)}")

    # Add scoring context for later phases
    if state.get("bureau_reports"):
        context_parts.append(f"Bureau Reports: {json.dumps(state['bureau_reports'], default=str)}")
    if state.get("composite_score"):
        context_parts.append(f"Composite Score: {state['composite_score']}")
    if state.get("risk_category"):
        context_parts.append(f"Risk Category: {state['risk_category']}")
    if state.get("dti_ratio"):
        context_parts.append(f"DTI Ratio: {state['dti_ratio']}")
    if state.get("fraud_flags"):
        context_parts.append(f"Fraud Flags: {', '.join(state['fraud_flags'])}")

    # Add reference number if assigned
    if state.get("reference_number"):
        context_parts.append(f"Application Reference: {state['reference_number']}")

    # Assemble
    prompt = base
    if context_parts:
        prompt += "\n--- Current Application Context ---\n"
        prompt += "\n".join(context_parts)
        prompt += "\n---\n"

    return prompt
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph/test_prompts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/graph/prompts/ tests/test_graph/test_prompts.py
git commit -m "feat: add dynamic prompt builder for LangGraph nodes"
```

---

### Task 10: LangGraph Tool Definitions

**Files:**
- Create: `src/graph/tools.py`
- Create: `tests/test_graph/test_tools.py`

- [ ] **Step 1: Write tests for LangGraph tool wrappers**

Create `tests/test_graph/test_tools.py`:

```python
from src.graph.tools import (
    check_eligibility_tool,
    calculate_dti_tool,
    calculate_risk_score_tool,
    score_four_cs_tool,
    lookup_rate_tool,
    generate_emi_schedule_tool,
    check_negative_list_tool,
    aggregate_scores_tool,
    calculate_volatility_tool,
    scan_hidden_debts_tool,
    check_bias_tool,
    CUSTOMER_FACING_TOOLS,
    BACKEND_TOOLS,
)


def test_eligibility_tool_callable():
    result = check_eligibility_tool.invoke({
        "age": 30,
        "monthly_income": 50000,
        "city": "Mumbai",
        "loan_amount": 500000,
    })
    assert result["eligible"] is True


def test_eligibility_tool_rejects_underage():
    result = check_eligibility_tool.invoke({
        "age": 18,
        "monthly_income": 50000,
        "city": "Mumbai",
        "loan_amount": 500000,
    })
    assert result["eligible"] is False


def test_dti_tool_callable():
    result = calculate_dti_tool.invoke({
        "monthly_income": 100000,
        "existing_emis": 20000,
        "proposed_emi": 15000,
    })
    assert "dti_ratio" in result
    assert result["dti_ratio"] > 0


def test_customer_facing_tools_list():
    assert len(CUSTOMER_FACING_TOOLS) >= 3


def test_backend_tools_list():
    assert len(BACKEND_TOOLS) >= 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph/test_tools.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement tool wrappers**

Create `src/graph/tools.py`:

```python
"""LangGraph tool definitions.

Wraps existing internal tools as LangChain @tool functions so LangGraph
nodes can call them. Split into two groups:

- CUSTOMER_FACING_TOOLS: emit inline UI (forms, uploads, cards)
- BACKEND_TOOLS: run computations without customer interaction
"""
from __future__ import annotations

from langchain_core.tools import tool

from src.tools.internal.eligibility_rules import check_eligibility
from src.tools.internal.dti_calculator import calculate_dti, estimate_emi
from src.tools.internal.risk_scorer import calculate_risk_score
from src.tools.internal.four_c_scorer import score_four_cs
from src.tools.internal.rate_card_engine import lookup_rate
from src.tools.internal.emi_scheduler import generate_emi_schedule
from src.tools.internal.negative_list import check_negative_list
from src.tools.internal.weighted_aggregator import aggregate_scores
from src.tools.internal.volatility_calculator import calculate_volatility
from src.tools.internal.hidden_debt_scanner import scan_hidden_debts
from src.tools.internal.bias_detector import check_bias


# -- Customer-facing tools (render inline UI) --------------------------------

@tool
def collect_basic_info(placeholder: str = "") -> dict:
    """Render an inline form to collect applicant basic information.

    Call this when you need to collect: name, PAN, DOB, mobile, email,
    employment type, monthly income, employer, city.
    The frontend will render a form card. Returns empty dict as the form
    submission comes back as a user message.
    """
    return {"tool": "collect_basic_info", "action": "render_form"}


@tool
def collect_loan_details(placeholder: str = "") -> dict:
    """Render an inline form to collect loan details.

    Call this when you need: loan amount, tenure (months), loan type.
    """
    return {"tool": "collect_loan_details", "action": "render_form"}


@tool
def upload_document(document_type: str, label: str) -> dict:
    """Render an inline document upload widget.

    Args:
        document_type: One of pan_card, aadhaar, bank_statement, payslip,
                       form_16, itr, gst_certificate, selfie
        label: Human-readable label for the upload widget
    """
    return {"tool": "upload_document", "document_type": document_type, "label": label}


@tool
def show_verification(document_type: str, status: str, extracted_data: dict, message: str) -> dict:
    """Show a document verification result card in the chat.

    Args:
        document_type: The type of document verified
        status: 'verified' or 'failed'
        extracted_data: Key fields extracted from the document
        message: Human-readable verification message
    """
    return {
        "tool": "show_verification",
        "document_type": document_type,
        "status": status,
        "extracted_data": extracted_data,
        "message": message,
    }


@tool
def show_progress(step: int, total: int, label: str) -> dict:
    """Show a progress tracker in the chat.

    Args:
        step: Current step number
        total: Total number of steps
        label: Description of current step
    """
    return {"tool": "show_progress", "step": step, "total": total, "label": label}


@tool
def show_offer(
    interest_rate: float,
    emi_amount: float,
    tenure_months: int,
    processing_fee: float,
    total_cost: float,
    loan_amount: float,
) -> dict:
    """Show the loan offer card to the customer.

    Args:
        interest_rate: Annual interest rate percentage
        emi_amount: Monthly EMI amount
        tenure_months: Loan tenure in months
        processing_fee: One-time processing fee
        total_cost: Total cost of credit
        loan_amount: Approved loan amount
    """
    return {
        "tool": "show_offer",
        "interest_rate": interest_rate,
        "emi_amount": emi_amount,
        "tenure_months": tenure_months,
        "processing_fee": processing_fee,
        "total_cost": total_cost,
        "loan_amount": loan_amount,
    }


@tool
def show_decision(decision: str, reasons: list[str], confidence: float) -> dict:
    """Show the credit decision card to the customer.

    Args:
        decision: One of 'approved', 'conditional', 'denied', 'escalated'
        reasons: List of reasons or conditions
        confidence: Decision confidence 0-1
    """
    return {
        "tool": "show_decision",
        "decision": decision,
        "reasons": reasons,
        "confidence": confidence,
    }


# -- Backend computation tools (no customer UI) -----------------------------

@tool
def check_eligibility_tool(age: int, monthly_income: float, city: str, loan_amount: float) -> dict:
    """Check basic eligibility for a personal loan.

    Age must be 21-58, minimum monthly income 15000, max loan is 60x income.
    """
    return check_eligibility(age, monthly_income, city, loan_amount)


@tool
def calculate_dti_tool(
    monthly_income: float,
    existing_emis: float,
    proposed_emi: float,
    credit_card_outstanding: float = 0,
    other_obligations: float = 0,
) -> dict:
    """Calculate Debt-to-Income ratio."""
    return calculate_dti(monthly_income, existing_emis, proposed_emi,
                         credit_card_outstanding, other_obligations)


@tool
def estimate_emi_tool(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Calculate EMI using standard formula."""
    return estimate_emi(principal, annual_rate, tenure_months)


@tool
def calculate_risk_score_tool(
    bureau_score: int | None,
    dti_ratio: float,
    income_stability: float,
    employment_type: str,
    loan_amount: float,
    existing_obligations: float,
    enquiry_count: int = 0,
    delinquency_count: int = 0,
) -> dict:
    """Calculate composite risk score from multiple factors."""
    return calculate_risk_score(bureau_score, dti_ratio, income_stability,
                                employment_type, loan_amount, existing_obligations,
                                enquiry_count, delinquency_count)


@tool
def score_four_cs_tool(
    bureau_score: int,
    repayment_history: float,
    monthly_income: float,
    total_obligations: float,
    assets_value: float,
    savings_balance: float,
) -> dict:
    """Evaluate the 4-C credit framework. Returns character, capacity, capital, collateral scores."""
    return score_four_cs(bureau_score, repayment_history, monthly_income,
                         total_obligations, assets_value, savings_balance)


@tool
def lookup_rate_tool(risk_category: str, loan_type: str = "personal", score: int = 0) -> dict:
    """Look up interest rate, processing fee, insurance from rate card."""
    return lookup_rate(risk_category, loan_type, score)


@tool
def generate_emi_schedule_tool(
    principal: float, annual_rate: float, tenure_months: int, start_date: str | None = None
) -> dict:
    """Generate full amortization EMI schedule."""
    return generate_emi_schedule(principal, annual_rate, tenure_months, start_date)


@tool
def check_negative_list_tool(entity_name: str, list_type: str = "individual") -> dict:
    """Check whether entity appears in negative/blacklist."""
    return check_negative_list(entity_name, list_type)


@tool
def aggregate_scores_tool(
    scores: dict, weights: dict, fraud_flags: list[str] | None = None
) -> dict:
    """Produce composite score 300-900 from weighted components."""
    return aggregate_scores(scores, weights, fraud_flags)


@tool
def calculate_volatility_tool(monthly_incomes: list[float]) -> dict:
    """Calculate income volatility from monthly income series."""
    return calculate_volatility(monthly_incomes)


@tool
def scan_hidden_debts_tool(bank_debits: list[dict], bureau_emis: list[dict]) -> dict:
    """Identify recurring EMI-like debits not in bureau report."""
    return scan_hidden_debts(bank_debits, bureau_emis)


@tool
def check_bias_tool(decisions: list[dict], protected_field: str) -> dict:
    """Perform disparate-impact 4/5ths rule check on lending decisions."""
    return check_bias(decisions, protected_field)


# -- Tool groups for binding to LangGraph nodes ------------------------------

CUSTOMER_FACING_TOOLS = [
    collect_basic_info,
    collect_loan_details,
    upload_document,
    show_verification,
    show_progress,
    show_offer,
    show_decision,
]

BACKEND_TOOLS = [
    check_eligibility_tool,
    calculate_dti_tool,
    estimate_emi_tool,
    calculate_risk_score_tool,
    score_four_cs_tool,
    lookup_rate_tool,
    generate_emi_schedule_tool,
    check_negative_list_tool,
    aggregate_scores_tool,
    calculate_volatility_tool,
    scan_hidden_debts_tool,
    check_bias_tool,
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph/test_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/graph/tools.py tests/test_graph/test_tools.py
git commit -m "feat: wrap all internal tools as LangGraph @tool functions"
```

---

### Task 11: LangGraph Nodes — Intake and Document Phases

**Files:**
- Create: `src/graph/nodes/__init__.py`
- Create: `src/graph/nodes/intake.py`
- Create: `src/graph/nodes/doc_collection.py`
- Create: `src/graph/nodes/doc_verification.py`
- Create: `tests/test_graph/test_nodes_intake.py`

- [ ] **Step 1: Write tests for intake node**

Create `tests/test_graph/test_nodes_intake.py`:

```python
from src.graph.nodes.intake import intake_node
from src.graph.nodes.doc_collection import doc_collection_node
from src.graph.nodes.doc_verification import doc_verification_node


def test_intake_node_is_callable():
    assert callable(intake_node)


def test_doc_collection_node_is_callable():
    assert callable(doc_collection_node)


def test_doc_verification_node_is_callable():
    assert callable(doc_verification_node)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph/test_nodes_intake.py -v`
Expected: FAIL

- [ ] **Step 3: Implement intake node**

Create `src/graph/nodes/__init__.py` (empty).

Create `src/graph/nodes/intake.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import collect_basic_info, collect_loan_details, check_eligibility_tool, show_progress


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def intake_node(state: LoanApplicationState) -> dict:
    """Intake node: greet customer, collect basic info, check eligibility, collect loan details."""
    llm = _get_llm()
    tools = [collect_basic_info, collect_loan_details, check_eligibility_tool, show_progress]
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = build_prompt("intake", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])

    response = await llm_with_tools.ainvoke(messages)

    return {"messages": [response], "current_phase": "intake"}
```

- [ ] **Step 4: Implement doc_collection node**

Create `src/graph/nodes/doc_collection.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import upload_document, show_progress


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def doc_collection_node(state: LoanApplicationState) -> dict:
    """Document collection node: determine required docs, ask for uploads one at a time."""
    # Determine required documents based on employment type
    employment = state.get("employment_type", "salaried")
    required = ["pan_card", "aadhaar", "selfie", "bank_statement"]
    if employment == "salaried":
        required.extend(["payslip", "form_16"])
    elif employment == "self_employed":
        required.extend(["itr", "gst_certificate"])

    uploaded = list(state.get("documents_uploaded", {}).keys())
    pending = [d for d in required if d not in uploaded]

    llm = _get_llm()
    tools = [upload_document, show_progress]
    llm_with_tools = llm.bind_tools(tools)

    updated_state = {**state, "documents_required": required, "documents_pending": pending}
    system_prompt = build_prompt("doc_collection", updated_state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])

    response = await llm_with_tools.ainvoke(messages)

    return {
        "messages": [response],
        "current_phase": "doc_collection",
        "documents_required": required,
        "documents_pending": pending,
    }
```

- [ ] **Step 5: Implement doc_verification node**

Create `src/graph/nodes/doc_verification.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import show_verification, show_progress


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def doc_verification_node(state: LoanApplicationState) -> dict:
    """Verify uploaded documents using Azure Document Intelligence.

    Extracts data, cross-validates fields, renders verification cards.
    """
    llm = _get_llm()
    tools = [show_verification, show_progress]
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = build_prompt("doc_verification", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])

    response = await llm_with_tools.ainvoke(messages)

    return {"messages": [response], "current_phase": "doc_verification"}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_graph/test_nodes_intake.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/graph/nodes/ tests/test_graph/test_nodes_intake.py
git commit -m "feat: add LangGraph intake, doc_collection, doc_verification nodes"
```

---

### Task 12: LangGraph Nodes — Risk, Scoring, Decision Phases

**Files:**
- Create: `src/graph/nodes/bureau_pull.py`
- Create: `src/graph/nodes/income_verification.py`
- Create: `src/graph/nodes/risk_assessment.py`
- Create: `src/graph/nodes/fraud_detection.py`
- Create: `src/graph/nodes/score_aggregation.py`
- Create: `src/graph/nodes/compliance.py`
- Create: `src/graph/nodes/pricing.py`
- Create: `src/graph/nodes/decision.py`
- Create: `src/graph/nodes/offer_generation.py`
- Create: `src/graph/nodes/human_review.py`
- Create: `tests/test_graph/test_nodes_backend.py`

- [ ] **Step 1: Write tests**

Create `tests/test_graph/test_nodes_backend.py`:

```python
from src.graph.nodes.bureau_pull import bureau_pull_node
from src.graph.nodes.income_verification import income_verification_node
from src.graph.nodes.risk_assessment import risk_assessment_node
from src.graph.nodes.fraud_detection import fraud_detection_node
from src.graph.nodes.score_aggregation import score_aggregation_node
from src.graph.nodes.compliance import compliance_node
from src.graph.nodes.pricing import pricing_node
from src.graph.nodes.decision import decision_node
from src.graph.nodes.offer_generation import offer_generation_node
from src.graph.nodes.human_review import human_review_node


def test_all_backend_nodes_are_callable():
    nodes = [
        bureau_pull_node, income_verification_node, risk_assessment_node,
        fraud_detection_node, score_aggregation_node, compliance_node,
        pricing_node, decision_node, offer_generation_node, human_review_node,
    ]
    for node in nodes:
        assert callable(node), f"{node.__name__} is not callable"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph/test_nodes_backend.py -v`
Expected: FAIL

- [ ] **Step 3: Implement all backend nodes**

Each backend node follows the same pattern as the intake node. The key difference is which tools are bound and which prompt phase is used.

Create `src/graph/nodes/bureau_pull.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def bureau_pull_node(state: LoanApplicationState) -> dict:
    """Pull credit bureau reports from CIBIL, Experian, CRIF, Equifax."""
    # In production, this calls the actual bureau clients.
    # For now, the LLM simulates the bureau pull based on context.
    llm = _get_llm()
    system_prompt = build_prompt("bureau_pull", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    return {"messages": [response], "current_phase": "bureau_pull"}
```

Create `src/graph/nodes/income_verification.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import calculate_volatility_tool, scan_hidden_debts_tool


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def income_verification_node(state: LoanApplicationState) -> dict:
    """Verify income from bank statements, payslips, employer data."""
    llm = _get_llm()
    tools = [calculate_volatility_tool, scan_hidden_debts_tool]
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = build_prompt("income_verification", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response], "current_phase": "income_verification"}
```

Create `src/graph/nodes/risk_assessment.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import (
    score_four_cs_tool, calculate_dti_tool, calculate_risk_score_tool,
    calculate_volatility_tool, scan_hidden_debts_tool,
)


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def risk_assessment_node(state: LoanApplicationState) -> dict:
    """Run 4Cs framework, DTI, volatility, hidden debt analysis."""
    llm = _get_llm()
    tools = [score_four_cs_tool, calculate_dti_tool, calculate_risk_score_tool,
             calculate_volatility_tool, scan_hidden_debts_tool]
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = build_prompt("risk_assessment", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response], "current_phase": "risk_assessment"}
```

Create `src/graph/nodes/fraud_detection.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def fraud_detection_node(state: LoanApplicationState) -> dict:
    """Identity and document fraud detection."""
    llm = _get_llm()
    system_prompt = build_prompt("fraud_detection", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    return {"messages": [response], "current_phase": "fraud_detection"}
```

Create `src/graph/nodes/score_aggregation.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import aggregate_scores_tool


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def score_aggregation_node(state: LoanApplicationState) -> dict:
    """Combine all scores into composite 300-900."""
    llm = _get_llm()
    tools = [aggregate_scores_tool]
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = build_prompt("score_aggregation", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response], "current_phase": "score_aggregation"}
```

Create `src/graph/nodes/compliance.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import check_bias_tool


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def compliance_node(state: LoanApplicationState) -> dict:
    """RBI compliance, fair lending, bias checks."""
    llm = _get_llm()
    tools = [check_bias_tool]
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = build_prompt("compliance", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response], "current_phase": "compliance"}
```

Create `src/graph/nodes/pricing.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import lookup_rate_tool, estimate_emi_tool, generate_emi_schedule_tool


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def pricing_node(state: LoanApplicationState) -> dict:
    """Calculate interest rate, processing fee, EMI."""
    llm = _get_llm()
    tools = [lookup_rate_tool, estimate_emi_tool, generate_emi_schedule_tool]
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = build_prompt("pricing", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response], "current_phase": "pricing"}
```

Create `src/graph/nodes/decision.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import show_decision


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def decision_node(state: LoanApplicationState) -> dict:
    """Make final credit decision: approve/conditional/deny/escalate."""
    llm = _get_llm()
    tools = [show_decision]
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = build_prompt("decision", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response], "current_phase": "decision"}
```

Create `src/graph/nodes/offer_generation.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt
from src.graph.tools import show_offer, generate_emi_schedule_tool


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def offer_generation_node(state: LoanApplicationState) -> dict:
    """Generate and present loan offer to customer."""
    llm = _get_llm()
    tools = [show_offer, generate_emi_schedule_tool]
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = build_prompt("offer_generation", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response], "current_phase": "offer_generation"}
```

Create `src/graph/nodes/human_review.py`:

```python
from __future__ import annotations

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage

from src.config import get_settings
from src.graph.state import LoanApplicationState
from src.graph.prompts.builder import build_prompt


def _get_llm():
    settings = get_settings()
    return AzureChatOpenAI(
        azure_deployment=settings.azure_chat_deployment,
        azure_endpoint=settings.azure_api_base,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
    )


async def human_review_node(state: LoanApplicationState) -> dict:
    """Inform customer their application is under human review."""
    llm = _get_llm()
    system_prompt = build_prompt("human_review", state)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    return {
        "messages": [response],
        "current_phase": "human_review",
        "needs_human_review": True,
        "conversation_complete": True,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph/test_nodes_backend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/graph/nodes/ tests/test_graph/test_nodes_backend.py
git commit -m "feat: add all 10 backend LangGraph nodes (bureau through human_review)"
```

---

### Task 13: LangGraph Graph Definition

**Files:**
- Create: `src/graph/graph.py`
- Create: `tests/test_graph/test_graph.py`

- [ ] **Step 1: Write tests for graph definition**

Create `tests/test_graph/test_graph.py`:

```python
from src.graph.graph import build_graph


def test_build_graph_returns_compiled_graph():
    graph = build_graph()
    assert graph is not None
    # LangGraph compiled graphs have a .invoke method
    assert hasattr(graph, "ainvoke")
    assert hasattr(graph, "astream")


def test_graph_has_all_nodes():
    graph = build_graph()
    # Access the graph's node names
    node_names = set(graph.nodes.keys())
    expected = {
        "intake", "doc_collection", "doc_verification",
        "bureau_pull", "income_verification",
        "risk_assessment", "fraud_detection", "score_aggregation",
        "compliance", "pricing", "decision",
        "offer_generation", "human_review",
        "__start__", "__end__",
    }
    # All expected nodes should be present (minus __start__ and __end__ which are implicit)
    for name in expected - {"__start__", "__end__"}:
        assert name in node_names, f"Missing node: {name}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph/test_graph.py -v`
Expected: FAIL

- [ ] **Step 3: Implement graph definition**

Create `src/graph/graph.py`:

```python
"""LangGraph StateGraph definition for loan underwriting.

13 nodes across 5 phases with conditional routing.
"""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from src.graph.state import LoanApplicationState
from src.graph.nodes.intake import intake_node
from src.graph.nodes.doc_collection import doc_collection_node
from src.graph.nodes.doc_verification import doc_verification_node
from src.graph.nodes.bureau_pull import bureau_pull_node
from src.graph.nodes.income_verification import income_verification_node
from src.graph.nodes.risk_assessment import risk_assessment_node
from src.graph.nodes.fraud_detection import fraud_detection_node
from src.graph.nodes.score_aggregation import score_aggregation_node
from src.graph.nodes.compliance import compliance_node
from src.graph.nodes.pricing import pricing_node
from src.graph.nodes.decision import decision_node
from src.graph.nodes.offer_generation import offer_generation_node
from src.graph.nodes.human_review import human_review_node


def _route_after_decision(state: LoanApplicationState) -> str:
    """Route after decision node: escalated → human_review, otherwise → offer."""
    decision = state.get("decision", "")
    if decision == "escalated" or state.get("needs_human_review"):
        return "human_review"
    if decision == "denied":
        return END
    return "offer_generation"


def build_graph(checkpointer=None):
    """Build and compile the 13-node loan underwriting StateGraph."""
    builder = StateGraph(LoanApplicationState)

    # Add all nodes
    builder.add_node("intake", intake_node)
    builder.add_node("doc_collection", doc_collection_node)
    builder.add_node("doc_verification", doc_verification_node)
    builder.add_node("bureau_pull", bureau_pull_node)
    builder.add_node("income_verification", income_verification_node)
    builder.add_node("risk_assessment", risk_assessment_node)
    builder.add_node("fraud_detection", fraud_detection_node)
    builder.add_node("score_aggregation", score_aggregation_node)
    builder.add_node("compliance", compliance_node)
    builder.add_node("pricing", pricing_node)
    builder.add_node("decision", decision_node)
    builder.add_node("offer_generation", offer_generation_node)
    builder.add_node("human_review", human_review_node)

    # Phase 1: Intake
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "doc_collection")

    # Phase 2: Extraction
    builder.add_edge("doc_collection", "doc_verification")

    # Phase 2→3: After verification, run parallel assessment
    builder.add_edge("doc_verification", "bureau_pull")
    builder.add_edge("doc_verification", "income_verification")

    # Phase 3: Risk (after bureau + income)
    builder.add_edge("bureau_pull", "risk_assessment")
    builder.add_edge("income_verification", "risk_assessment")
    builder.add_edge("risk_assessment", "fraud_detection")
    builder.add_edge("fraud_detection", "score_aggregation")

    # Phase 4: Decision
    builder.add_edge("score_aggregation", "compliance")
    builder.add_edge("score_aggregation", "pricing")
    builder.add_edge("compliance", "decision")
    builder.add_edge("pricing", "decision")

    # Conditional routing after decision
    builder.add_conditional_edges("decision", _route_after_decision)

    # Terminal edges
    builder.add_edge("offer_generation", END)
    builder.add_edge("human_review", END)

    return builder.compile(checkpointer=checkpointer)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/graph/graph.py tests/test_graph/test_graph.py
git commit -m "feat: define 13-node LangGraph StateGraph with conditional routing"
```

---

## Phase D: Streaming & Chat API

### Task 14: SSE Streaming Endpoint

**Files:**
- Create: `src/chat/__init__.py`
- Create: `src/chat/stream.py`
- Create: `tests/test_chat/__init__.py`
- Create: `tests/test_chat/test_stream.py`

- [ ] **Step 1: Write tests**

Create `tests/test_chat/__init__.py` (empty).

Create `tests/test_chat/test_stream.py`:

```python
from src.chat.stream import format_text_event, format_data_event


def test_format_text_event():
    event = format_text_event("msg_1", "txt_1", "Hello world")
    assert '"type":"text-delta"' in event
    assert '"delta":"Hello world"' in event


def test_format_data_event():
    event = format_data_event("msg_1", "status", {"phase": "intake"})
    assert '"type":"data-status"' in event
    assert '"phase":"intake"' in event
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_chat/test_stream.py -v`
Expected: FAIL

- [ ] **Step 3: Implement SSE stream helpers**

Create `src/chat/__init__.py` (empty).

Create `src/chat/stream.py`:

```python
"""SSE streaming helpers for Vercel AI SDK data stream protocol.

Converts LangGraph streaming events to the format expected by
Vercel AI SDK's useChat hook (x-vercel-ai-ui-message-stream: v1).
"""
from __future__ import annotations

import json
import uuid
from typing import AsyncGenerator

import structlog
from fastapi import Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.graph.graph import build_graph
from src.graph.state import LoanApplicationState
from src.db.session import get_db

logger = structlog.get_logger()


def format_text_event(message_id: str, part_id: str, delta: str) -> str:
    """Format a text-delta SSE event."""
    return f"data: {json.dumps({'type': 'text-delta', 'id': part_id, 'delta': delta})}\n\n"


def format_text_start(message_id: str, part_id: str) -> str:
    return f"data: {json.dumps({'type': 'text-start', 'id': part_id})}\n\n"


def format_text_end(part_id: str) -> str:
    return f"data: {json.dumps({'type': 'text-end', 'id': part_id})}\n\n"


def format_start_event(message_id: str) -> str:
    return f"data: {json.dumps({'type': 'start', 'messageId': message_id})}\n\n"


def format_finish_event(message_id: str) -> str:
    return f"data: {json.dumps({'type': 'finish', 'messageId': message_id})}\n\n"


def format_data_event(message_id: str, data_type: str, data: dict) -> str:
    """Format a custom data part SSE event."""
    return f"data: {json.dumps({'type': f'data-{data_type}', 'id': str(uuid.uuid4())[:8], 'data': data})}\n\n"


def format_tool_call_event(message_id: str, tool_name: str, args: dict) -> str:
    """Format a tool call as a data part that the frontend renders as inline UI."""
    return f"data: {json.dumps({'type': f'data-tool-{tool_name}', 'id': str(uuid.uuid4())[:8], 'data': args})}\n\n"


async def stream_langgraph_response(
    state: LoanApplicationState,
    thread_id: str,
    checkpointer=None,
) -> AsyncGenerator[str, None]:
    """Stream LangGraph execution as Vercel AI SDK SSE events."""
    graph = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    yield format_start_event(message_id)

    part_id = f"txt_{uuid.uuid4().hex[:8]}"
    text_started = False

    async for chunk in graph.astream(state, config=config, stream_mode=["updates", "custom"], version="v2"):
        chunk_type = chunk.get("type")

        if chunk_type == "updates":
            for node_name, update in chunk.get("data", {}).items():
                messages = update.get("messages", [])
                for msg in messages:
                    content = getattr(msg, "content", "")
                    tool_calls = getattr(msg, "tool_calls", [])

                    # Stream text content
                    if content and isinstance(content, str):
                        if not text_started:
                            yield format_text_start(message_id, part_id)
                            text_started = True
                        yield format_text_event(message_id, part_id, content)

                    # Stream tool calls as data parts
                    for tc in tool_calls:
                        tool_name = tc.get("name", "")
                        tool_args = tc.get("args", {})
                        yield format_tool_call_event(message_id, tool_name, tool_args)

                # Send phase update
                phase = update.get("current_phase")
                if phase:
                    yield format_data_event(message_id, "status", {"phase": phase, "node": node_name})

        elif chunk_type == "custom":
            yield format_data_event(message_id, "progress", chunk.get("data", {}))

    if text_started:
        yield format_text_end(part_id)
    yield format_finish_event(message_id)


def create_sse_response(generator: AsyncGenerator[str, None]) -> StreamingResponse:
    """Wrap an async generator in a proper SSE StreamingResponse."""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Vercel-AI-UI-Message-Stream": "v1",
        },
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_chat/test_stream.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/chat/ tests/test_chat/
git commit -m "feat: add SSE streaming with Vercel AI SDK data stream protocol"
```

---

### Task 15: Chat API Routes

**Files:**
- Create: `src/api/routes/chat.py`
- Create: `tests/test_chat/test_routes.py`

- [ ] **Step 1: Write tests for chat route structure**

Create `tests/test_chat/test_routes.py`:

```python
from src.api.routes.chat import router


def test_chat_router_has_stream_endpoint():
    paths = [r.path for r in router.routes]
    assert "/stream" in paths or any("/stream" in p for p in paths)


def test_chat_router_has_conversations_endpoint():
    paths = [r.path for r in router.routes]
    assert any("conversations" in str(p) for p in paths) or "" in paths
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_chat/test_routes.py -v`
Expected: FAIL

- [ ] **Step 3: Implement chat API routes**

Create `src/api/routes/chat.py`:

```python
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.models import User, Conversation, ChatMessage, Application, ApplicationStatus
from src.auth.middleware import get_current_user
from src.chat.stream import stream_langgraph_response, create_sse_response
from src.graph.state import LoanApplicationState

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    form_data: dict | None = None


@router.post("/stream")
async def chat_stream(
    req: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a chat response using LangGraph. Returns SSE events."""
    # Find or create conversation
    if req.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == uuid.UUID(req.conversation_id),
                Conversation.user_id == user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            user_id=user.id,
            status="active",
            current_phase="intake",
            langgraph_thread_id=f"thread_{uuid.uuid4().hex[:16]}",
        )
        db.add(conversation)
        await db.flush()

    # Store user message
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=req.message,
        tool_data=req.form_data,
    )
    db.add(user_msg)
    await db.flush()

    # Build LangGraph state from conversation history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at)
    )
    history = history_result.scalars().all()

    # Convert chat history to LangGraph messages
    from langchain_core.messages import HumanMessage, AIMessage
    messages = []
    for msg in history:
        if msg.role == "user":
            content = msg.content or ""
            if msg.tool_data:
                import json
                content += f"\n[Form Data]: {json.dumps(msg.tool_data)}"
            messages.append(HumanMessage(content=content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content or ""))

    state = LoanApplicationState(
        messages=messages,
        user_id=str(user.id),
        application_id=str(conversation.application_id or ""),
        reference_number="",
        current_phase=conversation.current_phase or "intake",
        conversation_complete=False,
        needs_human_review=False,
    )

    generator = stream_langgraph_response(
        state=state,
        thread_id=conversation.langgraph_thread_id or f"thread_{conversation.id}",
    )

    return create_sse_response(generator)


@router.get("/conversations")
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for the authenticated user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "status": c.status,
            "current_phase": c.current_phase,
            "application_id": str(c.application_id) if c.application_id else None,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a conversation (for resuming chat)."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msgs_result.scalars().all()

    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "tool_name": m.tool_name,
            "tool_data": m.tool_data,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_chat/test_routes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/routes/chat.py tests/test_chat/test_routes.py
git commit -m "feat: add chat API routes — stream, conversations, messages"
```

---

## Phase E: Backend Integration

### Task 16: Wire Up Main App — CORS, Auth, New Routes

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Update main.py**

Replace `src/main.py` with the updated version that includes CORS, auth routes, chat routes, and removes evolution routes:

```python
from __future__ import annotations

import time
from contextlib import asynccontextmanager

import structlog
import redis.asyncio as aioredis
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import get_settings
from src.db.session import engine
from src.api.middleware.audit import AuditMiddleware
from src.api.routes import applications, documents, hitl, reports, webhooks
from src.api.routes import offers, config, audit, notifications
from src.api.routes.auth import router as auth_router
from src.api.routes.chat import router as chat_router
from src.api.models.schemas import HealthResponse, ComponentHealth

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_loan_underwriting_system", environment=settings.environment)
    yield
    await engine.dispose()
    logger.info("shutdown_complete")


app = FastAPI(
    title="Personal Loan Underwriting API",
    description="AI-powered loan underwriting with LangGraph agent pipeline",
    version="4.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit logging
app.add_middleware(AuditMiddleware)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Auth routes (no auth required)
app.include_router(auth_router)

# Chat routes (auth required)
app.include_router(chat_router)

# Existing routes
app.include_router(applications.router)
app.include_router(documents.router)
app.include_router(hitl.router)
app.include_router(reports.router)
app.include_router(webhooks.router)
app.include_router(offers.router)
app.include_router(config.router)
app.include_router(audit.router)
app.include_router(notifications.router)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """System health check with component status."""
    from sqlalchemy import text

    components = {}

    # PostgreSQL
    try:
        start = time.time()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        components["db"] = ComponentHealth(
            status="healthy", latency_ms=round((time.time() - start) * 1000, 2)
        )
    except Exception as e:
        components["db"] = ComponentHealth(status=f"unhealthy: {e}")

    # Redis
    try:
        start = time.time()
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        components["redis"] = ComponentHealth(
            status="healthy", latency_ms=round((time.time() - start) * 1000, 2)
        )
    except Exception as e:
        components["redis"] = ComponentHealth(status=f"unhealthy: {e}")

    overall = "healthy" if all(c.status == "healthy" for c in components.values()) else "degraded"
    return HealthResponse(status=overall, components=components)
```

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v --tb=short -x`
Expected: All tests pass. Some existing tests may need minor import fixes if they reference removed modules.

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: wire up CORS, auth, chat routes; update health check; bump to v4"
```

---

### Task 17: Clean Up Legacy EvoAgentX Code

**Files:**
- Delete: `src/workflows/loan_underwriting_workflow.py`
- Delete: `src/agents/orchestrator.py`
- Delete: `src/memory/mem0_config.py`
- Delete: `src/memory/memory_manager.py`
- Delete: `src/evolution/textgrad_config.py`
- Delete: `src/evolution/aflow_config.py`
- Delete: `src/evolution/mipro_config.py`
- Delete: `src/api/routes/evolution.py`
- Modify: `src/workflows/__init__.py`
- Modify: `src/agents/__init__.py`

- [ ] **Step 1: Remove legacy files**

```bash
rm src/workflows/loan_underwriting_workflow.py
rm src/agents/orchestrator.py
rm src/memory/mem0_config.py
rm src/memory/memory_manager.py
rm src/evolution/textgrad_config.py
rm src/evolution/aflow_config.py
rm src/evolution/mipro_config.py
rm src/api/routes/evolution.py
```

- [ ] **Step 2: Update affected __init__.py files**

Clear `src/workflows/__init__.py`, `src/memory/__init__.py`, `src/evolution/__init__.py` to be empty.

- [ ] **Step 3: Remove evolution router from any remaining imports**

Grep for `evolution` imports and remove them.

- [ ] **Step 4: Fix any broken tests**

Run: `pytest tests/ -v --tb=short`

Remove or update tests that reference deleted modules:
- `tests/test_workflow/test_loan_underwriting.py` — delete this file (tests the old EvoAgentX workflow)
- `tests/test_agents/test_decision_pipeline.py` — delete if it imports from deleted EvoAgentX agents
- `tests/test_evolution/test_guardrails.py` — keep (guardrails.py is retained)
- `tests/test_agents/test_memory_manager.py` — delete

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v --tb=short -x`
Expected: All remaining tests pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: remove EvoAgentX, Mem0, evolution modules; LangGraph is the new runtime"
```

---

### Task 18: Update .env with New Variables

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Update .env.example with all new variables**

Add to `.env.example`:

```bash
# Google SSO
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Azure Document Intelligence
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-account.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=your-key

# Azure Blob Storage
AZURE_BLOB_CONNECTION_STRING=your-connection-string
AZURE_BLOB_CONTAINER=loan-documents

# Frontend
FRONTEND_URL=http://localhost:3000
```

- [ ] **Step 2: Update actual .env file locally with real values**

Add the Google SSO credentials and Azure Doc Intelligence endpoint from the existing AI Services account.

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "docs: update .env.example with Google SSO, JWT, Doc Intelligence variables"
```

---

### Task 19: Final Backend Verification

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 2: Verify app starts**

Run: `uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload`
Expected: Server starts without import errors. Check http://localhost:8000/docs for OpenAPI spec showing all routes including `/api/v1/auth/*` and `/api/v1/chat/*`.

- [ ] **Step 3: Commit any remaining fixes**

```bash
git add -A
git commit -m "fix: resolve any remaining import or runtime issues for v4 backend"
```
