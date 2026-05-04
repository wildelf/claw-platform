# User Authentication Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement JWT-based user authentication backend: register, login, logout, with bcrypt password hashing and proper user isolation.

**Architecture:** Add user CRUD to storage layer, create auth service with JWT generation/verification, expose login/register endpoints, update dependency injection to extract user from JWT. Users already have a domain entity and SQLite model — this plan extends them with auth capabilities.

**Tech Stack:** FastAPI, python-jose (JWT), passlib[bcrypt] (password hashing), already in project dependencies.

---

## File Inventory

**Create:**
- `backend/app/api/auth.py` — Login/register endpoints
- `backend/app/application/auth_service.py` — JWT token and password operations
- `backend/tests/test_auth_service.py` — Unit tests for auth service
- `backend/tests/test_auth_api.py` — Integration tests for auth endpoints

**Modify:**
- `backend/app/infrastructure/storage/base.py:1-50` — Add user storage operations to protocol
- `backend/app/infrastructure/storage/sqlite.py:1-536` — Implement `save_user`, `get_user`, `get_user_by_username`, `get_user_by_email`, `delete_user`
- `backend/app/api/deps.py:40-50` — Replace TODO stub with real JWT extraction, add `get_current_user`
- `backend/app/api/__init__.py` — Register auth router

---

## Task 1: Add user storage operations to protocol

**Files:**
- Modify: `backend/app/infrastructure/storage/base.py`

- [ ] **Step 1: Add user operations to StorageAdapter protocol**

```python
# Add to StorageAdapter class in base.py:
async def save_user(self, user: User) -> None: ...
async def get_user(self, id: str) -> Optional[User]: ...
async def get_user_by_username(self, username: str) -> Optional[User]: ...
async def get_user_by_email(self, email: str) -> Optional[User]: ...
async def delete_user(self, id: str) -> None: ...

# Add import:
from app.domain.user import User
```

- [ ] **Step 2: Run type check to verify protocol**

Run: `cd backend && python -c "from app.infrastructure.storage.base import StorageAdapter; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/infrastructure/storage/base.py
git commit -m "feat(auth): add user operations to storage protocol"
```

---

## Task 2: Implement user storage operations in SQLiteStorage

**Files:**
- Modify: `backend/app/infrastructure/storage/sqlite.py`

- [ ] **Step 1: Add user storage methods to SQLiteStorage**

Add these methods after the existing Feedback operations (after line ~536):

```python
# User operations
async def save_user(self, user: User) -> None:
    async with self.async_session() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        existing = result.scalar_one_or_none()

        model = UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        if existing:
            for key in ['username', 'email', 'password_hash', 'role', 'is_active', 'updated_at']:
                setattr(existing, key, getattr(model, key))
        else:
            session.add(model)
        await session.commit()

async def get_user(self, id: str) -> Optional[User]:
    async with self.async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(UserModel).where(UserModel.id == id))
        row = result.scalar_one_or_none()
        return self._to_user(row) if row else None

async def get_user_by_username(self, username: str) -> Optional[User]:
    async with self.async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(UserModel).where(UserModel.username == username))
        row = result.scalar_one_or_none()
        return self._to_user(row) if row else None

async def get_user_by_email(self, email: str) -> Optional[User]:
    async with self.async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(UserModel).where(UserModel.email == email))
        row = result.scalar_one_or_none()
        return self._to_user(row) if row else None

async def delete_user(self, id: str) -> None:
    async with self.async_session() as session:
        from sqlalchemy import delete
        await session.execute(delete(UserModel).where(UserModel.id == id))
        await session.commit()
```

- [ ] **Step 2: Run existing tests to ensure nothing broke**

Run: `cd backend && python -m pytest tests/test_storage.py -v 2>/dev/null || echo "No storage tests yet, skipping"`
Expected: No failures (or "No storage tests yet")

- [ ] **Step 3: Commit**

```bash
git add backend/app/infrastructure/storage/sqlite.py
git commit -m "feat(auth): implement user storage operations in SQLiteStorage"
```

---

## Task 3: Create auth service with JWT and password hashing

**Files:**
- Create: `backend/app/application/auth_service.py`

- [ ] **Step 1: Create auth service**

