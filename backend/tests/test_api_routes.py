"""Tests for API routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestAgentAPI:
    """Tests for agent API routes."""

    def test_list_agents(self):
        """GET /api/agents should be accessible."""
        client = TestClient(app)
        response = client.get("/api/agents")
        # Just verify the endpoint is accessible (returns 200 or auth error)
        assert response.status_code in [200, 401]

    def test_create_agent(self):
        """POST /api/agents should be accessible."""
        client = TestClient(app)
        response = client.post(
            "/api/agents",
            json={
                "name": "test-agent",
                "role": "assistant",
                "description": "A test agent",
            },
        )
        # Returns 200 if auth passes
        assert response.status_code in [200, 401]

    def test_get_agent_not_found(self):
        """GET /api/agents/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/agents/nonexistent-id")
        assert response.status_code == 404

    def test_update_agent_not_found(self):
        """PUT /api/agents/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.put(
            "/api/agents/nonexistent-id",
            json={"name": "updated"},
        )
        assert response.status_code == 404

    def test_delete_agent_not_found(self):
        """DELETE /api/agents/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.delete("/api/agents/nonexistent-id")
        assert response.status_code == 404


class TestSkillAPI:
    """Tests for skill API routes."""

    def test_list_skills(self):
        """GET /api/skills should be accessible."""
        client = TestClient(app)
        response = client.get("/api/skills")
        assert response.status_code in [200, 401]

    def test_create_skill(self):
        """POST /api/skills should be accessible."""
        client = TestClient(app)
        response = client.post(
            "/api/skills",
            json={"name": "test-skill", "description": "A test skill"},
        )
        assert response.status_code in [200, 401]

    def test_get_skill_not_found(self):
        """GET /api/skills/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/skills/nonexistent-id")
        assert response.status_code == 404

    def test_update_skill_not_found(self):
        """PUT /api/skills/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.put(
            "/api/skills/nonexistent-id",
            json={"name": "updated"},
        )
        assert response.status_code == 404

    def test_delete_skill_not_found(self):
        """DELETE /api/skills/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.delete("/api/skills/nonexistent-id")
        assert response.status_code == 404

    def test_list_skill_files(self):
        """GET /api/skills/{id}/files should be accessible."""
        client = TestClient(app)
        response = client.get("/api/skills/skill-123/files")
        assert response.status_code in [200, 401, 404]

    def test_get_skill_file_not_found(self):
        """GET /api/skills/{id}/files/{filename} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/skills/skill-123/files/nonexistent.txt")
        assert response.status_code == 404


class TestToolAPI:
    """Tests for tool API routes."""

    def test_list_tools(self):
        """GET /api/tools should be accessible."""
        client = TestClient(app)
        response = client.get("/api/tools")
        assert response.status_code in [200, 401]

    def test_create_tool(self):
        """POST /api/tools should be accessible."""
        client = TestClient(app)
        response = client.post(
            "/api/tools",
            json={"name": "test-tool", "type": "custom"},
        )
        assert response.status_code in [200, 401]

    def test_get_tool_not_found(self):
        """GET /api/tools/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/tools/nonexistent-id")
        assert response.status_code == 404

    def test_update_tool_not_found(self):
        """PUT /api/tools/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.put(
            "/api/tools/nonexistent-id",
            json={"name": "updated"},
        )
        assert response.status_code == 404

    def test_delete_tool_not_found(self):
        """DELETE /api/tools/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.delete("/api/tools/nonexistent-id")
        assert response.status_code == 404


class TestModelAPI:
    """Tests for model config API routes."""

    def test_list_models(self):
        """GET /api/models should be accessible."""
        client = TestClient(app)
        response = client.get("/api/models")
        assert response.status_code in [200, 401]

    def test_create_model(self):
        """POST /api/models should be accessible."""
        client = TestClient(app)
        response = client.post(
            "/api/models",
            json={
                "name": "test-model",
                "type": "openai",
                "model": "gpt-4",
            },
        )
        assert response.status_code in [200, 401]

    def test_get_model_not_found(self):
        """GET /api/models/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/models/nonexistent-id")
        assert response.status_code == 404

    def test_update_model_not_found(self):
        """PUT /api/models/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.put(
            "/api/models/nonexistent-id",
            json={"name": "updated"},
        )
        assert response.status_code == 404

    def test_delete_model_not_found(self):
        """DELETE /api/models/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.delete("/api/models/nonexistent-id")
        assert response.status_code == 404


class TestFeedbackAPI:
    """Tests for feedback API routes."""

    def test_list_feedback(self):
        """GET /api/feedback should be accessible."""
        client = TestClient(app)
        response = client.get("/api/feedback")
        assert response.status_code in [200, 401]

    def test_create_feedback_requires_valid_rating(self):
        """POST /api/feedback should return 422 for invalid rating."""
        client = TestClient(app)
        response = client.post(
            "/api/feedback",
            json={
                "agent_id": "agent-123",
                "task_id": "task-123",
                "result": "Success",
                "rating": "invalid_rating",
            },
        )
        # Returns 422 for validation error
        assert response.status_code == 422

    def test_get_feedback_not_found(self):
        """GET /api/feedback/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/feedback/nonexistent-id")
        assert response.status_code == 404


class TestHealthAPI:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """GET /health should return health status."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestRootAPI:
    """Tests for root endpoint."""

    def test_root(self):
        """GET / should return 404 (no root endpoint defined)."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 404
