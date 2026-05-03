"""Integration tests for auth API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.api import api_router
import tempfile
from pathlib import Path

from fastapi import FastAPI
from app.api.deps import get_storage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


@pytest_asyncio.fixture
async def test_app(temp_db):
    """Create test app with in-memory storage."""
    app = FastAPI()
    app.include_router(api_router)

    storage = SQLiteStorage(temp_db)
    await storage.init_db()

    async def override_get_storage():
        return storage

    app.dependency_overrides[get_storage] = override_get_storage

    yield app, storage


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