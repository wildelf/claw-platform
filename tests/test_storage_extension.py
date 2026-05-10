import pytest
import asyncio
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.domain.nudge_record import NudgeRecord, NudgePriority
from app.domain.base import EntityId

@pytest.mark.asyncio
async def test_save_and_get_nudge_record():
    storage = SQLiteStorage(db_path=":memory:")
    await storage.init_db()

    record = NudgeRecord.create(
        agent_id=EntityId("agent-123"),
        session_id="session-456",
        memory_type="MEMORY.md",
        content="Test content",
        trigger_reason="reasoning",
        priority=NudgePriority.MEDIUM,
    )
    await storage.save_nudge_record(record)

    retrieved = await storage.get_nudge_record(str(record.id))
    assert retrieved is not None
    assert retrieved.content == "Test content"
    assert retrieved.memory_type == "MEMORY.md"

@pytest.mark.asyncio
async def test_get_nudge_records_by_agent():
    storage = SQLiteStorage(db_path=":memory:")
    await storage.init_db()

    # Create multiple records
    for i in range(3):
        record = NudgeRecord.create(
            agent_id=EntityId("agent-123"),
            session_id=f"session-{i}",
            memory_type="MEMORY.md",
            content=f"Content {i}",
            trigger_reason="reasoning",
            priority=NudgePriority.MEDIUM,
        )
        await storage.save_nudge_record(record)

    records = await storage.get_nudge_records_by_agent("agent-123")
    assert len(records) == 3