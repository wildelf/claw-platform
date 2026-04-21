"""Agent application service."""

from typing import List, Optional

from app.domain.agent import Agent
from app.infrastructure.storage.sqlite import SQLiteStorage


class AgentService:
    """Service for agent operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, agent: Agent) -> Agent:
        """Create a new agent."""
        await self.storage.save_agent(agent)
        return agent

    async def get(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return await self.storage.get_agent(agent_id)

    async def list_by_user(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Agent]:
        """List agents for a user."""
        return await self.storage.list_agents(user_id, offset, limit)

    async def update(self, agent_id: str, data: dict) -> Optional[Agent]:
        """Update agent fields."""
        agent = await self.storage.get_agent(agent_id)
        if not agent:
            return None

        for key, value in data.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        await self.storage.save_agent(agent)
        return agent

    async def delete(self, agent_id: str) -> bool:
        """Delete an agent."""
        agent = await self.storage.get_agent(agent_id)
        if not agent:
            return False
        await self.storage.delete_agent(agent_id)
        return True