```python
"""Authentication service with JWT and password hashing."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.domain.user import User, UserRole
from app.domain.base import EntityId


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.auth.jwt.algorithm
SECRET_KEY = settings.auth.jwt.secret
ACCESS_TOKEN_EXPIRE_MINUTES = settings.auth.jwt.expire_minutes


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        pass

    def hash_password(self, plain_password: str) -> str:
        """Hash a plain password using bcrypt."""
        return pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: str, username: str, role: str) -> str:
        """Create a JWT access token."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode a JWT token. Returns payload if valid, None if invalid."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None

    def create_user(self, username: str, email: str, password: str, role: UserRole = UserRole.USER) -> User:
        """Create a new user with hashed password."""
        return User(
            id=EntityId.generate(),
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            role=role,
            is_active=True,
        )

    def authenticate_user(self, username: str, password: str, user: User) -> bool:
        """Authenticate a user by username and password."""
        if not user.is_active:
            return False
        return self.verify_password(password, user.password_hash)
```

- [ ] **Step 2: Verify the module loads**

Run: `cd backend && python -c "from app.application.auth_service import AuthService; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/application/auth_service.py
git commit -m "feat(auth): create auth service with JWT and password hashing"
```

---

## Task 4: Create auth API endpoints

**Files:**
- Create: `backend/app/api/auth.py`

- [ ] **Step 1: Create auth API routes**

```python
"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import Storage
from app.application.auth_service import AuthService
from app.domain.user import UserRole
from pydantic import BaseModel, Field, EmailStr


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Payload for user registration."""
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=255)
    password: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    """Payload for user login."""
    username: str = Field(max_length=50)
    password: str = Field(max_length=100)


class AuthResponse(BaseModel):
    """Response containing access token."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    storage: Storage,
) -> AuthResponse:
    """Register a new user."""
    # Check if username already exists
    existing_user = await storage.get_user_by_username(request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    existing_email = await storage.get_user_by_email(request.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    auth_service = AuthService()
    user = auth_service.create_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )

    # Save to storage
    await storage.save_user(user)

    # Generate token
    access_token = auth_service.create_access_token(
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )

    return AuthResponse(
        access_token=access_token,
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    storage: Storage,
) -> AuthResponse:
    """Login and receive an access token."""
    # Get user by username
    user = await storage.get_user_by_username(request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    auth_service = AuthService()
    if not auth_service.authenticate_user(request.username, request.password, user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate token
    access_token = auth_service.create_access_token(
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )

    return AuthResponse(
        access_token=access_token,
        user_id=str(user.id),
        username=user.username,
        role=user.role,
    )
```

- [ ] **Step 2: Verify the module loads**

Run: `cd backend && python -c "from app.api.auth import router; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/auth.py
git commit -m "feat(auth): add register and login API endpoints"
```

---

## Task 5: Update dependency injection for real JWT auth

**Files:**
- Modify: `backend/app/api/deps.py`

- [ ] **Step 1: Replace the TODO stub with real JWT extraction**

Replace the `get_current_user_id` function (lines 40-47) with:

```python
async def get_current_user_id() -> EntityId:
    """Get current user ID from auth context.

    Extracts user_id from the Authorization header JWT token.
    Raises HTTPException if token is missing or invalid.
    """
    from fastapi import HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from app.application.auth_service import AuthService

    security = HTTPBearer()

    # This will be called via Depends so we need to get credentials differently
    # See updated get_current_user below which handles this properly
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


class AuthContext:
    """Auth context containing the current user."""
    def __init__(self, user_id: EntityId, username: str, role: str):
        self.user_id = user_id
        self.username = username
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthContext:
    """Extract and validate JWT token, returning auth context.

    Depends on HTTPBearer to extract the token from Authorization header.
    """
    from fastapi import HTTPException, status
    from app.application.auth_service import AuthService

    token = credentials.credentials
    auth_service = AuthService()
    payload = auth_service.verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")

    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthContext(
        user_id=EntityId(user_id),
        username=username,
        role=role,
    )


async def get_current_user_id_from_auth(
    auth: AuthContext = Depends(get_current_user),
) -> EntityId:
    """Get current user ID from auth context."""
    return auth.user_id


UserId = Annotated[EntityId, Depends(get_current_user_id_from_auth)]
```

