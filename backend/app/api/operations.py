"""Operations API — Worker monitoring and task management.

Endpoints under /api/operations for:
- Worker status and control (heartbeat, restart, stop)
- Queue statistics and management
- Task listing and cancellation

Data source: Redis (worker heartbeat, task queue) + SQLite (agent info).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import Storage
from app.application.agent_service import AgentService
from app.config import settings
from app.infrastructure.heartbeat import HeartbeatManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operations", tags=["operations"])


# ---------------------------------------------------------------------------
# Worker endpoints
# ---------------------------------------------------------------------------


@router.get("/worker/status")
async def get_worker_status(
    storage: Storage,
):
    """Get the status of the active worker daemon.

    Returns the first registered worker's status (single-node for Phase 1).
    """
    heartbeat_mgr = HeartbeatManager()
    workers = await heartbeat_mgr.get_all_workers_info(
        stale_threshold=getattr(settings.worker, "stale_threshold", 60),
    )

    if not workers:
        return {
            "worker_id": None,
            "status": "offline",
            "last_heartbeat": None,
            "last_heartbeat_seconds_ago": None,
            "started_at": None,
            "uptime_seconds": None,
            "redis_connection": f"{settings.redis.host}:{settings.redis.port}",
        }

    # Single-node: return the first worker
    return workers[0]


@router.post("/worker/restart")
async def restart_worker():
    """Send a restart signal to the worker daemon.

    The worker checks this signal in its heartbeat loop and exits gracefully.
    The process manager (systemd/supervisor) will restart it automatically.
    """
    heartbeat_mgr = HeartbeatManager()
    workers = await heartbeat_mgr.get_all_workers_info()

    if not workers:
        raise HTTPException(status_code=404, detail="No worker registered")

    worker_id = workers[0]["worker_id"]
    await heartbeat_mgr.set_worker_signal(worker_id, "restart")

    return {
        "restarting": True,
        "message": "Worker restart signal sent",
    }


@router.post("/worker/stop")
async def stop_worker():
    """Send a stop signal to the worker daemon.

    The worker checks this signal in its heartbeat loop and exits.
    """
    heartbeat_mgr = HeartbeatManager()
    workers = await heartbeat_mgr.get_all_workers_info()

    if not workers:
        raise HTTPException(status_code=404, detail="No worker registered")

    worker_id = workers[0]["worker_id"]
    await heartbeat_mgr.set_worker_signal(worker_id, "stop")

    return {
        "stopping": True,
        "message": "Worker stop signal sent",
    }


# ---------------------------------------------------------------------------
# Queue endpoints
# ---------------------------------------------------------------------------


@router.get("/queue/stats")
async def get_queue_stats():
    """Get task queue statistics."""
    heartbeat_mgr = HeartbeatManager()
    stats = await heartbeat_mgr.get_queue_stats()
    return stats


@router.post("/queue/clear")
async def clear_queue():
    """Clear all pending tasks from the queue.

    Only affects queued tasks (task:queue), not processing tasks.
    """
    heartbeat_mgr = HeartbeatManager()
    cleared_count = await heartbeat_mgr.clear_queue()
    return {
        "cleared_count": cleared_count,
        "message": f"Cleared {cleared_count} tasks",
    }


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(
        default=None,
        description="Filter by status: queued/processing/completed/failed",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Max number of tasks to return",
    ),
    storage: Storage = None,
):
    """List tasks from the queue and processing lists.

    Optionally enriches tasks with agent names from the database.
    """
    heartbeat_mgr = HeartbeatManager()
    tasks = await heartbeat_mgr.list_tasks(status_filter=status, limit=limit)

    # Enrich with agent names
    agent_service = AgentService(storage)
    agent_cache = {}
    for task in tasks:
        agent_id = task.get("agent_id")
        if agent_id and agent_id not in agent_cache:
            agent = await agent_service.get(agent_id)
            agent_cache[agent_id] = agent.name if agent else None
        if agent_id and agent_id in agent_cache:
            task["agent_name"] = agent_cache[agent_id]

    return {
        "tasks": tasks,
        "total": len(tasks),
    }


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a task.

    - Queued tasks: immediately removed from queue, marked cancelled.
    - Processing tasks: cancel flag set, worker will detect and stop.
    - Completed/failed tasks: return 404.
    """
    heartbeat_mgr = HeartbeatManager()
    result = await heartbeat_mgr.cancel_task(task_id)

    if not result.get("cancelled") and result.get("message") == "Task not found":
        raise HTTPException(status_code=404, detail="Task not found")

    if not result.get("cancelled") and "Cannot cancel" in result.get("message", ""):
        raise HTTPException(status_code=404, detail=result["message"])

    return result
