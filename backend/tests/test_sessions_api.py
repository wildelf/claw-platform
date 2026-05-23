"""Integration tests for sessions API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.api import api_router
import tempfile
from pathlib import Path

from fastapi import FastAPI
from app.api.deps import get_storage, get_current_user


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


@pytest_asyncio.fixture
async def test_app(temp_db):
    """Create test app with in-memory storage."""
    app = FastAPI()
    app.include_router(api_router)

    storage = SQLiteStorage(temp_db)
    await storage.init_db()

    # Create a test user
    from app.application.auth_service import AuthService
    auth_service = AuthService()
    test_user = auth_service.create_user(
        username="testuser",
        email="test@example.com",
        password="password123",
    )
    await storage.save_user(test_user)

    # Create test agents owned by the test user
    from app.domain.agent import Agent
    from app.domain.base import EntityId
    test_agents = {
        "agent-123": Agent(
            id=EntityId("agent-123"),
            name="Test Agent 1",
            role="test",
            goal="testing",
            user_id=test_user.id,
        ),
        "agent-456": Agent(
            id=EntityId("agent-456"),
            name="Test Agent 2",
            role="test",
            goal="testing",
            user_id=test_user.id,
        ),
    }
    for agent in test_agents.values():
        await storage.save_agent(agent)

    async def override_get_storage():
        return storage

    async def override_get_current_user():
        """Fake authenticated user for tests."""
        from app.api.deps import AuthContext
        return AuthContext(
            user_id=test_user.id,
            username="testuser",
            role="user",
        )

    app.dependency_overrides[get_storage] = override_get_storage
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield app, storage


@pytest_asyncio.fixture
async def client(test_app):
    """Create test client."""
    app, _ = test_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCreateSession:
    """Tests for POST /sessions."""

    @pytest.mark.asyncio
    async def test_create_session_with_name(self, client):
        """Create session with name returns 201 and session data."""
        response = await client.post("/sessions", json={
            "agent_id": "agent-123",
            "name": "My Test Session",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == "agent-123"
        assert data["name"] == "My Test Session"
        assert data["message_count"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_session_without_name(self, client):
        """Create session without name returns 201 with auto-generated name."""
        response = await client.post("/sessions", json={
            "agent_id": "agent-456",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == "agent-456"
        assert data["name"] in (None, "")
        assert data["message_count"] == 0


class TestListSessions:
    """Tests for GET /sessions."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client):
        """List sessions when empty returns empty list."""
        response = await client.get("/sessions")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, client):
        """List sessions returns created sessions."""
        # Create two sessions using pre-created agents
        await client.post("/sessions", json={"agent_id": "agent-123", "name": "Session 1"})
        await client.post("/sessions", json={"agent_id": "agent-456", "name": "Session 2"})

        response = await client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_pagination(self, client):
        """List sessions with pagination works correctly."""
        # Create 5 sessions using pre-created agents
        agent_ids = ["agent-123", "agent-456"]
        for i in range(5):
            agent_id = agent_ids[i % 2]
            await client.post("/sessions", json={"agent_id": agent_id, "name": f"Session {i}"})

        # Get first 2
        response = await client.get("/sessions", params={"offset": 0, "limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get next 2
        response = await client.get("/sessions", params={"offset": 2, "limit": 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestGetSession:
    """Tests for GET /sessions/{session_id}."""

    @pytest.mark.asyncio
    async def test_get_session_success(self, client):
        """Get existing session returns 200 and session data."""
        # Create a session
        create_response = await client.post("/sessions", json={
            "agent_id": "agent-123",
            "name": "Get Test Session",
        })
        session_id = create_response.json()["id"]

        # Get the session
        response = await client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["name"] == "Get Test Session"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client):
        """Get non-existent session returns 404."""
        response = await client.get("/sessions/nonexistent-id")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


class TestUpdateSession:
    """Tests for PATCH /sessions/{session_id}."""

    @pytest.mark.asyncio
    async def test_update_session_success(self, client):
        """Update session name returns 200 and updated data."""
        # Create a session
        create_response = await client.post("/sessions", json={
            "agent_id": "agent-123",
            "name": "Original Name",
        })
        session_id = create_response.json()["id"]

        # Update the session
        response = await client.patch(f"/sessions/{session_id}", json={
            "name": "Updated Name",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, client):
        """Update non-existent session returns 404."""
        response = await client.patch("/sessions/nonexistent-id", json={
            "name": "New Name",
        })
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


class TestDeleteSession:
    """Tests for DELETE /sessions/{session_id}."""

    @pytest.mark.asyncio
    async def test_delete_session_success(self, client):
        """Delete session returns 200 and session is gone."""
        # Create a session
        create_response = await client.post("/sessions", json={
            "agent_id": "agent-123",
            "name": "To Be Deleted",
        })
        session_id = create_response.json()["id"]

        # Delete the session
        response = await client.delete(f"/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json() == {"ok": True}

        # Verify it's gone
        get_response = await client.get(f"/sessions/{session_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, client):
        """Delete non-existent session returns 200 (idempotent)."""
        response = await client.delete("/sessions/nonexistent-id")
        # DELETE is typically idempotent, returns 200 even if not found
        assert response.status_code == 200
        assert response.json() == {"ok": True}