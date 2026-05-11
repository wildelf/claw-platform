import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from app.application.memory.memory_search import MemorySearch, SearchResult


@pytest.mark.asyncio
async def test_search_returns_results():
    mock_storage = MagicMock()
    mock_storage.search_memories = AsyncMock(return_value=[
        {
            "agent_id": "agent-123",
            "memory_type": "MEMORY.md",
            "content": "记住这个重要配置",
            "session_id": "session-456",
            "created_at": "2026-05-12T00:00:00",
            "rank": -1.5,
        }
    ])

    search = MemorySearch(storage=mock_storage)
    results = await search.search(agent_id="agent-123", query="配置", limit=10)

    assert len(results) == 1
    assert results[0].memory_type == "MEMORY.md"
    assert "配置" in results[0].content
    assert results[0].relevance_score == -1.5


@pytest.mark.asyncio
async def test_search_empty_results():
    mock_storage = MagicMock()
    mock_storage.search_memories = AsyncMock(return_value=[])

    search = MemorySearch(storage=mock_storage)
    results = await search.search(agent_id="agent-123", query="notfound", limit=10)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_index_memory():
    mock_storage = MagicMock()
    mock_storage.index_memory = AsyncMock()

    search = MemorySearch(storage=mock_storage)
    await search.index_memory(
        agent_id="agent-123",
        memory_type="MEMORY.md",
        content="测试内容",
        session_id="session-456",
    )

    mock_storage.index_memory.assert_called_once()