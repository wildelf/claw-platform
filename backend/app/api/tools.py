"""Tool API routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage, UserId
from app.application.tool_service import ToolService
from app.domain.tool import Tool, ToolType, ToolArg, MCPAuthConfig, MCPConfig
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tools", tags=["tools"])


class AuthConfigSchema(BaseModel):
    type: str = "none"
    token: Optional[str] = None
    header_name: str = "X-API-Key"


class ArgSchema(BaseModel):
    name: str
    position: str = "body"
    required: bool = False
    arg_type: str = "string"


class MCPConfigSchema(BaseModel):
    endpoint: str
    method: str = "POST"
    auth: AuthConfigSchema = Field(default_factory=AuthConfigSchema)
    headers: dict = {}
    request_template: Optional[str] = None
    response_template: Optional[str] = None


class CreateToolRequest(BaseModel):
    name: str = Field(max_length=100)
    description: str = Field(max_length=500, default="")
    type: ToolType = ToolType.CUSTOM
    config: dict = Field(default_factory=dict)
    allowed_tools: List[str] = Field(default_factory=list)
    # MCP fields
    server_name: Optional[str] = Field(default=None, max_length=100)
    mcp_config: Optional[MCPConfigSchema] = None
    args: List[ArgSchema] = Field(default_factory=list)


class UpdateToolRequest(BaseModel):
    name: Optional[str] = Field(max_length=100, default=None)
    description: Optional[str] = Field(max_length=500, default=None)
    type: Optional[ToolType] = None
    config: Optional[dict] = Field(default=None)
    allowed_tools: Optional[List[str]] = None
    server_name: Optional[str] = Field(default=None, max_length=100)
    mcp_config: Optional[MCPConfigSchema] = None
    args: Optional[List[ArgSchema]] = None


@router.post("", response_model=Tool)
async def create_tool(
    request: CreateToolRequest,
    storage: Storage,
    user_id: UserId,
) -> Tool:
    """Register a new tool."""
    mcp_config = None
    if request.mcp_config:
        mcp_config = MCPConfig(
            endpoint=request.mcp_config.endpoint,
            method=request.mcp_config.method,
            auth=MCPAuthConfig(
                type=request.mcp_config.auth.type,
                token=request.mcp_config.auth.token,
                header_name=request.mcp_config.auth.header_name,
            ),
            headers=request.mcp_config.headers or {},
            request_template=request.mcp_config.request_template,
            response_template=request.mcp_config.response_template,
        )
    tool_args = [ToolArg(name=a.name, position=a.position, required=a.required, arg_type=a.arg_type) for a in request.args]
    tool = Tool(
        name=request.name,
        description=request.description,
        type=request.type,
        config=request.config,
        allowed_tools=request.allowed_tools,
        user_id=user_id,
        server_name=request.server_name,
        mcp_config=mcp_config,
        args=tool_args,
    )
    service = ToolService(storage)
    return await service.create(tool)


@router.get("", response_model=List[Tool])
async def list_tools(
    storage: Storage,
    user_id: UserId,
) -> List[Tool]:
    """List tools for current user."""
    service = ToolService(storage)
    return await service.list_by_user(user_id)


@router.get("/{tool_id}", response_model=Tool)
async def get_tool(
    tool_id: str,
    storage: Storage,
    user_id: UserId,
) -> Tool:
    """Get tool by ID."""
    service = ToolService(storage)
    tool = await service.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if tool.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this tool")
    return tool


@router.put("/{tool_id}", response_model=Tool)
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    storage: Storage,
    user_id: UserId,
) -> Tool:
    """Update tool."""
    service = ToolService(storage)
    tool = await service.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if tool.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this tool")
    data = request.model_dump(exclude_unset=True)

    # Convert nested MCP config
    if 'mcp_config' in data and data['mcp_config']:
        mc = data['mcp_config']
        auth_dict = mc.get('auth', {})
        data['mcp_config'] = MCPConfig(
            endpoint=mc['endpoint'],
            method=mc.get('method', 'POST'),
            auth=MCPAuthConfig(
                type=auth_dict.get('type', 'none'),
                token=auth_dict.get('token'),
                header_name=auth_dict.get('header_name', 'X-API-Key'),
            ),
            headers=mc.get('headers', {}),
            request_template=mc.get('request_template'),
            response_template=mc.get('response_template'),
        )
    if 'args' in data and data['args']:
        data['args'] = [ToolArg(name=a['name'], position=a.get('position', 'body'), required=a.get('required', False), arg_type=a.get('type', 'string')) for a in data['args']]

    tool = await service.update(tool_id, data)
    return tool


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    storage: Storage,
    user_id: UserId,
) -> dict:
    """Delete tool."""
    service = ToolService(storage)
    tool = await service.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if tool.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this tool")
    deleted = await service.delete(tool_id)
    return {"ok": True}