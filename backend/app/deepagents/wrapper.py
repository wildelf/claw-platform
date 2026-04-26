"""DeepAgents runtime wrapper.

This module provides integration with the deepagents library for
agent execution.
"""

import asyncio
import base64
import re
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from deepagents import create_deep_agent
from deepagents.graph import create_deep_agent
from deepagents.backends.state import StateBackend

from app.deepagents.skills_middleware import SkillEventMiddleware

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
        override_model_config_id: str | None = None,
    ):
        self.agent = agent
        self.storage = storage
        self._runner = None
        self._mcp_adapters: dict[str, MCPAdapter] = {}
        self._extra_skill_paths = extra_skill_paths or []
        self._system_prompt_override = system_prompt_override
        self._skill_event_queue: asyncio.Queue[dict] | None = None
        self._override_model_config_id = override_model_config_id

    async def create(self):
        """Create deepagents runner instance."""
        # 1. Create unified workspace directory first
        workspace_dir = Path(tempfile.mkdtemp(prefix="agent_workspace_"))
        skills_dir = workspace_dir / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        # 2. Get skill sources using the same workspace directory
        skill_sources = await self._get_skill_sources(workspace_dir)

        # 3. Load tools
        tools = await self._load_tools()

        # 4. Resolve model configuration
        model = await self._resolve_model()

        # 5. Build system prompt from agent config
        system_prompt = self._system_prompt_override or self._build_system_prompt()

        # 6. Create backend - single FilesystemBackend with virtual_mode=True for proper path resolution
        from deepagents.backends.filesystem import FilesystemBackend

        # Use virtual_mode=True so paths like /images/xxx.png resolve to {workspace_dir}/images/xxx.png
        backend = FilesystemBackend(root_dir=str(workspace_dir), virtual_mode=True)

        # Store for later use
        self._workspace_dir = workspace_dir

        # 7. Create deep_agent with skills
        self._runner = create_deep_agent(
            model=model,
            tools=tools if tools else None,
            system_prompt=system_prompt,
            skills=skill_sources if skill_sources else None,
            backend=backend,
        )
        self._backend = backend

    async def run(self, task: str, images: list[str] = None) -> AsyncGenerator[dict, None]:
        """Run agent task.

        Args:
            task: The task description.
            images: Optional list of base64 encoded images.

        Yields:
            Event dicts with type and data.
        """
        if not self._runner:
            await self.create()

        # Handle images - upload to backend with virtual path
        image_paths: list[str] = []
        if images:
            for idx, img_data in enumerate(images):
                # Decode base64 image
                if img_data.startswith("data:"):
                    # Format: data:image/png;base64,<base64_data>
                    base64_data = img_data.split(",", 1)[1]
                    media_type = img_data.split(";")[0].replace("data:", "")
                    ext = "png" if "png" in media_type else "jpg"
                else:
                    base64_data = img_data
                    ext = "png"

                image_filename = f"uploaded_image_{idx}.{ext}"
                image_content = base64.b64decode(base64_data)

                # Upload to backend using virtual path - with virtual_mode=True,
                # /images/xxx.png resolves to {workspace_dir}/images/xxx.png
                virtual_path = f"/images/{image_filename}"
                self._backend.upload_files([(virtual_path, image_content)])
                image_paths.append(virtual_path)

            # Prepend image paths to task
            image_desc = "\n".join([f"- Image {i+1}: {path}" for i, path in enumerate(image_paths)])
            task_with_images = f"""{task}

The user has uploaded {len(image_paths)} image(s) for you to process. You MUST use these exact file paths to read the images:
{image_desc}

IMPORTANT: When the user asks to manipulate an image (like "rotate the image"), use the exact file path shown above with your image processing tool. Do NOT ask the user for image paths - they have already been provided."""
            input_data = {"messages": [{"role": "user", "content": task_with_images}]}

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

        # Use astream with multiple stream modes
        # - "custom": for skill events via StreamWriter
        # - "messages": for LLM token-by-token output
        # - "updates": for node/task updates
        modes = ["custom", "messages", "updates"]

        async for chunk in self._runner.astream(input_data, stream_mode=modes):
            # Handle tuple format when multiple modes are enabled: (mode, data)
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, data = chunk
                if mode == "custom":
                    # Custom events from StreamWriter (skill events, etc.)
                    if isinstance(data, dict):
                        yield data
                elif mode == "messages":
                    # LLM token messages - extract content
                    content = self._extract_message_content(data)
                    if content:
                        yield {
                            "type": "content",
                            "content": content,
                        }
                elif mode == "updates":
                    # Node/task updates - extract relevant info
                    update = self._extract_update_content(data)
                    if update:
                        yield {
                            "type": "update",
                            "data": update,
                        }
            elif isinstance(chunk, dict):
                # Fallback for single mode or direct dict
                tool_calls = self._extract_tool_info(chunk)
                if tool_calls:
                    skill_event = self._detect_skill_file_access(tool_calls)
                    if skill_event:
                        yield skill_event

                    for tool_info in tool_calls:
                        yield {
                            "type": "tool_call",
                            "tool": tool_info["name"],
                            "input": tool_info.get("input"),
                        }

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

    def _extract_message_content(self, data) -> str | None:
        """Extract content from LLM message chunks in messages mode."""
        if data is None:
            return None
        # messages mode emits LLM token tuples (token, metadata)
        if isinstance(data, tuple) and len(data) >= 1:
            token = data[0]
            if isinstance(token, str):
                return token
            elif hasattr(token, 'content'):
                return str(token.content)
        elif isinstance(data, str):
            return data
        return None

    def _extract_update_content(self, data) -> Any | None:
        """Extract content from node/task updates in updates mode."""
        if data is None:
            return None
        # Updates can be node names, task results, etc.
        if isinstance(data, dict):
            return data
        elif isinstance(data, str):
            return {"update": data}
        return data

    def _extract_tool_info(self, chunk) -> list[dict] | None:
        """Extract tool call info from a chunk."""
        tool_calls = []

        # Try different formats of tool calls in LangChain/DeepAgents
        # Format 1: {"tool_calls": [...]}
        if "tool_calls" in chunk:
            calls = chunk["tool_calls"]
            if calls and len(calls) > 0:
                for call in calls:
                    tool_calls.append({
                        "name": call.get("name", "unknown"),
                        "input": call.get("input"),
                    })

        # Format 2: nested in messages
        if "messages" in chunk:
            for msg in chunk["messages"]:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for call in msg.tool_calls:
                        tool_calls.append({
                            "name": call.get("name", "unknown"),
                            "input": call.get("input"),
                        })

        return tool_calls if tool_calls else None

    def _detect_skill_file_access(self, tool_calls: list[dict]) -> dict | None:
        """Detect if a tool call is accessing a skill file.

        Returns skill event info if a skill file is being read.
        """
        for call in tool_calls:
            name = call.get("name", "")
            if name == "read_file":
                path = call.get("input", {})
                if isinstance(path, dict):
                    file_path = path.get("file_path", "")
                else:
                    file_path = str(path)

                # Check if reading a SKILL.md file
                if "SKILL.md" in file_path or "/skills/" in file_path:
                    # Extract skill name from path
                    # Path format: /skills/{skill_id}/SKILL.md or similar
                    parts = file_path.split("/")
                    for i, part in enumerate(parts):
                        if part == "skills" and i + 1 < len(parts):
                            skill_id = parts[i + 1]
                            return {
                                "type": "skill_reading",
                                "skill_id": skill_id,
                                "file": file_path.split("/")[-1],
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
        """Resolve model from agent configuration with override support."""
        from langchain_openai import ChatOpenAI

        # Priority 1: Temporary override
        if self._override_model_config_id:
            config = await self.storage.get_model_config(self._override_model_config_id)
            if config:
                return self._create_model_from_config(config)
            raise ValueError(f"Override model config not found: {self._override_model_config_id}")

        # Priority 2: Agent default model
        if self.agent.model_config_id:
            config = await self.storage.get_model_config(self.agent.model_config_id)
            if config:
                return self._create_model_from_config(config)

        # Priority 3: System default
        default_model = settings.models.default
        if default_model.base_url:
            return ChatOpenAI(
                model=default_model.model,
                api_key=default_model.api_key,
                base_url=default_model.base_url,
            )
        return f"openai:{default_model.model}"

    def _create_model_from_config(self, config):
        """Create LangChain model from ModelConfig."""
        from langchain_openai import ChatOpenAI
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

    async def _get_skill_sources(self, workspace_dir: Path) -> list[str]:
        """Get skill sources from agent's skills.

        Exports skill files to a temp directory so deepagents can read them.
        The directory structure follows deepagents conventions: skills are at
        /skills/{skill_id}/SKILL.md.

        Args:
            workspace_dir: The workspace directory to store skills under.
        """
        from pathlib import Path

        skills_dir = workspace_dir / "skills"
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