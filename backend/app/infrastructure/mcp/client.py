"""MCP client for connecting to MCP servers."""

import asyncio
import json
from typing import Any, Dict, List, Optional

DEFAULT_REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECS = [1, 2, 4]  # backoff sequence: 1s, 2s, 4s


class MCPClient:
    """Client for Model Context Protocol servers with retry logic."""

    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.command = command
        self.args = args
        self.env = env or {}
        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0

    async def start(self) -> None:
        """Start the MCP server process."""
        self._process = await asyncio.subprocess.create_subprocess_exec(
            self.command,
            *self.args,
            env={**self._process_env(), **self.env},
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def stop(self) -> None:
        """Stop the MCP server process."""
        if self._process:
            self._process.terminate()
            await self._process.wait()
            self._process = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        response = await self._send_request_with_retry("tools/list", {})
        return response.get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server with retry logic."""
        response = await self._send_request_with_retry("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        return response.get("content", [])

    async def _send_request_with_retry(
        self, method: str, params: Dict[str, Any], timeout: float = DEFAULT_REQUEST_TIMEOUT
    ) -> Dict[str, Any]:
        """Send a JSON-RPC request with retry and backoff on transient errors."""
        from app.deepagents.exceptions import MCPAuthError, MCPParseError, MCPTimeoutError

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                return await self._send_request(method, params, timeout)
            except MCPTimeoutError as e:
                last_error = e
                logger.warning(f"MCP request {method} timed out (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            except MCPAuthError as e:
                # Don't retry auth errors
                raise
            except (MCPParseError, RuntimeError) as e:
                last_error = e
                logger.warning(f"MCP request {method} failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES - 1:
                backoff = RETRY_BACKOFF_SECS[min(attempt, len(RETRY_BACKOFF_SECS) - 1)]
                await asyncio.sleep(backoff)

        raise last_error or RuntimeError(f"MCP request {method} failed after {MAX_RETRIES} retries")

    async def _send_request(self, method: str, params: Dict[str, Any], timeout: float = DEFAULT_REQUEST_TIMEOUT) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        from app.deepagents.exceptions import MCPAuthError, MCPParseError, MCPTimeoutError

        if not self._process:
            raise RuntimeError("MCP client not started")

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        request_json = json.dumps(request) + "\n"
        self._process.stdin.write(request_json.encode())
        await self._process.stdin.drain()

        try:
            response_line = await asyncio.wait_for(
                self._process.stdout.readline(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise MCPTimeoutError(tool_name=method, timeout=timeout)

        try:
            response = json.loads(response_line.decode())
        except json.JSONDecodeError as e:
            raise MCPParseError(tool_name=method, reason=str(e))

        if "error" in response:
            error_data = response["error"]
            if isinstance(error_data, dict):
                code = error_data.get("code", 0)
                # Common auth error codes
                if code in (403, -32000):
                    raise MCPAuthError(tool_name=method)
            raise RuntimeError(f"MCP error: {error_data}")

        return response.get("result", {})

    def _process_env(self) -> Dict[str, str]:
        """Get environment for subprocess."""
        env = dict(self.env)
        return env


logger = __import__("logging").getLogger(__name__)