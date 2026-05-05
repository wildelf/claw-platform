"""Custom exceptions for the deepagents module."""


class MCPToolError(Exception):
    """Base exception for MCP tool errors."""
    pass


class MCPTimeoutError(MCPToolError):
    """MCP tool call timed out."""

    def __init__(self, tool_name: str, timeout: float):
        self.tool_name = tool_name
        self.timeout = timeout
        super().__init__(f"MCP tool '{tool_name}' timed out after {timeout}s")


class MCPParseError(MCPToolError):
    """MCP returned malformed data."""

    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"MCP tool '{tool_name}' returned malformed data: {reason}")


class MCPAuthError(MCPToolError):
    """MCP tool call unauthorized (403)."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"无权限访问 MCP 工具 '{tool_name}'，请联系 IT 管理员")


class PermissionDeniedError(Exception):
    """Agent tried to call an unauthorized tool."""

    def __init__(self, tool_name: str, agent_id: str):
        self.tool_name = tool_name
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' tried to call unauthorized tool '{tool_name}'")


class SkillNotFoundError(Exception):
    """SKILL.md file not found."""

    def __init__(self, skill_path: str):
        self.skill_path = skill_path
        super().__init__(f"SOP 未找到，请检查配置: {skill_path}")


class LLMResponseError(Exception):
    """LLM returned an unparseable or invalid response."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"AI 响应异常: {reason}")
