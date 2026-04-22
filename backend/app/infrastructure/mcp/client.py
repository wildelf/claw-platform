"""MCP client for connecting to MCP servers."""

import asyncio
import json
from typing import Any, Dict, List, Optional


class MCPClient:
    """Client for Model Context Protocol servers."""

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
        response = await self._send_request("tools/list", {})
        return response.get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        return response.get("content", [])

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
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

        response_line = await self._process.stdout.readline()
        response = json.loads(response_line.decode())

        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")

        return response.get("result", {})

    def _process_env(self) -> Dict[str, str]:
        """Get environment for subprocess."""
        env = dict(self.env)
        return env