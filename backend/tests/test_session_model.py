import pytest
from datetime import datetime, timezone

from app.domain.base import EntityId
from app.domain.session import Session


def test_session_create():
    """Test Session.create() factory method."""
    agent_id = "agent-123"
    session = Session.create(agent_id=agent_id)

    assert isinstance(session.id, EntityId)
    assert session.agent_id == EntityId(agent_id)
    assert session.name == ""
    assert session.message_count == 0
    assert session.created_at == session.updated_at
    assert isinstance(session.created_at, datetime)


def test_session_create_with_name():
    """Test Session.create() with a name."""
    agent_id = "agent-456"
    name = "Test Session"
    session = Session.create(agent_id=agent_id, name=name)

    assert session.name == name
    assert session.agent_id == EntityId(agent_id)


def test_session_fields():
    """Test that Session has all required fields."""
    now = datetime.now(timezone.utc)
    session = Session(
        id=EntityId.generate(),
        name="My Session",
        agent_id=EntityId("agent-789"),
        created_at=now,
        updated_at=now,
        message_count=5,
    )

    assert session.id is not None
    assert session.name == "My Session"
    assert session.agent_id == EntityId("agent-789")
    assert session.created_at == now
    assert session.updated_at == now
    assert session.message_count == 5