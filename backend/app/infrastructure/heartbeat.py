"""Redis-based heartbeat mechanism for worker daemon.

Manages worker registration, heartbeat updates, and stale worker detection.
"""

import time
from typing import List, Optional

from app.infrastructure.redis_client import get_redis_client


class HeartbeatManager:
    """Manages worker heartbeats via Redis."""

    WORKER_HEARTBEAT_KEY = "worker:heartbeat:{}"
    WORKER_REGISTRY_KEY = "worker:registry"
    TASK_QUEUE_KEY = "task:queue"
    TASK_PROCESSING_KEY = "task:processing"
    TASK_RESULT_KEY = "task:result:{}"

    def __init__(self, redis_client=None):
        """Initialize heartbeat manager.

        Args:
            redis_client: Optional Redis client (uses get_redis_client() if not provided)
        """
        self._redis = redis_client

    async def _get_redis(self):
        """Get Redis client."""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis

    async def register_worker(self, worker_id: str) -> None:
        """Register a worker in Redis.

        Args:
            worker_id: Unique worker identifier
        """
        redis = await self._get_redis()
        await redis.sadd(self.WORKER_REGISTRY_KEY, worker_id)
        await self.heartbeat(worker_id)

    async def heartbeat(self, worker_id: str) -> None:
        """Update worker heartbeat.

        Args:
            worker_id: Unique worker identifier
        """
        redis = await self._get_redis()
        now = time.time()
        await redis.set(
            self.WORKER_HEARTBEAT_KEY.format(worker_id),
            str(now),
            ex=120,  # Expire after 120 seconds
        )

    async def deregister_worker(self, worker_id: str) -> None:
        """Deregister a worker from Redis.

        Args:
            worker_id: Unique worker identifier
        """
        redis = await self._get_redis()
        await redis.srem(self.WORKER_REGISTRY_KEY, worker_id)
        await redis.delete(self.WORKER_HEARTBEAT_KEY.format(worker_id))

    async def get_stale_workers(self, threshold_seconds: int = 60) -> List[str]:
        """Find workers with expired heartbeats.

        Args:
            threshold_seconds: Seconds since last heartbeat to consider stale

        Returns:
            List of stale worker IDs
        """
        redis = await self._get_redis()
        now = time.time()

        # Get all registered workers
        worker_ids = await redis.smembers(self.WORKER_REGISTRY_KEY)
        stale_workers = []

        for worker_id in worker_ids:
            last_heartbeat = await redis.get(self.WORKER_HEARTBEAT_KEY.format(worker_id))
            if last_heartbeat is None:
                # No heartbeat recorded
                stale_workers.append(worker_id)
            else:
                last_heartbeat_time = float(last_heartbeat)
                if (now - last_heartbeat_time) > threshold_seconds:
                    stale_workers.append(worker_id)

        return stale_workers

    async def push_task(self, task_data: dict) -> str:
        """Push a task to the queue.

        Args:
            task_data: Task data dict (must include 'task_id')

        Returns:
            Task ID
        """
        import json
        redis = await self._get_redis()
        task_id = task_data.get("task_id")
        await redis.lpush(self.TASK_QUEUE_KEY, json.dumps(task_data))
        return task_id

    async def claim_task(self, worker_id: str, timeout: int = 5) -> Optional[dict]:
        """Claim a task from the queue.

        Uses BRPOPLPUSH to atomically move task from queue to processing.

        Args:
            worker_id: Worker ID claiming the task
            timeout: Timeout in seconds to wait for a task

        Returns:
            Task data dict or None if timeout
        """
        import json
        redis = await self._get_redis()

        # BRPOPLPUSH: pop from queue, push to processing, with timeout
        task_json = await redis.brpoplpush(
            self.TASK_QUEUE_KEY,
            self.TASK_PROCESSING_KEY,
            timeout=timeout,
        )

        if task_json is None:
            return None

        task_data = json.loads(task_json)
        task_data["claimed_by"] = worker_id
        return task_data

    async def complete_task(self, task_id: str, result: dict) -> None:
        """Mark a task as completed.

        Args:
            task_id: Task ID
            result: Task result data
        """
        import json
        redis = await self._get_redis()

        # Remove from processing queue
        # Note: LREM removes all matching items; for production, use a more sophisticated approach
        await redis.lrem(self.TASK_PROCESSING_KEY, 1, json.dumps({"task_id": task_id}))

        # Store result
        await redis.set(
            self.TASK_RESULT_KEY.format(task_id),
            json.dumps({"status": "completed", "result": result}),
            ex=3600,  # Expire after 1 hour
        )

    async def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed and requeue it.

        Args:
            task_id: Task ID
            error: Error message
        """
        import json
        redis = await self._get_redis()

        # Remove from processing
        await redis.lrem(self.TASK_PROCESSING_KEY, 1, json.dumps({"task_id": task_id}))

        # Store error result
        await redis.set(
            self.TASK_RESULT_KEY.format(task_id),
            json.dumps({"status": "failed", "error": error}),
            ex=3600,
        )

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status.

        Args:
            task_id: Task ID

        Returns:
            Task status dict or None
        """
        import json
        redis = await self._get_redis()
        result_json = await redis.get(self.TASK_RESULT_KEY.format(task_id))
        if result_json:
            return json.loads(result_json)

        # Check if still processing
        # This is a simplified check - in production, use a more sophisticated approach
        return {"status": "pending"}

    async def recover_tasks_for_worker(self, worker_id: str) -> List[dict]:
        """Recover uncompleted tasks for a stale worker.

        Moves tasks from processing back to queue.

        Args:
            worker_id: Stale worker ID

        Returns:
            List of recovered task data
        """
        import json
        redis = await self._get_redis()

        # Get all tasks in processing queue
        tasks = await redis.lrange(self.TASK_PROCESSING_KEY, 0, -1)
        recovered = []

        for task_json in tasks:
            task_data = json.loads(task_json)
            if task_data.get("claimed_by") == worker_id:
                # Requeue this task
                await redis.lrem(self.TASK_PROCESSING_KEY, 1, task_json)
                await redis.lpush(self.TASK_QUEUE_KEY, task_json)
                recovered.append(task_data)

        return recovered

    # --- Operations API support methods ---

    WORKER_START_KEY = "worker:start_time:{}"
    WORKER_SIGNAL_KEY = "worker:signal:{}"

    async def set_worker_start(self, worker_id: str) -> None:
        """Record worker start time."""
        redis = await self._get_redis()
        await redis.set(
            self.WORKER_START_KEY.format(worker_id),
            str(time.time()),
        )

    async def get_worker_start(self, worker_id: str) -> Optional[float]:
        """Get worker start time."""
        redis = await self._get_redis()
        val = await redis.get(self.WORKER_START_KEY.format(worker_id))
        if val:
            return float(val)
        return None

    async def get_worker_info(self, worker_id: str, stale_threshold: int = 60) -> dict:
        """Get detailed worker status.

        Args:
            worker_id: Worker ID
            stale_threshold: Seconds to consider stale

        Returns:
            Worker status dict
        """
        redis = await self._get_redis()
        now = time.time()

        last_heartbeat_raw = await redis.get(self.WORKER_HEARTBEAT_KEY.format(worker_id))
        start_time_raw = await redis.get(self.WORKER_START_KEY.format(worker_id))

        last_heartbeat = None
        last_heartbeat_seconds_ago = None
        started_at = None
        uptime_seconds = None

        if last_heartbeat_raw:
            last_heartbeat_ts = float(last_heartbeat_raw)
            last_heartbeat = last_heartbeat_ts
            last_heartbeat_seconds_ago = round(now - last_heartbeat_ts, 1)

        if start_time_raw:
            started_at_ts = float(start_time_raw)
            started_at = started_at_ts
            uptime_seconds = round(now - started_at_ts, 1)

        # Determine status
        if last_heartbeat is None:
            status = "offline"
        elif last_heartbeat_seconds_ago is not None and last_heartbeat_seconds_ago > stale_threshold:
            status = "stale"
        else:
            status = "online"

        redis_cfg = redis.connection_pool.connection_kwargs
        redis_connection = f"{redis_cfg.get('host', 'localhost')}:{redis_cfg.get('port', 6379)}"

        return {
            "worker_id": worker_id,
            "status": status,
            "last_heartbeat": last_heartbeat,
            "last_heartbeat_seconds_ago": last_heartbeat_seconds_ago,
            "started_at": started_at,
            "uptime_seconds": uptime_seconds,
            "redis_connection": redis_connection,
        }

    async def get_all_workers_info(self, stale_threshold: int = 60) -> List[dict]:
        """Get status for all registered workers."""
        redis = await self._get_redis()
        worker_ids = await redis.smembers(self.WORKER_REGISTRY_KEY)
        workers = []
        for wid in worker_ids:
            info = await self.get_worker_info(wid, stale_threshold)
            workers.append(info)
        return workers

    async def get_queue_stats(self) -> dict:
        """Get task queue statistics.

        Returns:
            Queue stats dict
        """
        import json
        redis = await self._get_redis()

        queued_count = await redis.llen(self.TASK_QUEUE_KEY)
        processing_count = await redis.llen(self.TASK_PROCESSING_KEY)

        # Scan for completed/failed results
        completed_today = 0
        failed_today = 0
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match="task:result:*", count=100)
            for key in keys:
                result_json = await redis.get(key)
                if result_json:
                    try:
                        result = json.loads(result_json)
                        if result.get("status") == "completed":
                            completed_today += 1
                        elif result.get("status") == "failed":
                            failed_today += 1
                    except (json.JSONDecodeError, TypeError):
                        pass
            if cursor == 0:
                break

        total = completed_today + failed_today
        success_rate = round(completed_today / total, 2) if total > 0 else 0.0

        return {
            "queued": queued_count,
            "processing": processing_count,
            "completed_today": completed_today,
            "failed_today": failed_today,
            "success_rate": success_rate,
        }

    async def list_tasks(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """List tasks from queue and processing.

        Args:
            status_filter: Optional filter (queued/processing/completed/failed)
            limit: Max number of tasks to return

        Returns:
            List of task dicts
        """
        import json
        redis = await self._get_redis()
        tasks = []

        # Queued tasks
        if status_filter is None or status_filter == "queued":
            queued_items = await redis.lrange(self.TASK_QUEUE_KEY, 0, limit - 1)
            for item in queued_items:
                task_data = json.loads(item)
                tasks.append({
                    "task_id": task_data.get("task_id"),
                    "agent_id": task_data.get("agent_id"),
                    "task": task_data.get("task", ""),
                    "status": "queued",
                    "created_at": task_data.get("created_at"),
                    "started_at": None,
                    "completed_at": None,
                    "elapsed_seconds": None,
                    "error": None,
                })

        # Processing tasks
        if status_filter is None or status_filter == "processing":
            processing_items = await redis.lrange(self.TASK_PROCESSING_KEY, 0, limit - 1)
            for item in processing_items:
                task_data = json.loads(item)
                created_at = task_data.get("created_at")
                now = time.time()
                elapsed = round(now - created_at, 1) if created_at else None
                tasks.append({
                    "task_id": task_data.get("task_id"),
                    "agent_id": task_data.get("agent_id"),
                    "task": task_data.get("task", ""),
                    "status": "processing",
                    "created_at": created_at,
                    "started_at": task_data.get("started_at"),
                    "completed_at": None,
                    "elapsed_seconds": elapsed,
                    "error": None,
                })

        # Completed/failed tasks from result keys
        if status_filter is None or status_filter in ("completed", "failed"):
            cursor = 0
            found = 0
            while found < limit:
                cursor, keys = await redis.scan(cursor, match="task:result:*", count=50)
                for key in keys:
                    task_id = key.decode().split("task:result:")[1]
                    result_json = await redis.get(key)
                    if result_json:
                        result = json.loads(result_json)
                        result_status = result.get("status")
                        if status_filter and result_status != status_filter:
                            continue
                        tasks.append({
                            "task_id": task_id,
                            "agent_id": None,
                            "task": "",
                            "status": result_status,
                            "created_at": None,
                            "started_at": None,
                            "completed_at": None,
                            "elapsed_seconds": None,
                            "error": result.get("error"),
                        })
                        found += 1
                        if found >= limit:
                            break
                if cursor == 0:
                    break

        return tasks[:limit]

    async def cancel_task(self, task_id: str) -> dict:
        """Cancel a task.

        Args:
            task_id: Task ID to cancel

        Returns:
            Cancellation result dict
        """
        import json
        redis = await self._get_redis()

        # Try to remove from queued tasks
        queued_items = await redis.lrange(self.TASK_QUEUE_KEY, 0, -1)
        for item in queued_items:
            task_data = json.loads(item)
            if task_data.get("task_id") == task_id:
                await redis.lrem(self.TASK_QUEUE_KEY, 1, item)
                # Store cancelled result
                await redis.set(
                    self.TASK_RESULT_KEY.format(task_id),
                    json.dumps({"status": "cancelled", "error": "Task cancelled by user"}),
                    ex=3600,
                )
                return {
                    "cancelled": True,
                    "task_id": task_id,
                    "message": "Task cancelled",
                }

        # Try to cancel processing task (set cancel flag)
        processing_items = await redis.lrange(self.TASK_PROCESSING_KEY, 0, -1)
        for item in processing_items:
            task_data = json.loads(item)
            if task_data.get("task_id") == task_id:
                # Set cancel flag for worker to detect
                await redis.set(
                    f"task:cancel:{task_id}",
                    "1",
                    ex=300,
                )
                return {
                    "cancelled": True,
                    "task_id": task_id,
                    "message": "Cancel signal sent to worker",
                }

        # Check if task already completed/failed
        result_json = await redis.get(self.TASK_RESULT_KEY.format(task_id))
        if result_json:
            result = json.loads(result_json)
            if result.get("status") in ("completed", "failed", "cancelled"):
                return {
                    "cancelled": False,
                    "task_id": task_id,
                    "message": f"Cannot cancel task with status '{result.get('status')}'",
                }

        return {
            "cancelled": False,
            "task_id": task_id,
            "message": "Task not found",
        }

    async def clear_queue(self) -> int:
        """Clear all queued tasks.

        Returns:
            Number of cleared tasks
        """
        redis = await self._get_redis()
        count = await redis.llen(self.TASK_QUEUE_KEY)
        if count > 0:
            await redis.delete(self.TASK_QUEUE_KEY)
        return count

    async def set_worker_signal(self, worker_id: str, signal: str) -> None:
        """Set a signal for the worker (restart/stop).

        Args:
            worker_id: Worker ID
            signal: Signal type (restart/stop)
        """
        redis = await self._get_redis()
        await redis.set(
            self.WORKER_SIGNAL_KEY.format(worker_id),
            signal,
            ex=60,
        )
