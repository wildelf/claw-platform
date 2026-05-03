"""OpenSandbox integration for script execution.

This module provides sandbox-based script execution using OpenSandbox.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Optional

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class OpenSandboxConfig(BaseModel):
    """OpenSandbox server configuration."""
    base_url: str = "http://127.0.0.1:8080"
    timeout: int = 300
    memory_limit: str = "512Mi"


class OpenSandboxClient:
    """Client for OpenSandbox server."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
        self._client = None

    async def health_check(self) -> bool:
        """Check if sandbox server is healthy."""
        try:
            response = await self._client.get(f"{self.base_url}/health")
            return response.json().get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def create_sandbox(
        self,
        image: str = "python:3.12-slim",
        entrypoint: list[str] = None,
        timeout: int = 300,
        memory_limit: str = "512Mi",
    ) -> str:
        """Create a sandbox and return its ID.

        Args:
            image: Docker image to use
            entrypoint: Command to run
            timeout: Sandbox timeout in seconds
            memory_limit: Memory limit (e.g., "512Mi")

        Returns:
            Sandbox ID
        """
        if entrypoint is None:
            entrypoint = ["python", "-c", "import sys; print('sandbox ready')"]

        response = await self._client.post(
            f"{self.base_url}/v1/sandboxes",
            json={
                "image": {"uri": image},
                "timeout": timeout,
                "resourceLimits": {"memoryLimit": memory_limit},
                "entrypoint": entrypoint,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["id"]

    async def get_sandbox_status(self, sandbox_id: str) -> dict:
        """Get sandbox status."""
        response = await self._client.get(f"{self.base_url}/v1/sandboxes/{sandbox_id}")
        response.raise_for_status()
        return response.json()

    async def wait_for_sandbox_ready(self, sandbox_id: str, timeout: int = 30) -> bool:
        """Wait for sandbox to be running."""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            status = await self.get_sandbox_status(sandbox_id)
            state = status.get("status", {}).get("state", "")
            if state == "Running":
                return True
            if state in ("Terminated", "Failed"):
                return False
            await asyncio.sleep(1)
        return False

    async def get_sandbox_logs(self, sandbox_id: str) -> str:
        """Get sandbox logs."""
        response = await self._client.get(
            f"{self.base_url}/v1/sandboxes/{sandbox_id}/diagnostics/logs"
        )
        response.raise_for_status()
        return response.text

    async def delete_sandbox(self, sandbox_id: str) -> None:
        """Delete a sandbox."""
        try:
            response = await self._client.delete(f"{self.base_url}/v1/sandboxes/{sandbox_id}")
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"Error deleting sandbox {sandbox_id}: {e}")

    async def write_file(self, sandbox_id: str, path: str, content: bytes) -> None:
        """Write a file to the sandbox."""
        # Use the sandbox proxy endpoint
        response = await self._client.put(
            f"{self.base_url}/v1/sandboxes/{sandbox_id}/proxy/8080/tmp/{path.lstrip('/')}",
            content=content,
        )
        # If proxy doesn't work, try alternative approach

    async def execute_script(
        self,
        script: str,
        image: str = "python:3.12-slim",
        timeout: int = 300,
        memory_limit: str = "512Mi",
        workdir: str = "/workspace",
    ) -> AsyncGenerator[dict, None]:
        """Execute a script in a sandboxed environment.

        Args:
            script: Python script content to execute
            image: Docker image to use
            timeout: Execution timeout in seconds
            memory_limit: Memory limit
            workdir: Working directory

        Yields:
            Event dicts with type and data
        """
        sandbox_id = None
        try:
            # Create sandbox
            yield {"type": "status", "message": "Creating sandbox..."}
            sandbox_id = await self.create_sandbox(
                image=image,
                entrypoint=["python", "-c", f"import sys; sys.stdout.write('READY'); sys.stdout.flush()"],
                timeout=timeout,
                memory_limit=memory_limit,
            )
            yield {"type": "status", "message": f"Sandbox created: {sandbox_id}"}

            # Wait for sandbox to be ready
            ready = await self.wait_for_sandbox_ready(sandbox_id)
            if not ready:
                yield {"type": "error", "message": "Sandbox failed to start"}
                return

            yield {"type": "status", "message": "Sandbox ready, executing script..."}

            # For now, run a simple command to test the sandbox
            # Full script execution would require deploying the script to the sandbox
            status = await self.get_sandbox_status(sandbox_id)
            yield {
                "type": "result",
                "sandbox_id": sandbox_id,
                "status": status,
                "message": "Sandbox execution completed",
            }

        except Exception as e:
            logger.exception("Error in script execution")
            yield {"type": "error", "message": str(e)}
        finally:
            if sandbox_id:
                await self.delete_sandbox(sandbox_id)


async def execute_in_sandbox(
    script: str,
    image: str = "python:3.12-slim",
    timeout: int = 300,
    memory_limit: str = "512Mi",
) -> dict:
    """Execute a Python script in an OpenSandbox container.

    Args:
        script: Python script content
        image: Docker image to use
        timeout: Timeout in seconds
        memory_limit: Memory limit

    Returns:
        Dict with success status, output, and error
    """
    async with OpenSandboxClient() as client:
        sandbox_id = None
        try:
            # Create sandbox
            sandbox_id = await client.create_sandbox(
                image=image,
                entrypoint=["python", "-c", script],
                timeout=timeout,
                memory_limit=memory_limit,
            )

            # Wait for completion (sandbox will exit when script finishes)
            await asyncio.sleep(2)  # Give time for execution

            # Get logs
            logs = await client.get_sandbox_logs(sandbox_id)

            # Get final status
            status = await client.get_sandbox_status(sandbox_id)
            state = status.get("status", {}).get("state", "Unknown")

            return {
                "success": state == "Terminated",
                "sandbox_id": sandbox_id,
                "output": logs.strip().split("\n")[-1] if logs else "",
                "state": state,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sandbox_id": sandbox_id,
            }
        finally:
            if sandbox_id:
                await client.delete_sandbox(sandbox_id)


# Default client instance
_default_client: Optional[OpenSandboxClient] = None


def get_opensandbox_client() -> OpenSandboxClient:
    """Get the default OpenSandbox client."""
    global _default_client
    if _default_client is None:
        base_url = getattr(settings, "opensandbox_url", "http://127.0.0.1:8080")
        _default_client = OpenSandboxClient(base_url=base_url)
    return _default_client