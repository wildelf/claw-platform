"""Worker service for managing the always-on worker daemon.

Handles worker lifecycle, task execution, heartbeat, and crash recovery.
"""

import asyncio
import logging
import signal
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.deepagents.wrapper import DeepAgentsRunner
from app.infrastructure.heartbeat import HeartbeatManager
from app.infrastructure.redis_client import get_redis_client
from app.infrastructure.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class WorkerService:
    """Manages the always-on worker daemon lifecycle."""

    def __init__(self, storage: SQLiteStorage):
        """Initialize worker service.

        Args:
            storage: SQLite storage adapter
        """
        self.storage = storage
        self.heartbeat_mgr = HeartbeatManager()
        self.worker_id = self._generate_worker_id()
        self._running = False
        self._heartbeat_task = None
        self._task_polling_task = None

    def _generate_worker_id(self) -> str:
        """Generate unique worker ID."""
        import socket
        import os
        return f"worker:{socket.gethostname()}:{os.getpid()}"

    async def start(self) -> None:
        """Start the worker daemon.

        Registers in Redis, starts heartbeat loop, and starts task polling.
        """
        logger.info(f"Starting worker daemon: {self.worker_id}")

        # Register in Redis
        await self.heartbeat_mgr.register_worker(self.worker_id)
        await self.heartbeat_mgr.set_worker_start(self.worker_id)

        # Recover stale tasks
        await self.recover_stale_tasks()

        self._running = True

        # Start heartbeat loop
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Start task polling loop
        self._task_polling_task = asyncio.create_task(self._task_polling_loop())

        # Wait for shutdown signal
        await self._wait_for_shutdown()

    async def stop(self) -> None:
        """Gracefully stop the worker daemon."""
        logger.info(f"Stopping worker daemon: {self.worker_id}")
        self._running = False

        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._task_polling_task:
            self._task_polling_task.cancel()

        # Deregister from Redis
        await self.heartbeat_mgr.deregister_worker(self.worker_id)

    async def _heartbeat_loop(self) -> None:
        """Periodic heartbeat loop with signal detection."""
        interval = getattr(settings, 'worker', None) and getattr(settings.worker, 'heartbeat_interval', 30) or 30

        while self._running:
            try:
                await self.heartbeat_mgr.heartbeat(self.worker_id)
                logger.debug(f"Heartbeat sent: {self.worker_id}")

                # Check for remote signals (restart/stop)
                signal = await self.heartbeat_mgr._get_redis()
                signal_key = self.heartbeat_mgr.WORKER_SIGNAL_KEY.format(self.worker_id)
                signal_val = await signal.get(signal_key)
                if signal_val:
                    signal_type = signal_val.decode() if isinstance(signal_val, bytes) else signal_val
                    logger.info(f"Received worker signal: {signal_type}")
                    if signal_type in ("restart", "stop"):
                        self._running = False
                        break
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
            await asyncio.sleep(interval)

    async def _task_polling_loop(self) -> None:
        """Periodic task polling loop with cancel detection."""
        while self._running:
            try:
                task_data = await self.heartbeat_mgr.claim_task(self.worker_id, timeout=5)
                if task_data:
                    task_id = task_data.get("task_id")
                    logger.info(f"Claimed task: {task_id}")

                    # Check if task was cancelled before execution started
                    redis = await self.heartbeat_mgr._get_redis()
                    cancel_key = f"task:cancel:{task_id}"
                    cancel_flag = await redis.get(cancel_key)
                    if cancel_flag:
                        logger.info(f"Task {task_id} was cancelled before execution")
                        await redis.delete(cancel_key)
                        await self.heartbeat_mgr.fail_task(
                            task_id, "Task cancelled by user"
                        )
                        continue

                    await self.execute_task(task_data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task polling error: {e}")
                await asyncio.sleep(1)

    async def execute_task(self, task_data: dict) -> None:
        """Execute a queued task.

        Args:
            task_data: Task data dict with agent_id, task, session_id, etc.
        """
        import json

        task_id = task_data.get("task_id")
        agent_id = task_data.get("agent_id")
        task_input = task_data.get("task")
        session_id = task_data.get("session_id")

        logger.info(f"Executing task {task_id} for agent {agent_id}")

        try:
            # Load agent from DB
            agent = await self.storage.get_agent(agent_id)
            if not agent:
                await self.heartbeat_mgr.fail_task(task_id, f"Agent {agent_id} not found")
                return

            # Create runner and execute
            runner = DeepAgentsRunner(agent=agent, storage=self.storage)
            await runner.create()

            # Execute task (collect all streaming events)
            result_events = []
            async for event in runner.run(task=task_input):
                result_events.append(event)

            # Mark task as completed
            await self.heartbeat_mgr.complete_task(task_id, {
                "events_count": len(result_events),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })

            logger.info(f"Task {task_id} completed with {len(result_events)} events")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            await self.heartbeat_mgr.fail_task(task_id, str(e))

    async def recover_stale_tasks(self) -> None:
        """Recover uncompleted tasks from stale workers."""
        # Get stale workers
        stale_threshold = getattr(settings, 'worker', None) and getattr(settings.worker, 'stale_threshold', 60) or 60
        stale_workers = await self.heartbeat_mgr.get_stale_workers(stale_threshold)

        for worker_id in stale_workers:
            logger.info(f"Recovering tasks for stale worker: {worker_id}")
            recovered = await self.heartbeat_mgr.recover_tasks_for_worker(worker_id)
            if recovered:
                logger.info(f"Recovered {len(recovered)} tasks from {worker_id}")

    async def _wait_for_shutdown(self) -> None:
        """Wait for shutdown signal (SIGTERM or SIGINT)."""
        loop = asyncio.get_event_loop()

        def shutdown_handler():
            logger.info("Shutdown signal received")
            self._running = False

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, shutdown_handler)

        # Wait until _running becomes False
        while self._running:
            await asyncio.sleep(0.5)


async def run_worker():
    """Entry point for worker daemon."""
    from app.infrastructure.storage.sqlite import SQLiteStorage
    from app.config import settings

    storage = SQLiteStorage(settings.storage.sqlite.path)
    await storage.init_db()

    worker = WorkerService(storage)

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()
    finally:
        await storage.close()
