"""Tests for tool service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.tool_service import ToolService
from app.domain.tool import Tool, ToolType
from app.domain.base import EntityId


@pytest.fixture
def mock_storage():
    """Create a mock storage."""
    storage = MagicMock()
    storage.get_tool = AsyncMock()
    storage.save_tool = AsyncMock(return_value=None)
    storage.delete_tool = AsyncMock(return_value=None)
    storage.list_tools = AsyncMock(return_value=[])
    return storage


@pytest.fixture
def sample_tool():
    """Create a sample tool for testing."""
    return Tool(
        name="test-tool",
        description="A test tool",
        type=ToolType.CUSTOM,
        user_id=EntityId.generate(),
    )


@pytest.fixture
def sample_mcp_tool():
    """Create a sample MCP tool for testing."""
    return Tool(
        name="mcp-tool",
        description="An MCP tool",
        type=ToolType.MCP,
        config={"command": "npx", "args": ["-y", "some-tool"]},
        user_id=EntityId.generate(),
    )


class TestToolService:
    """Tests for ToolService."""

    @pytest.mark.asyncio
    async def test_create_tool(self, mock_storage, sample_tool):
        """Creating a tool should save it to storage."""
        service = ToolService(mock_storage)
        result = await service.create(sample_tool)
        assert result.name == sample_tool.name
        mock_storage.save_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tool_returns_none_when_not_found(self, mock_storage):
        """get_tool should return None for non-existent tool."""
        mock_storage.get_tool.return_value = None
        service = ToolService(mock_storage)
        result = await service.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_tool_returns_tool(self, mock_storage, sample_tool):
        """get_tool should return tool when found."""
        mock_storage.get_tool.return_value = sample_tool
        service = ToolService(mock_storage)
        result = await service.get(sample_tool.id)
        assert result == sample_tool

    @pytest.mark.asyncio
    async def test_update_tool(self, mock_storage, sample_tool):
        """Updating a tool should save it."""
        mock_storage.get_tool.return_value = sample_tool
        service = ToolService(mock_storage)
        result = await service.update(sample_tool.id, {"name": "updated-name"})
        assert result.name == "updated-name"
        mock_storage.save_tool.assert_called()

    @pytest.mark.asyncio
    async def test_update_tool_returns_none_when_not_found(self, mock_storage):
        """update_tool should return None for non-existent tool."""
        mock_storage.get_tool.return_value = None
        service = ToolService(mock_storage)
        result = await service.update("nonexistent", {"name": "test"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_tool_returns_true_when_found(self, mock_storage, sample_tool):
        """delete_tool should return True when tool exists."""
        mock_storage.get_tool.return_value = sample_tool
        mock_storage.delete_tool.return_value = True
        service = ToolService(mock_storage)
        result = await service.delete(sample_tool.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_tool_returns_false_when_not_found(self, mock_storage):
        """delete_tool should return False when tool doesn't exist."""
        mock_storage.get_tool.return_value = None
        service = ToolService(mock_storage)
        result = await service.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_tools(self, mock_storage, sample_tool):
        """list_tools should return list of tools."""
        mock_storage.list_tools.return_value = [sample_tool]
        service = ToolService(mock_storage)
        result = await service.list_by_user("user-1")
        assert len(result) == 1
        assert result[0].name == "test-tool"

    @pytest.mark.asyncio
    async def test_list_tools_empty(self, mock_storage):
        """list_tools should return empty list when no tools."""
        mock_storage.list_tools.return_value = []
        service = ToolService(mock_storage)
        result = await service.list_by_user("user-1")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_mcp_tool_config(self, mock_storage, sample_mcp_tool):
        """MCP tool should have config with command and args."""
        mock_storage.get_tool.return_value = sample_mcp_tool
        service = ToolService(mock_storage)
        result = await service.get(sample_mcp_tool.id)
        assert result.type == ToolType.MCP
        assert "command" in result.config


class TestToolType:
    """Tests for ToolType enum."""

    def test_custom_type_value(self):
        """Custom type should have correct value."""
        assert ToolType.CUSTOM.value == "custom"

    def test_mcp_type_value(self):
        """MCP type should have correct value."""
        assert ToolType.MCP.value == "mcp"

    def test_all_tool_types_defined(self):
        """All expected tool types should be defined."""
        assert hasattr(ToolType, "CUSTOM")
        assert hasattr(ToolType, "MCP")