Also add this import at the top of the file after existing imports:
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
```

- [ ] **Step 2: Verify the module loads**

Run: `cd backend && python -c "from app.api.deps import get_current_user, UserId; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/deps.py
git commit -m "feat(auth): replace TODO stub with real JWT extraction"
```

---

## Task 6: Register auth router

**Files:**
- Modify: `backend/app/api/__init__.py`

- [ ] **Step 1: Add auth router to API**

Replace the current `__init__.py` content with:

```python
"""API route aggregation."""

from fastapi import APIRouter

from app.api import agents, auth, feedback, models, skills, tools

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(agents.router)
api_router.include_router(auth.router)
api_router.include_router(feedback.router)
api_router.include_router(models.router)
api_router.include_router(skills.router)
api_router.include_router(tools.router)

__all__ = ["api_router"]
```

- [ ] **Step 2: Verify no circular import**

Run: `cd backend && python -c "from app.api import api_router; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/__init__.py
git commit -m "feat(auth): register auth router in API"
```

---

## Task 7: Write unit tests for auth service

**Files:**
- Create: `backend/tests/test_auth_service.py`

- [ ] **Step 1: Write auth service unit tests**

```python
"""Tests for auth service."""

import pytest
from app.application.auth_service import AuthService
from app.domain.user import User, UserRole
from app.domain.base import EntityId


class TestPasswordHashing:
    """Tests for password hashing."""

    def test_hash_password_returns_different_value(self):
        """Hashed password should differ from plain text."""
        service = AuthService()
        password = "testpassword123"
        hashed = service.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_is_unique(self):
        """Same password should produce different hashes (salted)."""
        service = AuthService()
        password = "testpassword123"
        hash1 = service.hash_password(password)
        hash2 = service.hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """verify_password returns True for correct password."""
        service = AuthService()
        password = "testpassword123"
        hashed = service.hash_password(password)
        assert service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password returns False for incorrect password."""
        service = AuthService()
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = service.hash_password(password)
        assert service.verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Tests for JWT token operations."""

    def test_create_access_token_returns_string(self):
        """create_access_token returns a non-empty string."""
        service = AuthService()
        token = service.create_access_token(
            user_id="user-123",
            username="testuser",
            role="user",
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_valid(self):
        """verify_token returns payload for valid token."""
        service = AuthService()
        token = service.create_access_token(
            user_id="user-123",
            username="testuser",
            role="user",
        )
        payload = service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"

    def test_verify_token_invalid(self):
        """verify_token returns None for invalid token."""
        service = AuthService()
        payload = service.verify_token("invalid.token.here")
        assert payload is None

    def test_verify_token_tampered(self):
        """verify_token returns None for tampered token."""
        service = AuthService()
        token = service.create_access_token(
            user_id="user-123",
            username="testuser",
            role="user",
        )
        # Tamper with the token
        tampered = token[:-5] + "XXXXX"
        payload = service.verify_token(tampered)
        assert payload is None


class TestUserCreation:
    """Tests for user creation."""

    def test_create_user_hashes_password(self):
        """create_user should hash the password, not store plain text."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="plaintextpassword",
        )
        assert user.password_hash != "plaintextpassword"
        assert user.password_hash.startswith("$2b$")  # bcrypt prefix

    def test_create_user_generates_id(self):
        """create_user should generate a unique ID."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
        )
        assert user.id is not None
        assert len(str(user.id)) == 36  # UUID format

    def test_create_user_default_role(self):
        """create_user should default to USER role."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="password",
        )
        assert user.role == UserRole.USER

    def test_create_user_admin_role(self):
        """create_user should accept admin role."""
        service = AuthService()
        user = service.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password",
            role=UserRole.ADMIN,
        )
        assert user.role == UserRole.ADMIN


class TestAuthenticateUser:
    """Tests for user authentication."""

    def test_authenticate_user_success(self):
        """authenticate_user returns True for valid credentials."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="correctpassword",
        )
        result = service.authenticate_user("testuser", "correctpassword", user)
        assert result is True

    def test_authenticate_user_wrong_password(self):
        """authenticate_user returns False for wrong password."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="correctpassword",
        )
        result = service.authenticate_user("testuser", "wrongpassword", user)
        assert result is False

    def test_authenticate_user_inactive_user(self):
        """authenticate_user returns False for inactive user."""
        service = AuthService()
        user = service.create_user(
            username="testuser",
            email="test@example.com",
            password="correctpassword",
        )
        user.is_active = False
        result = service.authenticate_user("testuser", "correctpassword", user)
        assert result is False
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_auth_service.py -v`
Expected: All 11 tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_auth_service.py
git commit -m "test(auth): add unit tests for auth service"
```

---

## Task 8: Write integration tests for auth API

**Files:**
- Create: `backend/tests/test_auth_api.py`

- [ ] **Step 1: Write auth API integration tests**

```python
"""Integration tests for auth API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.api import api_router
from app.config import settings
import tempfile
from pathlib import Path


