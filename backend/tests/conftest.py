"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from app.infrastructure.storage.sqlite import SQLiteStorage


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
    await storage.initialize()
    yield storage
    await storage.close()


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()