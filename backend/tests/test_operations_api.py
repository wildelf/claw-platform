"""Tests for Operations API and HeartbeatManager extensions."""

import json
import time

import pytest

from app.infrastructure.heartbeat import HeartbeatManager
from app.infrastructure.redis_client import reset_redis_client


# ---------------------------------------------------------------------------
# HeartbeatManager Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestHeartbeatManagerWorkerInfo:
    """Tests for worker info methods."""

    def setup_method(self):
        """Reset Redis client for each test to avoid event loop issues."""
        reset_redis_client()

    async def test_set_and_get_worker_start(self):
        """Test recording and retrieving worker start time."""
        mgr = HeartbeatManager()
        worker_id = "test-worker-start"
        try:
            await mgr.set_worker_start(worker_id)
            start_time = await mgr.get_worker_start(worker_id)
            assert start_time is not None
            assert start_time <= time.time()
        finally:
            redis = await mgr._get_redis()
            await redis.delete(mgr.WORKER_START_KEY.format(worker_id))

    async def test_get_worker_info_offline(self):
        """Test worker info when no heartbeat exists."""
        mgr = HeartbeatManager()
        worker_id = "test-worker-offline"
        try:
            redis = await mgr._get_redis()
            await redis.sadd(mgr.WORKER_REGISTRY_KEY, worker_id)

            info = await mgr.get_worker_info(worker_id)
            assert info["worker_id"] == worker_id
            assert info["status"] == "offline"
            assert info["last_heartbeat"] is None
        finally:
            redis = await mgr._get_redis()
            await redis.srem(mgr.WORKER_REGISTRY_KEY, worker_id)

    async def test_get_worker_info_online(self):
        """Test worker info when heartbeat is recent."""
        mgr = HeartbeatManager()
        worker_id = "test-worker-online"
        try:
            await mgr.register_worker(worker_id)
            info = await mgr.get_worker_info(worker_id)
            assert info["worker_id"] == worker_id
            assert info["status"] == "online"
            assert info["last_heartbeat_seconds_ago"] is not None
            assert info["last_heartbeat_seconds_ago"] < 60
        finally:
            await mgr.deregister_worker(worker_id)

    async def test_get_worker_info_stale(self):
        """Test worker info when heartbeat is expired."""
        mgr = HeartbeatManager()
        worker_id = "test-worker-stale"
        try:
            await mgr.register_worker(worker_id)

            redis = await mgr._get_redis()
            old_time = time.time() - 120
            await redis.set(
                mgr.WORKER_HEARTBEAT_KEY.format(worker_id),
                str(old_time),
                ex=120,
            )

            info = await mgr.get_worker_info(worker_id, stale_threshold=60)
            assert info["status"] == "stale"
            assert info["last_heartbeat_seconds_ago"] > 60
        finally:
            await mgr.deregister_worker(worker_id)


@pytest.mark.asyncio
class TestHeartbeatManagerQueueOps:
    """Tests for queue operations."""

    def setup_method(self):
        """Reset Redis client for each test to avoid event loop issues."""
        reset_redis_client()

    async def _clean_queues(self, mgr):
        """Helper to clean queue keys."""
        redis = await mgr._get_redis()
        await redis.delete(mgr.TASK_QUEUE_KEY)
        await redis.delete(mgr.TASK_PROCESSING_KEY)

    async def test_push_and_list_tasks(self):
        """Test pushing tasks and listing them."""
        mgr = HeartbeatManager()
        await self._clean_queues(mgr)
        try:
            await mgr.push_task({
                "task_id": "task-1",
                "agent_id": "agent-1",
                "task": "Test task 1",
                "created_at": time.time(),
            })
            await mgr.push_task({
                "task_id": "task-2",
                "agent_id": "agent-2",
                "task": "Test task 2",
                "created_at": time.time(),
            })

            tasks = await mgr.list_tasks(status_filter="queued")
            assert len(tasks) == 2
            task_ids = {t["task_id"] for t in tasks}
            assert "task-1" in task_ids
            assert "task-2" in task_ids
        finally:
            await self._clean_queues(mgr)

    async def test_list_tasks_with_filter(self):
        """Test listing tasks with status filter."""
        mgr = HeartbeatManager()
        await self._clean_queues(mgr)
        try:
            await mgr.push_task({
                "task_id": "task-q1",
                "agent_id": "agent-1",
                "task": "Queued task",
                "created_at": time.time(),
            })

            queued = await mgr.list_tasks(status_filter="queued")
            assert len(queued) >= 1

            processing = await mgr.list_tasks(status_filter="processing")
            assert len(processing) == 0
        finally:
            await self._clean_queues(mgr)

    async def test_clear_queue(self):
        """Test clearing all queued tasks."""
        mgr = HeartbeatManager()
        await self._clean_queues(mgr)
        try:
            await mgr.push_task({
                "task_id": "task-clear-1",
                "agent_id": "agent-1",
                "task": "Task to clear",
                "created_at": time.time(),
            })
            await mgr.push_task({
                "task_id": "task-clear-2",
                "agent_id": "agent-1",
                "task": "Another task to clear",
                "created_at": time.time(),
            })

            cleared = await mgr.clear_queue()
            assert cleared == 2

            tasks = await mgr.list_tasks(status_filter="queued")
            assert len(tasks) == 0
        finally:
            await self._clean_queues(mgr)

    async def test_cancel_queued_task(self):
        """Test cancelling a queued task."""
        mgr = HeartbeatManager()
        await self._clean_queues(mgr)
        try:
            await mgr.push_task({
                "task_id": "task-cancel-q",
                "agent_id": "agent-1",
                "task": "Task to cancel",
                "created_at": time.time(),
            })

            result = await mgr.cancel_task("task-cancel-q")
            assert result["cancelled"] is True
            assert "cancelled" in result["message"].lower()
        finally:
            await self._clean_queues(mgr)

    async def test_cancel_nonexistent_task(self):
        """Test cancelling a task that doesn't exist."""
        mgr = HeartbeatManager()
        await self._clean_queues(mgr)
        result = await mgr.cancel_task("nonexistent-task-id")
        assert result["cancelled"] is False
        assert "not found" in result["message"].lower()

    async def test_get_queue_stats(self):
        """Test queue statistics."""
        mgr = HeartbeatManager()
        await self._clean_queues(mgr)
        try:
            await mgr.push_task({
                "task_id": "task-stat-1",
                "agent_id": "agent-1",
                "task": "Stat task",
                "created_at": time.time(),
            })

            stats = await mgr.get_queue_stats()
            assert "queued" in stats
            assert "processing" in stats
            assert "completed_today" in stats
            assert "failed_today" in stats
            assert "success_rate" in stats
            assert stats["queued"] >= 1
        finally:
            await self._clean_queues(mgr)


