"""Script execution tool using OpenSandbox.

This tool provides sandboxed Python script execution for AI agents.
"""

import asyncio
import logging
from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.config import settings
from app.infrastructure.opensandbox import OpenSandboxClient

logger = logging.getLogger(__name__)


class ScriptExecutionInput(BaseModel):
    """Input for script execution tool."""
    script: str = Field(description="Python script to execute")
    timeout: int = Field(default=60, description="Execution timeout in seconds")
    memory_limit: str = Field(default="256Mi", description="Memory limit")


class ScriptExecutionTool(BaseTool):
    """Tool for executing Python scripts in an OpenSandbox sandbox."""

    name: str = "execute_script"
    description: str = "Execute a Python script in an isolated sandbox. Use this to run Python code."
    args_schema: Type[BaseModel] = ScriptExecutionInput

    def __init__(self, opensandbox_url: str = None):
        super().__init__()
        self._opensandbox_url = opensandbox_url or getattr(settings, "opensandbox_url", "http://127.0.0.1:8080")

    async def _ainvoke(self, tool_input: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Execute script asynchronously."""
        script = tool_input.get("script", "")
        timeout = tool_input.get("timeout", 60)
        memory_limit = tool_input.get("memory_limit", "256Mi")

        result = await self.execute_script(script, timeout, memory_limit)
        return result

    def _invoke(self, tool_input: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Synchronous invoke (delegates to async)."""
        return asyncio.run(self._ainvoke(tool_input, **kwargs))

    def _run(self, tool_input: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Synchronous run (delegates to async)."""
        return asyncio.run(self._ainvoke(tool_input, **kwargs))

    async def execute_script(
        self,
        script: str,
        timeout: int = 60,
        memory_limit: str = "256Mi",
    ) -> dict[str, Any]:
        """Execute a Python script in OpenSandbox.

        Args:
            script: Python script content
            timeout: Timeout in seconds
            memory_limit: Memory limit (e.g., "256Mi", "512Mi")

        Returns:
            Dict with success status, output, and error
        """
        client = OpenSandboxClient(base_url=self._opensandbox_url)

        async def _execute():
            async with client:
                try:
                    # Create sandbox with the script as entrypoint
                    sandbox_id = await client.create_sandbox(
                        image="python:3.12-slim",
                        entrypoint=["python", "-c", script],
                        timeout=timeout,
                        memory_limit=memory_limit,
                    )

                    # Wait briefly for execution
                    await asyncio.sleep(2)

                    # Get logs and status
                    logs = await client.get_sandbox_logs(sandbox_id)
                    status = await client.get_sandbox_status(sandbox_id)
                    state = status.get("status", {}).get("state", "Unknown")

                    return {
                        "success": state == "Terminated",
                        "sandbox_id": sandbox_id,
                        "output": logs.strip() if logs else "",
                        "state": state,
                        "error": None,
                    }

                except Exception as e:
                    logger.exception("Script execution failed")
                    return {
                        "success": False,
                        "error": str(e),
                        "output": "",
                        "sandbox_id": None,
                        "state": "Error",
                    }
                finally:
                    pass  # Client handles cleanup

        return await _execute()

    async def execute_script_stream(
        self,
        script: str,
        timeout: int = 60,
        memory_limit: str = "256Mi",
    ):
        """Execute script with streaming events.

        Yields:
            Event dicts
        """
        client = OpenSandboxClient(base_url=self._opensandbox_url)

        async with client:
            try:
                yield {"type": "status", "message": "Creating sandbox..."}

                sandbox_id = await client.create_sandbox(
                    image="python:3.12-slim",
                    entrypoint=["python", "-c", script],
                    timeout=timeout,
                    memory_limit=memory_limit,
                )
                yield {"type": "status", "message": f"Sandbox: {sandbox_id}"}

                # Wait for execution
                await asyncio.sleep(2)

                # Get results
                logs = await client.get_sandbox_logs(sandbox_id)
                status = await client.get_sandbox_status(sandbox_id)
                state = status.get("status", {}).get("state", "Unknown")

                yield {"type": "result", "state": state, "output": logs.strip() if logs else ""}

            except Exception as e:
                logger.exception("Streaming execution failed")
                yield {"type": "error", "message": str(e)}


class SandboxToolFactory:
    """Factory for creating sandbox-based tools."""

    @staticmethod
    def create_script_tool(opensandbox_url: str = None) -> ScriptExecutionTool:
        """Create a script execution tool."""
        return ScriptExecutionTool(opensandbox_url=opensandbox_url)

    @staticmethod
    def get_tools(opensandbox_url: str = None) -> list[BaseTool]:
        """Get all sandbox tools."""
        return [ScriptExecutionTool(opensandbox_url=opensandbox_url)]