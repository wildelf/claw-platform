"""Tests for NudgeRecord domain entity."""

from datetime import datetime, timezone

from app.domain.nudge_record import NudgeRecord, NudgePriority, NudgeType


def test_nudge_record_create():
    """Test NudgeRecord.create() creates a valid instance."""
    record = NudgeRecord.create(
        agent_id="agent-123",
        session_id="session-456",
        memory_type="MEMORY.md",
        content="Remember to check the database connection",
        trigger_reason="rule",
        priority="high",
    )

    assert record.agent_id == "agent-123"
    assert record.session_id == "session-456"
    assert record.memory_type == "MEMORY.md"
    assert record.content == "Remember to check the database connection"
    assert record.trigger_reason == "rule"
    assert record.priority == "high"
    assert record.id is not None
    assert record.created_at is not None


def test_nudge_record_serialization():
    """Test NudgeRecord can be serialized to dict."""
    record = NudgeRecord.create(
        agent_id="agent-123",
        session_id="session-456",
        memory_type="USER.md",
        content="Update user preferences",
        trigger_reason="reasoning",
        priority="medium",
    )

    data = record.model_dump()

    assert data["agent_id"] == "agent-123"
    assert data["session_id"] == "session-456"
    assert data["memory_type"] == "USER.md"
    assert data["content"] == "Update user preferences"
    assert data["trigger_reason"] == "reasoning"
    assert data["priority"] == "medium"
    assert "id" in data
    assert "created_at" in data


def test_nudge_record_default_priority():
    """Test NudgeRecord.create() uses 'medium' as default priority."""
    record = NudgeRecord.create(
        agent_id="agent-123",
        session_id="session-456",
        memory_type="skill",
        content="Invoke the backup skill",
        trigger_reason="composite",
    )

    assert record.priority == "medium"


def test_nudge_type_enum():
    """Test NudgeType enum values."""
    assert NudgeType.MEMORY == "memory"
    assert NudgeType.SKILL == "skill"
    assert NudgeType.BOTH == "both"


def test_nudge_priority_enum():
    """Test NudgePriority enum values."""
    assert NudgePriority.HIGH == "high"
    assert NudgePriority.MEDIUM == "medium"
    assert NudgePriority.LOW == "low"