"""MCP adapter for converting MCP tools to platform tools."""

import asyncio
from typing import Any, Dict, List

from app.domain.tool import Tool, ToolType
from app.infrastructure.mcp.client import MCPClient


class MCPAdapter:
    """Adapter for MCP tools."""

    def __init__(self, tool: Tool):
        self.tool = tool
        self._client: MCPClient | None = None
        self._init_lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize MCP client from tool config."""
        if self.tool.type != ToolType.MCP:
            raise ValueError("Tool is not an MCP tool")

        async with self._init_lock:
            if self._initialized:
                return
            config = self.tool.config
            command = config.get("command", "npx")
            args = config.get("args", [])

            self._client = MCPClient(command=command, args=args)
            await self._client.start()
            self._initialized = True

    async def close(self) -> None:
        """Close MCP client connection."""
        async with self._init_lock:
            if self._client:
                await self._client.stop()
                self._client = None
            self._initialized = False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        async with self._init_lock:
            if not self._client:
                await self._ensure_initialized()
        return await self._client.list_tools()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        async with self._init_lock:
            if not self._client:
                await self._ensure_initialized()
        return await self._client.call_tool(tool_name, arguments)

    async def _ensure_initialized(self) -> None:
        """Ensure MCP client is initialized."""
        if self._initialized:
            return
        if self.tool.type != ToolType.MCP:
            raise ValueError("Tool is not an MCP tool")

        config = self.tool.config
        command = config.get("command", "npx")
        args = config.get("args", [])

        self._client = MCPClient(command=command, args=args)
        await self._client.start()
        self._initialized = True