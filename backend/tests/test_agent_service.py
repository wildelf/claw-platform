"""Tests for agent service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.agent_service import AgentService
from app.domain.agent import Agent, AgentStatus
from app.domain.base import EntityId


@pytest.fixture
def mock_storage():
    """Create a mock storage."""
    storage = MagicMock()
    storage.get_agent = AsyncMock()
    storage.save_agent = AsyncMock(return_value=None)
    storage.delete_agent = AsyncMock(return_value=None)
    storage.list_agents = AsyncMock(return_value=[])
    return storage


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    return Agent(
        name="test-agent",
        description="A test agent",
        role="assistant",
        goal="help users",
        backstory="I am a helpful assistant",
        skill_ids=[],
        tool_ids=[],
        user_id=EntityId.generate(),
    )


class TestAgentService:
    """Tests for AgentService."""

    @pytest.mark.asyncio
    async def test_create_agent(self, mock_storage, sample_agent):
        """Creating an agent should save it to storage."""
        service = AgentService(mock_storage)
        result = await service.create(sample_agent)
        assert result.name == sample_agent.name
        mock_storage.save_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_agent_returns_none_when_not_found(self, mock_storage):
        """get_agent should return None for non-existent agent."""
        mock_storage.get_agent.return_value = None
        service = AgentService(mock_storage)
        result = await service.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_returns_agent(self, mock_storage, sample_agent):
        """get_agent should return agent when found."""
        mock_storage.get_agent.return_value = sample_agent
        service = AgentService(mock_storage)
        result = await service.get(sample_agent.id)
        assert result == sample_agent

    @pytest.mark.asyncio
    async def test_update_agent(self, mock_storage, sample_agent):
        """Updating an agent should save it."""
        mock_storage.get_agent.return_value = sample_agent
        service = AgentService(mock_storage)
        result = await service.update(sample_agent.id, {"name": "updated-name"})
        assert result.name == "updated-name"
        mock_storage.save_agent.assert_called()

    @pytest.mark.asyncio
    async def test_update_agent_returns_none_when_not_found(self, mock_storage):
        """update_agent should return None for non-existent agent."""
        mock_storage.get_agent.return_value = None
        service = AgentService(mock_storage)
        result = await service.update("nonexistent", {"name": "test"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_agent_returns_true_when_found(self, mock_storage, sample_agent):
        """delete_agent should return True when agent exists."""
        mock_storage.get_agent.return_value = sample_agent
        mock_storage.delete_agent.return_value = True
        service = AgentService(mock_storage)
        result = await service.delete(sample_agent.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_agent_returns_false_when_not_found(self, mock_storage):
        """delete_agent should return False when agent doesn't exist."""
        mock_storage.get_agent.return_value = None
        service = AgentService(mock_storage)
        result = await service.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_agents(self, mock_storage, sample_agent):
        """list_agents should return list of agents."""
        mock_storage.list_agents.return_value = [sample_agent]
        service = AgentService(mock_storage)
        result = await service.list_by_user("user-1", 0, 10)
        assert len(result) == 1
        assert result[0].name == "test-agent"

    @pytest.mark.asyncio
    async def test_list_agents_with_pagination(self, mock_storage, sample_agent):
        """list_agents should respect offset and limit."""
        mock_storage.list_agents.return_value = [sample_agent]
        service = AgentService(mock_storage)
        result = await service.list_by_user("user-1", 5, 20)
        mock_storage.list_agents.assert_called_with("user-1", 5, 20)

    @pytest.mark.asyncio
    async def test_update_agent_skill_ids(self, mock_storage, sample_agent):
        """Updating skill_ids should work through update method."""
        mock_storage.get_agent.return_value = sample_agent
        service = AgentService(mock_storage)
        new_skill_ids = ["skill-1", "skill-2"]
        result = await service.update(sample_agent.id, {"skill_ids": new_skill_ids})
        assert result.skill_ids == new_skill_ids