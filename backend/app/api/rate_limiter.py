"""Rate limiting middleware for API endpoints."""

import time
import asyncio
from collections import defaultdict
from typing import Optional

from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse


class TokenBucket:
    """Simple token bucket rate limiter."""

    def __init__(self, rate: float, capacity: float):
        """
        Args:
            rate: Tokens added per second
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_refill)
        self._lock = asyncio.Lock()

    def _refill(self, key: str) -> tuple[float, float]:
        """Refill tokens for a key. Returns (tokens, last_refill)."""
        now = time.monotonic()
        if key not in self._buckets:
            return (self.capacity, now)

        tokens, last_refill = self._buckets[key]
        elapsed = now - last_refill
        tokens = min(self.capacity, tokens + elapsed * self.rate)
        return (tokens, now)

    async def consume(self, key: str) -> bool:
        """Try to consume a token. Returns True if allowed, False if rate limited."""
        async with self._lock:
            tokens, now = self._refill(key)
            if tokens >= 1:
                self._buckets[key] = (tokens - 1, now)
                return True
            self._buckets[key] = (tokens, now)
            return False

    async def cleanup(self, max_age: float = 3600):
        """Remove stale buckets older than max_age seconds."""
        now = time.monotonic()
        async with self._lock:
            stale_keys = [
                k for k, (_, last_refill) in self._buckets.items()
                if now - last_refill > max_age
            ]
            for k in stale_keys:
                del self._buckets[k]


# Default rate limiter: 10 requests per minute per key
agent_run_limiter = TokenBucket(rate=10 / 60, capacity=10)


def _get_client_key(request: Request) -> str:
    """Get a rate limit key from the request (user ID or IP)."""
    # Try to get user ID from auth context (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    # Fallback to IP address
    return f"ip:{request.client.host}"


async def rate_limit_dependency(
    request: Request,
    limiter: Optional[TokenBucket] = None,
) -> None:
    """FastAPI dependency for rate limiting.

    Raises 429 Too Many Requests if rate limit exceeded.
    """
    lim = limiter or agent_run_limiter
    key = _get_client_key(request)

    if not await lim.consume(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"},
        )


# Pre-configured dependency for agent run endpoints
async def rate_limit_agent_run(request: Request) -> None:
    """Rate limit dependency for agent execution endpoints."""
    await rate_limit_dependency(request, agent_run_limiter)
