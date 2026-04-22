"""Tool API routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage, UserId
from app.application.tool_service import ToolService
from app.domain.tool import Tool, ToolType
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tools", tags=["tools"])


class CreateToolRequest(BaseModel):
    name: str = Field(max_length=100)
    description: str = Field(max_length=500, default="")
    type: ToolType = ToolType.CUSTOM
    config: dict = Field(default_factory=dict)
    allowed_tools: List[str] = Field(default_factory=list)


class UpdateToolRequest(BaseModel):
    name: Optional[str] = Field(max_length=100, default=None)
    description: Optional[str] = Field(max_length=500, default=None)
    config: Optional[dict] = Field(default=None)
    allowed_tools: Optional[List[str]] = Field(default=None)


@router.post("", response_model=Tool)
async def create_tool(
    request: CreateToolRequest,
    storage: Storage,
    user_id: UserId,
) -> Tool:
    """Register a new tool."""
    tool = Tool(
        name=request.name,
        description=request.description,
        type=request.type,
        config=request.config,
        allowed_tools=request.allowed_tools,
        user_id=user_id,
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
) -> Tool:
    """Get tool by ID."""
    service = ToolService(storage)
    tool = await service.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.put("/{tool_id}", response_model=Tool)
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    storage: Storage,
) -> Tool:
    """Update tool."""
    service = ToolService(storage)
    data = request.model_dump(exclude_unset=True)
    tool = await service.update(tool_id, data)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    storage: Storage,
) -> dict:
    """Delete tool."""
    service = ToolService(storage)
    deleted = await service.delete(tool_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"ok": True}