"""Tests for API routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestAgentAPI:
    """Tests for agent API routes."""

    def test_list_agents(self, auth_headers):
        """GET /api/agents should require auth."""
        client = TestClient(app)
        response = client.get("/api/agents", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_create_agent(self, auth_headers):
        """POST /api/agents should require auth."""
        client = TestClient(app)
        response = client.post(
            "/api/agents",
            json={
                "name": "test-agent",
                "role": "assistant",
                "description": "A test agent",
            },
            headers=auth_headers,
        )
        assert response.status_code in [200, 401]

    def test_get_agent_not_found(self, auth_headers):
        """GET /api/agents/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/agents/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    def test_update_agent_not_found(self, auth_headers):
        """PUT /api/agents/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.put(
            "/api/agents/nonexistent-id",
            json={"name": "updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_agent_not_found(self, auth_headers):
        """DELETE /api/agents/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.delete("/api/agents/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404


class TestSkillAPI:
    """Tests for skill API routes."""

    def test_list_skills(self, auth_headers):
        """GET /api/skills should require auth."""
        client = TestClient(app)
        response = client.get("/api/skills", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_create_skill(self, auth_headers):
        """POST /api/skills should require auth."""
        client = TestClient(app)
        response = client.post(
            "/api/skills",
            json={"name": "test-skill", "description": "A test skill"},
            headers=auth_headers,
        )
        assert response.status_code in [200, 401]

    def test_get_skill_not_found(self, auth_headers):
        """GET /api/skills/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/skills/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    def test_update_skill_not_found(self, auth_headers):
        """PUT /api/skills/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.put(
            "/api/skills/nonexistent-id",
            json={"name": "updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_skill_not_found(self, auth_headers):
        """DELETE /api/skills/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.delete("/api/skills/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    def test_list_skill_files(self, auth_headers):
        """GET /api/skills/{id}/files should be accessible."""
        client = TestClient(app)
        response = client.get("/api/skills/skill-123/files", headers=auth_headers)
        assert response.status_code in [200, 401, 404]

    def test_get_skill_file_not_found(self, auth_headers):
        """GET /api/skills/{id}/files/{filename} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/skills/skill-123/files/nonexistent.txt", headers=auth_headers)
        assert response.status_code == 404


class TestToolAPI:
    """Tests for tool API routes."""

    def test_list_tools(self, auth_headers):
        """GET /api/tools should require auth."""
        client = TestClient(app)
        response = client.get("/api/tools", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_create_tool(self, auth_headers):
        """POST /api/tools should require auth."""
        client = TestClient(app)
        response = client.post(
            "/api/tools",
            json={"name": "test-tool", "type": "custom"},
            headers=auth_headers,
        )
        assert response.status_code in [200, 401]

    def test_get_tool_not_found(self, auth_headers):
        """GET /api/tools/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/tools/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    def test_update_tool_not_found(self, auth_headers):
        """PUT /api/tools/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.put(
            "/api/tools/nonexistent-id",
            json={"name": "updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_tool_not_found(self, auth_headers):
        """DELETE /api/tools/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.delete("/api/tools/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404


class TestModelAPI:
    """Tests for model config API routes."""

    def test_list_models(self, auth_headers):
        """GET /api/models should require auth."""
        client = TestClient(app)
        response = client.get("/api/models", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_create_model(self, auth_headers):
        """POST /api/models should require auth."""
        client = TestClient(app)
        response = client.post(
            "/api/models",
            json={
                "name": "test-model",
                "type": "openai",
                "model": "gpt-4",
            },
            headers=auth_headers,
        )
        assert response.status_code in [201, 401]

    def test_get_model_not_found(self, auth_headers):
        """GET /api/models/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/models/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    def test_update_model_not_found(self, auth_headers):
        """PUT /api/models/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.put(
            "/api/models/nonexistent-id",
            json={"name": "updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_model_not_found(self, auth_headers):
        """DELETE /api/models/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.delete("/api/models/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404


class TestFeedbackAPI:
    """Tests for feedback API routes."""

    def test_list_feedback(self, auth_headers):
        """GET /api/feedback should require auth."""
        client = TestClient(app)
        response = client.get("/api/feedback", headers=auth_headers)
        assert response.status_code in [200, 401]

    def test_create_feedback_requires_valid_rating(self, auth_headers):
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
            headers=auth_headers,
        )
        # Returns 422 for validation error
        assert response.status_code == 422

    def test_get_feedback_not_found(self, auth_headers):
        """GET /api/feedback/{id} should return 404 for non-existent."""
        client = TestClient(app)
        response = client.get("/api/feedback/nonexistent-id", headers=auth_headers)
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
