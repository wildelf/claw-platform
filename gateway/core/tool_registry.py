"""In-memory registry of tool configurations fetched from claw-platform."""

import logging
import threading
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolConfig:
    """MCP tool configuration (mirrors backend Tool domain)."""
    id: str
    name: str
    description: str
    type: str  # "mcp"
    server_name: Optional[str]
    endpoint: str
    method: str
    auth: Dict  # {"type": "bearer"|"apikey"|"none", "token": "...", "header_name": "..."}
    headers: Dict[str, str]
    args: list  # [{"name": "...", "position": "body"|"query"|"path"|"header", "required": bool, "type": "string"}]
    request_template: Optional[str]
    response_template: Optional[str]
    updated_at: str


class ToolRegistry:
    """Thread-safe in-memory cache of tool configurations."""

    def __init__(self):
        self._tools: Dict[str, ToolConfig] = {}
        self._lock = threading.RLock()
        self._last_sync: Optional[str] = None

    def update_tools(self, tools: list):
        """Replace all tools with a new list fetched from claw-platform."""
        with self._lock:
            self._tools.clear()
            for tool in tools:
                if tool.get("type", "").lower() == "mcp" and tool.get("mcp_config"):
                    mcp_cfg = tool["mcp_config"]
                    auth_cfg = mcp_cfg.get("auth", {})
                    cfg = ToolConfig(
                        id=tool["id"],
                        name=tool["name"],
                        description=tool.get("description", ""),
                        type=tool.get("type", "mcp"),
                        server_name=tool.get("server_name"),
                        endpoint=mcp_cfg.get("endpoint", ""),
                        method=mcp_cfg.get("method", "POST"),
                        auth={
                            "type": auth_cfg.get("type", "none"),
                            "token": auth_cfg.get("token"),
                            "header_name": auth_cfg.get("header_name", "X-API-Key"),
                        },
                        headers=mcp_cfg.get("headers", {}),
                        args=tool.get("args", []),
                        request_template=mcp_cfg.get("request_template"),
                        response_template=mcp_cfg.get("response_template"),
                        updated_at=tool.get("updated_at", ""),
                    )
                    self._tools[tool["id"]] = cfg
                    self._tools[cfg.name] = cfg  # index by name too
            logger.info(f"Tool registry updated: {len(self._tools)} tools")

    def get_tool(self, identifier: str) -> Optional[ToolConfig]:
        """Get tool by ID or name."""
        with self._lock:
            return self._tools.get(identifier)

    def list_tools(self) -> list:
        """List all registered tools."""
        with self._lock:
            # deduplicate by id
            seen = set()
            result = []
            for t in self._tools.values():
                if t.id not in seen:
                    seen.add(t.id)
                    result.append(t)
            return result

    @property
    def last_sync(self) -> Optional[str]:
        with self._lock:
            return self._last_sync

    @last_sync.setter
    def last_sync(self, value: str):
        with self._lock:
            self._last_sync = value

    @property
    def tool_count(self) -> int:
        with self._lock:
            seen = set()
            for t in self._tools.values():
                seen.add(t.id)
            return len(seen)