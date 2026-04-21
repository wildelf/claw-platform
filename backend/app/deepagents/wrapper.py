"""DeepAgents runtime wrapper.

This module provides integration with the deepagents library for
agent execution. Currently a stub - full implementation follows.
"""

from typing import Any, AsyncGenerator, Optional

from app.domain.agent import Agent
from app.domain.tool import Tool
from app.infrastructure.storage.sqlite import SQLiteStorage


class DeepAgentsRunner:
    """Wrapper for deepagents runtime.

    TODO: Full implementation
    - Load skills from storage
    - Load tools (MCP + custom)
    - Resolve model configuration
    - Create and run deep_agent
    """

    def __init__(
        self,
        agent: Agent,
        storage: SQLiteStorage,
    ):
        self.agent = agent
        self.storage = storage

    async def create(self):
        """Create deepagents runner instance."""
        # TODO: Implement
        pass

    async def run(self, task: str) -> AsyncGenerator[Any, None]:
        """Run agent task.

        Yields:
            Events from agent execution.
        """
        # TODO: Implement
        yield {"status": "todo", "message": "Not yet implemented"}

    async def stop(self):
        """Stop running agent."""
        # TODO: Implement
        pass