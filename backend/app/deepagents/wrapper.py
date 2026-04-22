"""DeepAgents runtime wrapper.

This module provides integration with the deepagents library for
agent execution.
"""

import asyncio
from typing import Any, AsyncGenerator, Optional

from deepagents import create_deep_agent, SkillsMiddleware
from deepagents.backends.state import StateBackend

from app.domain.agent import Agent
from app.domain.tool import Tool, ToolType
from app.domain.model_config import ModelConfig, ModelProviderType
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.infrastructure.mcp.adapter import MCPAdapter
from app.infrastructure.model.openai import OpenAIAdapter
from app.infrastructure.model.anthropic import AnthropicAdapter


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
            tools=tools,
            middleware=[skills_middleware],
            system_prompt=system_prompt,
        )

    async def run(self, task: str) -> AsyncGenerator[Any, None]:
        """Run agent task.

        Yields:
            Events from agent execution.
        """
        if not self._runner:
            await self.create()

        async for event in self._runner.astream_events(task):
            yield event

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
        """Resolve model from agent configuration."""
        if not self.agent.model_config_id:
            # Use default model
            return OpenAIAdapter(ModelConfig(
                name="default",
                type=ModelProviderType.OPENAI,
                model="gpt-4o",
                user_id=self.agent.user_id,
            ))

        config = await self.storage.get_model_config(self.agent.model_config_id)
        if not config:
            raise ValueError(f"Model config not found: {self.agent.model_config_id}")

        if config.type == ModelProviderType.OPENAI:
            return OpenAIAdapter(config)
        elif config.type == ModelProviderType.ANTHROPIC:
            return AnthropicAdapter(config)
        else:
            raise ValueError(f"Unsupported model type: {config.type}")

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