"""Redis client for distributed agent coordination."""

import json
import os
import socket
from typing import Any

import redis.asyncio as redis

from app.config import settings

# Redis key prefixes
RUNNING_AGENTS_KEY = "running_agents"
CANCEL_FLAG_PREFIX = "cancel_agent:"
WORKER_HEARTBEAT_KEY = "worker:heartbeat:{}"
WORKER_REGISTRY_KEY = "worker:registry"
TASK_QUEUE_KEY = "task:queue"
TASK_PROCESSING_KEY = "task:processing"
TASK_RESULT_KEY = "task:result:{}"


def _get_node_id() -> str:
    """Get unique node identifier (hostname:pid)."""
    return f"{socket.gethostname()}:{os.getpid()}"


class RedisAgentRegistry:
    """Redis-backed registry for tracking running agents across nodes."""

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._node_id = _get_node_id()

    async def register_agent(self, agent_id: str) -> None:
        """Register an agent as running on this node."""
        await self._redis.hset(
            RUNNING_AGENTS_KEY,
            agent_id,
            json.dumps({"node_id": self._node_id}),
        )

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent (stopped or never started)."""
        await self._redis.hdel(RUNNING_AGENTS_KEY, agent_id)

    async def is_agent_running(self, agent_id: str) -> bool:
        """Check if agent is registered as running on any node."""
        return await self._redis.hexists(RUNNING_AGENTS_KEY, agent_id)

    async def get_running_agents(self) -> dict[str, dict[str, Any]]:
        """Get all running agents and their node info."""
        data = await self._redis.hgetall(RUNNING_AGENTS_KEY)
        return {k.decode(): json.loads(v.decode()) for k, v in data.items()}

    async def request_agent_cancel(self, agent_id: str) -> bool:
        """
        Request cancellation of an agent.
        Returns True if the agent was found and cancel was requested.
        """
        if await self.is_agent_running(agent_id):
            await self._redis.set(f"{CANCEL_FLAG_PREFIX}{agent_id}", "1")
            return True
        return False

    async def check_cancel_requested(self, agent_id: str) -> bool:
        """Check if cancellation was requested for this agent."""
        result = await self._redis.get(f"{CANCEL_FLAG_PREFIX}{agent_id}")
        return result is not None

    async def clear_cancel_flag(self, agent_id: str) -> None:
        """Clear the cancel flag after agent has stopped."""
        await self._redis.delete(f"{CANCEL_FLAG_PREFIX}{agent_id}")


# Global Redis client instance
_redis_client: redis.Redis | None = None
_agent_registry: RedisAgentRegistry | None = None


def get_redis_client() -> redis.Redis:
    """Get or create the global Redis client."""
    global _redis_client
    if _redis_client is None:
        cfg = settings.redis
        _redis_client = redis.Redis(
            host=cfg.host,
            port=cfg.port,
            db=cfg.db,
            password=cfg.password,
            decode_responses=False,
        )
    return _redis_client


def get_agent_registry() -> RedisAgentRegistry:
    """Get the global agent registry."""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = RedisAgentRegistry(get_redis_client())
    return _agent_registry


def reset_redis_client() -> None:
    """Reset the global Redis client (useful for test cleanup between event loops)."""
    global _redis_client, _agent_registry
    _redis_client = None
    _agent_registry = None