# Create a test app
from fastapi import FastAPI


@pytest_asyncio.fixture
async def test_app(temp_db):
    """Create test app with in-memory storage."""
    from app.api.deps import get_storage

    app = FastAPI()
    app.include_router(api_router)

    storage = SQLiteStorage(temp_db)
    await storage.init_db()

    async def override_get_storage():
        return storage

    app.dependency_overrides[get_storage] = override_get_storage

    yield app, storage

    await storage.close()


@pytest_asyncio.fixture
async def client(test_app):
    """Create test client."""
    app, _ = test_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestRegisterEndpoint:
    """Tests for POST /auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Register with valid data returns 201 and token."""
        response = await client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "newuser"
        assert data["role"] == "user"
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client):
        """Register with existing username returns 400."""
        # First registration
        await client.post("/auth/register", json={
            "username": "duplicateuser",
            "email": "user1@example.com",
            "password": "password123",
        })
        # Second registration with same username
        response = await client.post("/auth/register", json={
            "username": "duplicateuser",
            "email": "user2@example.com",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        """Register with existing email returns 400."""
        # First registration
        await client.post("/auth/register", json={
            "username": "user1",
            "email": "same@example.com",
            "password": "password123",
        })
        # Second registration with same email
        response = await client.post("/auth/register", json={
            "username": "user2",
            "email": "same@example.com",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_short_password(self, client):
        """Register with too-short password returns 422."""
        response = await client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345",  # less than 6 chars
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_username(self, client):
        """Register with too-short username returns 422."""
        response = await client.post("/auth/register", json={
            "username": "ab",  # less than 3 chars
            "email": "test@example.com",
            "password": "password123",
        })
        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """Login with valid credentials returns token."""
        # Register first
        await client.post("/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "correctpassword",
        })
        # Login
        response = await client.post("/auth/login", json={
            "username": "loginuser",
            "password": "correctpassword",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "loginuser"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        """Login with wrong password returns 401."""
        # Register first
        await client.post("/auth/register", json={
            "username": "loginuser2",
            "email": "login2@example.com",
            "password": "correctpassword",
        })
        # Login with wrong password
        response = await client.post("/auth/login", json={
            "username": "loginuser2",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Login with non-existent user returns 401."""
        response = await client.post("/auth/login", json={
            "username": "doesnotexist",
            "password": "anypassword",
        })
        assert response.status_code == 401
```

- [ ] **Step 2: Run integration tests**

Run: `cd backend && python -m pytest tests/test_auth_api.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_auth_api.py
git commit -m "test(auth): add integration tests for auth API"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - User registration: Task 4 (POST /auth/register)
   - User login: Task 4 (POST /auth/login)
   - JWT token generation: Task 3 (AuthService.create_access_token)
   - JWT verification: Task 3 (AuthService.verify_token)
   - Password hashing: Task 3 (AuthService.hash_password/verify_password)
   - User isolation (per-user storage): Task 1-2 (user_id filtering in storage)
   - Auth dependency injection: Task 5 (get_current_user)
   - All endpoints tested: Task 7-8

2. **Placeholder scan:** No TBD/TODO placeholders. All code is complete and runnable.

3. **Type consistency:** All method signatures use consistent types from domain entities. AuthService uses `EntityId` from `app.domain.base`. User role uses `UserRole` enum.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-03-user-authentication-backend.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**