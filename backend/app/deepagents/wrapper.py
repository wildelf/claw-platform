"""DeepAgents runtime wrapper.

This module provides integration with the deepagents library for
agent execution.
"""

import asyncio
import re
from typing import Any, AsyncGenerator, Optional

from deepagents import create_deep_agent
from deepagents.graph import create_deep_agent
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
        extra_skill_paths: list[str] | None = None,
        system_prompt_override: str | None = None,
    ):
        self.agent = agent
        self.storage = storage
        self._runner = None
        self._mcp_adapters: dict[str, MCPAdapter] = {}
        self._extra_skill_paths = extra_skill_paths or []
        self._system_prompt_override = system_prompt_override

    async def create(self):
        """Create deepagents runner instance."""
        # 1. Get skill sources (temp directories with skill files)
        skill_sources = await self._get_skill_sources()

        # 2. Load tools
        tools = await self._load_tools()

        # 3. Resolve model configuration
        model = await self._resolve_model()

        # 4. Build system prompt from agent config
        system_prompt = self._system_prompt_override or self._build_system_prompt()

        # 5. Create backend - use FilesystemBackend for skills if available
        if skill_sources:
            from deepagents.backends.filesystem import FilesystemBackend
            backend = FilesystemBackend(root_dir=skill_sources[0])
        else:
            backend = StateBackend()

        # 6. Create deep_agent with skills
        self._runner = create_deep_agent(
            model=model,
            tools=tools if tools else None,
            system_prompt=system_prompt,
            skills=skill_sources if skill_sources else None,
            backend=backend,
        )

    async def run(self, task: str) -> AsyncGenerator[dict, None]:
        """Run agent task.

        Yields:
            Event dicts with type and data.
        """
        if not self._runner:
            await self.create()

        # deepagents expects dict input with 'messages' key for chat models
        input_data = {"messages": [{"role": "user", "content": task}]}

        # Emit preparing event
        yield {
            "type": "preparing",
            "message": "准备执行环境...",
        }

        # Emit skill loading events for bound skills
        if self.agent.skill_ids:
            for skill_id in self.agent.skill_ids:
                skill = await self.storage.get_skill(skill_id)
                if skill:
                    yield {
                        "type": "skill_loading",
                        "skill_id": str(skill_id),
                        "skill_name": skill.name,
                    }
                    yield {
                        "type": "skill_loaded",
                        "skill_id": str(skill_id),
                        "skill_name": skill.name,
                    }
        else:
            yield {
                "type": "preparing",
                "message": "无绑定的 skills，开始执行...",
            }

        # Emit thinking event
        yield {
            "type": "thinking",
            "message": "AI 正在思考...",
        }

        # Use astream to get incremental output chunks
        async for chunk in self._runner.astream(input_data):
            if not isinstance(chunk, dict):
                continue

            # Check for tool calls in the chunk
            tool_info = self._extract_tool_info(chunk)
            if tool_info:
                yield {
                    "type": "tool_call",
                    "tool": tool_info["name"],
                    "input": tool_info.get("input"),
                }

            # Extract content from various chunk formats
            content = self._extract_content(chunk)
            if content:
                yield {
                    "type": "content",
                    "content": content,
                }

    def _extract_content(self, chunk) -> str | None:
        """Extract text content from a chunk."""
        if "model" in chunk:
            model_data = chunk["model"]
            if isinstance(model_data, dict) and "messages" in model_data:
                for msg in model_data["messages"]:
                    if hasattr(msg, 'content') and msg.content:
                        return msg.content
        elif "messages" in chunk:
            for msg in chunk["messages"]:
                if hasattr(msg, 'content') and msg.content:
                    return msg.content
        return None

    def _extract_tool_info(self, chunk) -> dict | None:
        """Extract tool call info from a chunk."""
        # Try different formats of tool calls in LangChain/DeepAgents
        # Format 1: {"tool_calls": [...]}
        if "tool_calls" in chunk:
            tool_calls = chunk["tool_calls"]
            if tool_calls and len(tool_calls) > 0:
                call = tool_calls[0]
                return {
                    "name": call.get("name", "unknown"),
                    "input": call.get("input"),
                }
        # Format 2: nested in messages
        if "messages" in chunk:
            for msg in chunk["messages"]:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    call = msg.tool_calls[0]
                    return {
                        "name": call.get("name", "unknown"),
                        "input": call.get("input"),
                    }
        return None

    async def stop(self):
        """Stop running agent and cleanup."""
        # Close all MCP connections
        for adapter in self._mcp_adapters.values():
            await adapter.close()
        self._mcp_adapters.clear()
        self._runner = None

    async def _load_agent_skills_to_backend(self, backend):
        """Load agent's skills from database into backend.

        Args:
            backend: StateBackend to load skills into
        """
        from deepagents.backends.state import StateBackend

        if not isinstance(backend, StateBackend):
            return

        for skill_id in self.agent.skill_ids:
            skill = await self.storage.get_skill(skill_id)
            if not skill:
                continue
            # List all files for this skill
            files = await self.storage.list_skill_files(str(skill_id))
            for filename in files:
                content = await self.storage.get_skill_file(str(skill_id), filename)
                if content:
                    # Path format: /skills/{skill_id}/{filename}
                    path = f"/skills/{skill_id}/{filename}"
                    if isinstance(content, str):
                        content = content.encode("utf-8")
                    backend.upload_files([(path, content)])

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
        """Get skill sources from agent's skills.

        Exports skill files to a temp directory so deepagents can read them.
        The directory structure follows deepagents conventions: skills are at
        /skills/{skill_id}/SKILL.md.
        """
        import tempfile
        from pathlib import Path

        sources = []
        temp_dir = Path(tempfile.mkdtemp(prefix="skills_"))
        skills_dir = temp_dir / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        for skill_id in self.agent.skill_ids:
            skill = await self.storage.get_skill(skill_id)
            if not skill:
                continue

            # Create skill directory: /temp/skills_xxx/skills/{skill_id}/
            skill_dir = skills_dir / skill_id
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Export all skill files to temp directory
            files = await self.storage.list_skill_files(str(skill_id))
            for filename in files:
                content = await self.storage.get_skill_file(str(skill_id), filename)
                if content:
                    file_path = skill_dir / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, bytes):
                        file_path.write_bytes(content)
                    else:
                        file_path.write_text(content, encoding="utf-8")

        # Return the temp/skills directory as the source
        return [str(skills_dir)]

    def _add_filesystem_skill_to_backend(self, backend: StateBackend, skill_path: str):
        """Add a filesystem-based skill to the backend.

        Args:
            backend: StateBackend to add files to
            skill_path: Absolute path to the skill directory
        """
        import os
        from pathlib import Path

        skill_dir = Path(skill_path)
        if not skill_dir.exists():
            return

        # Add all files from the skill directory to the backend
        for root, dirs, files in os.walk(skill_dir):
            for filename in files:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(skill_dir.parent)
                content = file_path.read_text(encoding="utf-8")
                backend.upload_files([(str(rel_path), content.encode("utf-8"))])