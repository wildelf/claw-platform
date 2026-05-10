import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_get_agent_memories():
    from app.main import app

    # Mock MemoryPersistence - it's imported inside the route function
    mock_persistence = MagicMock()
    mock_persistence.get_all_memories = AsyncMock(return_value={
        "MEMORY.md": "# Test Memory\n记住这个",
        "USER.md": "# User Preferences\n中文"
    })

    with patch("app.application.memory.memory_persistence.MemoryPersistence", return_value=mock_persistence):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/agents/agent-123/memories")
            assert response.status_code == 200
            data = response.json()
            assert "MEMORY.md" in data
            assert "USER.md" in data

@pytest.mark.asyncio
async def test_search_memories_returns_empty():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/agents/agent-123/memories/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["results"] == []