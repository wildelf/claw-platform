"""Tool domain entity."""

from enum import Enum
from typing import Dict, Any, List

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class ToolType(str, Enum):
    MCP = "mcp"
    CUSTOM = "custom"


class Tool(BaseEntity):
    """Tool entity representing an external tool or MCP server."""

    name: str = Field(max_length=100)
    description: str = Field(max_length=500, default="")
    type: ToolType = ToolType.CUSTOM
    config: Dict[str, Any] = Field(default_factory=dict)
    allowed_tools: List[str] = Field(default_factory=list)
    user_id: EntityId

    class Config:
        use_enum_values = True