"""Tool application service."""

from typing import List, Optional

from app.domain.tool import Tool
from app.infrastructure.storage.sqlite import SQLiteStorage


class ToolService:
    """Service for tool operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, tool: Tool) -> Tool:
        """Create a new tool."""
        await self.storage.save_tool(tool)
        return tool

    async def get(self, tool_id: str) -> Optional[Tool]:
        """Get tool by ID."""
        return await self.storage.get_tool(tool_id)

    async def list_by_user(self, user_id: str) -> List[Tool]:
        """List tools for a user."""
        return await self.storage.list_tools(user_id)

    async def update(self, tool_id: str, data: dict) -> Optional[Tool]:
        """Update tool fields."""
        tool = await self.storage.get_tool(tool_id)
        if not tool:
            return None

        for key, value in data.items():
            if hasattr(tool, key):
                setattr(tool, key, value)

        await self.storage.save_tool(tool)
        return tool

    async def delete(self, tool_id: str) -> bool:
        """Delete a tool."""
        tool = await self.storage.get_tool(tool_id)
        if not tool:
            return False
        await self.storage.delete_tool(tool_id)
        return True