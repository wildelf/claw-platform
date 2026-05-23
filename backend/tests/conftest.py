"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from app.infrastructure.storage.sqlite import SQLiteStorage
from app.application.auth_service import AuthService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


@pytest_asyncio.fixture
async def storage(temp_db):
    """Create a storage instance with temporary database."""
    storage = SQLiteStorage(temp_db)
    await storage.init_db()
    yield storage
    await storage.close()


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def auth_service():
    """Create an AuthService instance for token generation."""
    return AuthService()


@pytest.fixture
def valid_token(auth_service):
    """Generate a valid JWT token for testing."""
    return auth_service.create_access_token(
        user_id="test-user-id-123",
        username="testuser",
        role="user",
    )


@pytest.fixture
def auth_headers(valid_token):
    """Return headers with valid auth token."""
    return {"Authorization": f"Bearer {valid_token}"}