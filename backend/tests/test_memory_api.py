import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
from app.api.deps import get_current_user


@pytest.mark.asyncio
async def test_get_agent_memories():
    from app.main import app
    from app.api.deps import AuthContext
    from app.domain.base import EntityId

    test_user_id = EntityId("test-user-id")

    # Override auth dependency
    async def override_get_current_user():
        return AuthContext(
            user_id=test_user_id,
            username="testuser",
            role="user",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        # Mock AgentService.get to return an agent owned by the test user
        from app.domain.agent import Agent
        mock_agent = Agent(
            id=EntityId("agent-123"),
            name="Test Agent",
            role="test",
            goal="testing",
            user_id=test_user_id,
        )

        # Mock MemoryPersistence
        mock_persistence = MagicMock()
        mock_persistence.get_all_memories = AsyncMock(return_value={
            "MEMORY.md": "# Test Memory\n记住这个",
            "USER.md": "# User Preferences\n中文"
        })

        with patch("app.api.agents.AgentService") as mock_agent_service_cls:
            mock_service = MagicMock()
            mock_service.get = AsyncMock(return_value=mock_agent)
            mock_agent_service_cls.return_value = mock_service

            with patch("app.application.memory.memory_persistence.MemoryPersistence", return_value=mock_persistence):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/api/agents/agent-123/memories")
                    assert response.status_code == 200
                    data = response.json()
                    assert "MEMORY.md" in data
                    assert "USER.md" in data
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_search_memories_returns_empty():
    from app.main import app
    from app.api.deps import AuthContext
    from app.domain.base import EntityId
    from app.domain.agent import Agent

    test_user_id = EntityId("test-user-id")

    # Override auth dependency
    async def override_get_current_user():
        return AuthContext(
            user_id=test_user_id,
            username="testuser",
            role="user",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        # Mock AgentService.get
        mock_agent = Agent(
            id=EntityId("agent-123"),
            name="Test Agent",
            role="test",
            goal="testing",
            user_id=test_user_id,
        )

        with patch("app.api.agents.AgentService") as mock_agent_service_cls:
            mock_service = MagicMock()
            mock_service.get = AsyncMock(return_value=mock_agent)
            mock_agent_service_cls.return_value = mock_service

            # Mock MemorySearch
            with patch("app.application.memory.memory_search.MemorySearch") as mock_search_cls:
                mock_search = MagicMock()
                mock_search.search = AsyncMock(return_value=[])
                mock_search_cls.return_value = mock_search

                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/api/agents/agent-123/memories/search?q=test")
                    assert response.status_code == 200
                    data = response.json()
                    assert "results" in data
                    assert data["results"] == []
    finally:
        app.dependency_overrides.pop(get_current_user, None)
