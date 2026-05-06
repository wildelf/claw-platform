"""Tests for session storage operations."""

import pytest
from datetime import datetime, timezone

from app.domain.session import Session
from app.domain.base import EntityId
from app.infrastructure.storage.sqlite import SQLiteStorage


@pytest.mark.asyncio
async def test_save_and_get_session(tmp_path):
    """Test saving and retrieving a session."""
    db_path = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path)
    await storage.init_db()

    session = Session.create(agent_id="agent-123", name="Test Session")

    await storage.save_session(session)

    retrieved = await storage.get_session(str(session.id))
    assert retrieved is not None
    assert retrieved.id == session.id
    assert retrieved.name == "Test Session"
    assert retrieved.agent_id == EntityId("agent-123")
    assert retrieved.message_count == 0

    await storage.close()


@pytest.mark.asyncio
async def test_save_session_updates_existing(tmp_path):
    """Test that saving an existing session updates it."""
    db_path = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path)
    await storage.init_db()

    session = Session.create(agent_id="agent-123", name="Original Name")

    await storage.save_session(session)

    # Update the session
    session.name = "Updated Name"
    session.message_count = 5
    await storage.save_session(session)

    # Should still be one session
    sessions = await storage.list_sessions()
    assert len(sessions) == 1

    retrieved = await storage.get_session(str(session.id))
    assert retrieved is not None
    assert retrieved.name == "Updated Name"
    assert retrieved.message_count == 5

    await storage.close()


@pytest.mark.asyncio
async def test_list_sessions(tmp_path):
    """Test listing sessions."""
    db_path = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path)
    await storage.init_db()

    # Create multiple sessions
    for i in range(5):
        session = Session.create(agent_id=f"agent-{i}", name=f"Session {i}")
        await storage.save_session(session)

    sessions = await storage.list_sessions(offset=0, limit=10)
    assert len(sessions) == 5

    # Test pagination
    sessions_page1 = await storage.list_sessions(offset=0, limit=2)
    sessions_page2 = await storage.list_sessions(offset=2, limit=2)
    sessions_page3 = await storage.list_sessions(offset=4, limit=2)

    assert len(sessions_page1) == 2
    assert len(sessions_page2) == 2
    assert len(sessions_page3) == 1

    await storage.close()


@pytest.mark.asyncio
async def test_delete_session(tmp_path):
    """Test deleting a session."""
    db_path = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path)
    await storage.init_db()

    session = Session.create(agent_id="agent-123", name="To Delete")
    await storage.save_session(session)

    retrieved = await storage.get_session(str(session.id))
    assert retrieved is not None

    await storage.delete_session(str(session.id))

    retrieved = await storage.get_session(str(session.id))
    assert retrieved is None

    await storage.close()


@pytest.mark.asyncio
async def test_list_sessions_ordering(tmp_path):
    """Test that sessions are ordered by updated_at descending."""
    db_path = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path)
    await storage.init_db()

    # Create sessions with slight time differences
    session1 = Session.create(agent_id="agent-1", name="First")
    await storage.save_session(session1)

    # Small delay to ensure different timestamps
    session2 = Session.create(agent_id="agent-2", name="Second")
    await storage.save_session(session2)

    session3 = Session.create(agent_id="agent-3", name="Third")
    await storage.save_session(session3)

    sessions = await storage.list_sessions()

    # Most recently updated should be first
    assert sessions[0].name == "Third"
    assert sessions[1].name == "Second"
    assert sessions[2].name == "First"

    await storage.close()


@pytest.mark.asyncio
async def test_session_message_count(tmp_path):
    """Test that message_count is properly stored."""
    db_path = str(tmp_path / "test.db")
    storage = SQLiteStorage(db_path)
    await storage.init_db()

    session = Session.create(agent_id="agent-123", name="Message Test")
    session.message_count = 42

    await storage.save_session(session)

    retrieved = await storage.get_session(str(session.id))
    assert retrieved is not None
    assert retrieved.message_count == 42

    await storage.close()