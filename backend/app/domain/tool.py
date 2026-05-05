"""Tool domain entity."""

from enum import Enum
from typing import Dict, Any, List, Optional

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class ToolType(str, Enum):
    MCP = "mcp"
    CUSTOM = "custom"
    IMAGE_GENERATION = "image_generation"


class AuthType(str, Enum):
    NONE = "none"
    BEARER = "bearer"
    API_KEY = "apikey"


class ArgPosition(str, Enum):
    BODY = "body"
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    FORM_DATA = "form-data"


class ToolArg(BaseEntity):
    """Argument definition for an MCP tool."""
    name: str = Field(max_length=100)
    position: ArgPosition = ArgPosition.BODY
    required: bool = False
    arg_type: str = Field(default="string", max_length=50)

    class Config:
        use_enum_values = True


class MCPAuthConfig(BaseEntity):
    """Authentication config for an MCP tool."""
    type: AuthType = AuthType.NONE
    token: Optional[str] = Field(default=None, max_length=500)
    header_name: str = Field(default="X-API-Key", max_length=100)

    class Config:
        use_enum_values = True


class MCPConfig(BaseEntity):
    """Full MCP tool configuration (inspired by Unla's tool config)."""
    endpoint: str = Field(max_length=500, description="HTTP endpoint URL")
    method: str = Field(default="POST", max_length=10)
    auth: MCPAuthConfig = Field(default_factory=MCPAuthConfig)
    headers: Dict[str, str] = Field(default_factory=dict)
    request_template: Optional[str] = Field(default=None, description="Request body template with {{.Args.xxx}} expressions")
    response_template: Optional[str] = Field(default=None, description="Response transform template with {{.Response.data}} expressions")


class Tool(BaseEntity):
    """Tool entity representing an external tool or MCP server."""

    name: str = Field(max_length=100)
    description: str = Field(max_length=500, default="")
    type: ToolType = ToolType.CUSTOM
    config: Dict[str, Any] = Field(default_factory=dict)
    allowed_tools: List[str] = Field(default_factory=list)
    user_id: EntityId
    # MCP-specific fields (only used when type == MCP)
    server_name: Optional[str] = Field(default=None, max_length=100, description="Groups tools under same backend server")
    mcp_config: Optional[MCPConfig] = Field(default=None, description="Full MCP configuration")
    args: List[ToolArg] = Field(default_factory=list, description="Argument definitions")

    class Config:
        use_enum_values = True