"""Permission controller for agent-level MCP tool access control."""

import logging
from typing import NamedTuple

from app.domain.agent import Agent
from app.domain.tool import Tool, ToolType
from app.infrastructure.storage.base import StorageAdapter

logger = logging.getLogger(__name__)


class PermissionResult(NamedTuple):
    """Result of a permission check."""

    allowed: bool
    error_message: str | None = None


class PermissionController:
    """Controls which MCP tools an agent can access.

    Agent-level permissions: each agent has a list of allowed tool IDs.
    Built-in tools are always allowed unless explicitly disabled.
    """

    def __init__(self, agent: Agent, storage: StorageAdapter):
        self._agent = agent
        self._storage = storage

    async def is_tool_allowed(self, tool_name: str) -> PermissionResult:
        """Check if the agent is allowed to call the given tool.

        Args:
            tool_name: The name of the tool being called.

        Returns:
            PermissionResult indicating if the tool call is allowed.
        """
        # Built-in tools are always allowed (unless explicitly disabled)
        # These are handled separately by the agent's enabled_builtin_tools list
        if self._is_builtin_tool(tool_name):
            return PermissionResult(allowed=True)

        # Check MCP tool permissions
        allowed_tool_ids = set(str(tid) for tid in self._agent.tool_ids)

        if not allowed_tool_ids:
            return PermissionResult(
                allowed=False,
                error_message="该操作未被授权：该 Agent 未配置任何 MCP 工具权限"
            )

        # Check each registered tool to see if tool_name matches
        for tool_id in allowed_tool_ids:
            tool = await self._storage.get_tool(tool_id)
            if tool and tool.name == tool_name:
                return PermissionResult(allowed=True)

        return PermissionResult(
            allowed=False,
            error_message=f"该操作未被授权：该 Agent 无法使用工具 '{tool_name}'"
        )

    def _is_builtin_tool(self, tool_name: str) -> bool:
        """Check if tool_name refers to a built-in tool.

        Built-in tools: read_file, write_file, bash, etc.
        These are always available unless explicitly disabled.
        """
        # List of known built-in tool names
        builtin_tools = {
            "read_file", "write_file", "bash", "shell",
            "Calculator", "WolframAlpha", "arxiv",
            "ImageGenerationTool", "ScriptExecutionTool", "WebSearchTool",
            # Add more as needed
        }
        return tool_name in builtin_tools

    async def filter_allowed_tools(self, tools: list[Tool]) -> list[Tool]:
        """Filter a list of tools to only those the agent is allowed to use.

        Args:
            tools: All available tools.

        Returns:
            Only the tools the agent is allowed to use.
        """
        allowed = []
        for tool in tools:
            result = await self.is_tool_allowed(tool.name)
            if result.allowed:
                allowed.append(tool)
        return allowed
