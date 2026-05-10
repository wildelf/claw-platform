"""Tests for SkillGenerator."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.skill_generator import SkillGenerator


@pytest.mark.asyncio
async def test_generate_skill_md():
    mock_storage = MagicMock()
    mock_storage.save_skill = AsyncMock()
    mock_storage.save_skill_file = AsyncMock()
    mock_storage.get_conversation_memories = AsyncMock(return_value=[])

    generator = SkillGenerator(storage=mock_storage)
    skill = await generator.generate_from_conversation(
        agent_id="agent-123",
        session_id="session-456",
        skill_name="test-skill",
        description="Test skill description",
    )

    assert skill is not None
    assert skill.name == "test-skill"
    assert skill.description == "Test skill description"
    # auto_created should default to False since it's not in old Skill model
    assert skill.status == "trained"


@pytest.mark.asyncio
async def test_generate_with_memories():
    mock_storage = MagicMock()
    mock_storage.save_skill = AsyncMock()
    mock_storage.save_skill_file = AsyncMock()

    # Mock conversation memory
    mock_mem = MagicMock()
    mock_mem.user_input = "用户输入"
    mock_mem.agent_output = "代理回复"
    mock_storage.get_conversation_memories = AsyncMock(return_value=[mock_mem])

    generator = SkillGenerator(storage=mock_storage)
    skill = await generator.generate_from_conversation(
        agent_id="agent-123",
        session_id="session-456",
        skill_name="test-skill-2",
        description="Test skill with memories",
    )

    assert skill is not None
    assert skill.name == "test-skill-2"