@pytest.mark.asyncio
class TestHeartbeatManagerWorkerSignal:
    """Tests for worker signal management."""

    def setup_method(self):
        """Reset Redis client for each test."""
        reset_redis_client()

    async def test_set_worker_signal(self):
        """Test setting a worker signal."""
        mgr = HeartbeatManager()
        worker_id = "test-worker-signal"
        await mgr.set_worker_signal(worker_id, "restart")

        redis = await mgr._get_redis()
        signal_key = mgr.WORKER_SIGNAL_KEY.format(worker_id)
        val = await redis.get(signal_key)
        assert val is not None
        signal_val = val.decode() if isinstance(val, bytes) else val
        assert signal_val == "restart"

        await redis.delete(signal_key)


# ---------------------------------------------------------------------------
# Operations API Tests
# ---------------------------------------------------------------------------


class TestOperationsAPI:
    """Tests for Operations API endpoints."""

    def setup_method(self):
        """Reset Redis client between tests."""
        reset_redis_client()

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, auth_service):
        """Generate auth headers."""
        token = auth_service.create_access_token(
            user_id="test-ops-user",
            username="opsuser",
            role="user",
        )
        return {"Authorization": f"Bearer {token}"}

    def test_get_worker_status_offline(self, client, auth_headers):
        """Test worker status when no worker is registered."""
        response = client.get("/api/operations/worker/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "offline"
        assert data["worker_id"] is None

    def test_get_queue_stats(self, client, auth_headers):
        """Test queue statistics endpoint."""
        response = client.get("/api/operations/queue/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "queued" in data
        assert "processing" in data
        assert "completed_today" in data

    def test_list_tasks(self, client, auth_headers):
        """Test listing tasks."""
        response = client.get("/api/operations/tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data

    def test_list_tasks_with_status_filter(self, client, auth_headers):
        """Test listing tasks with status filter."""
        response = client.get("/api/operations/tasks?status=queued", headers=auth_headers)
        assert response.status_code == 200

    def test_list_tasks_with_limit(self, client, auth_headers):
        """Test listing tasks with limit."""
        response = client.get("/api/operations/tasks?limit=10", headers=auth_headers)
        assert response.status_code == 200

    def test_clear_queue(self, client, auth_headers):
        """Test clearing the queue."""
        response = client.post("/api/operations/queue/clear", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "cleared_count" in data
        assert "message" in data

    def test_cancel_nonexistent_task(self, client, auth_headers):
        """Test cancelling a task that doesn't exist."""
        response = client.post(
            "/api/operations/tasks/nonexistent-id/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_restart_worker_no_worker(self, client, auth_headers):
        """Test restarting worker when none is registered."""
        response = client.post("/api/operations/worker/restart", headers=auth_headers)
        assert response.status_code == 404

    def test_stop_worker_no_worker(self, client, auth_headers):
        """Test stopping worker when none is registered."""
        response = client.post("/api/operations/worker/stop", headers=auth_headers)
        assert response.status_code == 404
