# backend/tests/api/test_scheduled_tasks_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.application.auth_service import AuthService


def get_test_token():
    """Create a valid JWT token for testing."""
    auth_service = AuthService()
    return auth_service.create_access_token(
        user_id="test-user-123",
        username="testuser",
        role="user"
    )


@pytest.mark.asyncio
async def test_create_and_list_scheduled_task():
    token = get_test_token()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create task
        response = await client.post(
            "/api/scheduled-tasks",
            json={
                "name": "Test Scheduled Task",
                "agent_id": "agent-123",
                "schedule_type": "cron",
                "cron_expression": "0 9 * * *",
                "task_input": "Test task"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Scheduled Task"

        # List tasks (with auth header)
        response = await client.get(
            "/api/scheduled-tasks",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1