"""DeepAgents runtime wrapper.

This module provides integration with the deepagents library for
agent execution.
"""

import asyncio
import re
from typing import Any, AsyncGenerator, Optional

from deepagents import create_deep_agent
from deepagents.middleware import SkillsMiddleware
from deepagents.backends.state import StateBackend

from app.domain.agent import Agent
from app.domain.tool import Tool, ToolType
from app.domain.model_config import ModelProviderType
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.infrastructure.mcp.adapter import MCPAdapter
from app.config import settings


class DeepAgentsRunner:
    """Wrapper for deepagents runtime.

    Provides integration between the platform's storage, tools, and models
    with the deepagents library.
    """

    def __init__(
        self,
        agent: Agent,
        storage: SQLiteStorage,
    ):
        self.agent = agent
        self.storage = storage
        self._runner = None
        self._mcp_adapters: dict[str, MCPAdapter] = {}

    async def create(self):
        """Create deepagents runner instance."""
        # 1. Load skills from storage into StateBackend
        backend = await self._create_backend()

        # 2. Load tools
        tools = await self._load_tools()

        # 3. Resolve model configuration
        model = await self._resolve_model()

        # 4. Build system prompt from agent config
        system_prompt = self._build_system_prompt()

        # 5. Create Skills middleware
        skill_sources = await self._get_skill_sources()
        skills_middleware = SkillsMiddleware(
            backend=backend,
            sources=skill_sources,
        )

        # 6. Create deep_agent
        self._runner = create_deep_agent(
            model=model,
            tools=tools if tools else None,
            system_prompt=system_prompt,
            middleware=[skills_middleware] if skill_sources else [],
        )

    async def run(self, task: str) -> AsyncGenerator[str, None]:
        """Run agent task.

        Yields:
            String chunks from agent execution.
        """
        if not self._runner:
            await self.create()

        # deepagents expects dict input with 'messages' key for chat models
        input_data = {"messages": [{"role": "user", "content": task}]}

        # Use astream to get incremental output chunks
        async for chunk in self._runner.astream(input_data):
            if not isinstance(chunk, dict):
                continue
            # Extract content from various chunk formats
            if "model" in chunk:
                model_data = chunk["model"]
                if isinstance(model_data, dict) and "messages" in model_data:
                    for msg in model_data["messages"]:
                        if hasattr(msg, 'content') and msg.content:
                            yield msg.content
            elif "messages" in chunk:
                for msg in chunk["messages"]:
                    if hasattr(msg, 'content') and msg.content:
                        yield msg.content

    async def stop(self):
        """Stop running agent and cleanup."""
        # Close all MCP connections
        for adapter in self._mcp_adapters.values():
            await adapter.close()
        self._mcp_adapters.clear()
        self._runner = None

    async def _create_backend(self) -> StateBackend:
        """Create StateBackend from platform storage."""
        # StateBackend requires a backend that implements the protocol
        # For now, return an in-memory backend
        return StateBackend()

    async def _load_tools(self) -> list:
        """Load tools from storage."""
        tools = []
        for tool_id in self.agent.tool_ids:
            tool = await self.storage.get_tool(tool_id)
            if not tool:
                continue

            if tool.type == ToolType.MCP:
                adapter = MCPAdapter(tool)
                await adapter.initialize()
                self._mcp_adapters[tool_id] = adapter
                # MCP tools would be converted to LangChain tools here
                # For now, skip as it requires more complex adaptation
            elif tool.type == ToolType.CUSTOM:
                # Custom tools would be loaded here
                pass

        return tools

    async def _resolve_model(self):
        """Resolve model from agent configuration.

        Returns a LangChain chat model instance compatible with deepagents.
        For custom base_url, we need to use the raw ChatOpenAI/ChatAnthropic
        and pass to create_deep_agent instead of a string.
        """
        from langchain_openai import ChatOpenAI

        if not self.agent.model_config_id:
            # Use default model from config
            default_model = settings.models.default
            if default_model.base_url:
                return ChatOpenAI(
                    model=default_model.model,
                    api_key=default_model.api_key,
                    base_url=default_model.base_url,
                )
            return f"openai:{default_model.model}"

        config = await self.storage.get_model_config(self.agent.model_config_id)
        if not config:
            raise ValueError(f"Model config not found: {self.agent.model_config_id}")

        if config.base_url:
            return ChatOpenAI(
                model=config.model,
                api_key=config.api_key,
                base_url=config.base_url,
            )
        return f"openai:{config.model}"

    def _build_system_prompt(self) -> str:
        """Build system prompt from agent configuration."""
        parts = []

        if self.agent.role:
            parts.append(f"You are {self.agent.role}.")
        if self.agent.goal:
            parts.append(f"Your goal is: {self.agent.goal}.")
        if self.agent.backstory:
            parts.append(f"Background: {self.agent.backstory}")

        return "\n\n".join(parts)

    async def _get_skill_sources(self) -> list[str]:
        """Get skill sources from agent's skills."""
        sources = []
        for skill_id in self.agent.skill_ids:
            skill = await self.storage.get_skill(skill_id)
            if skill and skill.path:
                sources.append(skill.path)
        return sources