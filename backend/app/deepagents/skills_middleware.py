"""Custom SkillsMiddleware with event emission via stream_writer.

This middleware extends the base SkillsMiddleware to emit events when:
1. Skills are being loaded (before_agent)
2. A skill file is being read (wrap_tool_call)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated, Any, Literal, cast

import yaml
from langchain.agents.middleware.types import PrivateStateAttr
from langchain.tools import ToolRuntime
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from langgraph.types import Command

from deepagents.backends.protocol import LsResult
from deepagents.middleware.skills import (
    SKILLS_SYSTEM_PROMPT,
    SkillsMiddleware as BaseSkillsMiddleware,
    SkillsState,
    SkillsStateUpdate,
    _format_skill_annotations,
    _list_skills,
    _parse_skill_metadata,
)
from deepagents.middleware._utils import append_to_system_message
from deepagents.middleware.skills import SkillMetadata

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from deepagents.backends.protocol import BACKEND_TYPES, BackendProtocol


class SkillEventMiddleware(BaseSkillsMiddleware):
    """SkillsMiddleware with event emission for skill loading and usage.

    Emits events via stream_writer when:
    - `skill_loading`: When a skill starts loading
    - `skill_loaded`: When a skill is successfully loaded
    - `skill_reading`: When the agent reads a skill file via read_file tool

    Example:
        ```python
        middleware = SkillEventMiddleware(
            backend=my_backend,
            sources=["/skills/user/"],
        )
        ```
    """

    def __init__(
        self,
        *,
        backend: BACKEND_TYPES,
        sources: list[str],
        event_handler: Callable[[dict], None] | None = None,
    ) -> None:
        """Initialize the skill event middleware.

        Args:
            backend: Backend instance for file operations
            sources: List of skill source paths
            event_handler: Optional callback for handling events.
                         If not provided, events are sent via stream_writer.
        """
        super().__init__(backend=backend, sources=sources)
        self._event_handler = event_handler

    def _emit_event(self, runtime: Runtime, event: dict) -> None:
        """Emit an event via stream_writer or event_handler."""
        if self._event_handler:
            self._event_handler(event)
        elif runtime.stream_writer:
            runtime.stream_writer(event)

    def before_agent(
        self, state: SkillsState, runtime: Runtime, config: RunnableConfig
    ) -> SkillsStateUpdate | None:
        """Load skills metadata before agent execution, emitting events."""
        # Skip if skills_metadata is already present in state
        if "skills_metadata" in state:
            return None

        # Emit skill_loading event for each source
        for source_path in self.sources:
            self._emit_event(
                runtime,
                {
                    "type": "skill_loading",
                    "source": source_path,
                },
            )

        # Call parent implementation
        result = super().before_agent(state, runtime, config)

        # Emit skill_loaded events for each skill
        if result and result.get("skills_metadata"):
            for skill in result["skills_metadata"]:
                self._emit_event(
                    runtime,
                    {
                        "type": "skill_loaded",
                        "skill_id": skill.get("path", "").split("/")[-2],
                        "skill_name": skill.get("name", ""),
                    },
                )

        return result

    async def abefore_agent(
        self, state: SkillsState, runtime: Runtime, config: RunnableConfig
    ) -> SkillsStateUpdate | None:
        """Load skills metadata before agent execution, emitting events (async)."""
        # Skip if skills_metadata is already present in state
        if "skills_metadata" in state:
            return None

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"abefore_agent: sources = {self.sources}")

        # Emit skill_loading event for each source
        for source_path in self.sources:
            logger.info(f"abefore_agent: emitting skill_loading for source={source_path}")
            self._emit_event(
                runtime,
                {
                    "type": "skill_loading",
                    "source": source_path,
                },
            )

        # Call parent implementation
        result = await super().abefore_agent(state, runtime, config)

        # Emit skill_loaded events for each skill
        if result and result.get("skills_metadata"):
            for skill in result["skills_metadata"]:
                self._emit_event(
                    runtime,
                    {
                        "type": "skill_loaded",
                        "skill_id": skill.get("path", "").split("/")[-2],
                        "skill_name": skill.get("name", ""),
                    },
                )

        return result

    def _is_skill_file_access(self, tool_name: str, tool_input: dict) -> tuple[bool, str | None]:
        """Check if a tool call is accessing a skill file.

        Returns:
            Tuple of (is_skill_access, skill_id_or_path)
        """
        if tool_name != "read_file":
            return False, None

        file_path = tool_input.get("file_path", "")
        if not file_path:
            return False, None

        # Check if path contains /skills/ or ends with SKILL.md
        if "/skills/" in file_path or "/SKILL.md" in file_path:
            # Extract skill path
            match = re.search(r"/skills/([^/]+)", file_path)
            if match:
                return True, match.group(1)

        return False, None

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        """Intercept tool calls to emit skill_reading events."""
        tool_call = request.tool_call
        tool_name = tool_call.get("name", "")
        tool_input = tool_call.get("input", {})

        is_skill, skill_id = self._is_skill_file_access(tool_name, tool_input)
        if is_skill and request.runtime:
            self._emit_event(
                request.runtime,
                {
                    "type": "skill_reading",
                    "skill_id": skill_id,
                    "file": tool_input.get("file_path", ""),
                },
            )

        return handler(request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        """Intercept tool calls to emit skill_reading events (async)."""
        import logging
        logger = logging.getLogger(__name__)

        tool_call = request.tool_call
        tool_name = tool_call.get("name", "")
        tool_input = tool_call.get("input", {})
        file_path = tool_input.get("file_path", "")

        logger.info(f"awrap_tool_call: tool={tool_name}, file_path={file_path}")

        is_skill, skill_id = self._is_skill_file_access(tool_name, tool_input)
        if is_skill and request.runtime:
            logger.info(f"awrap_tool_call: detected skill access, skill_id={skill_id}")
            self._emit_event(
                request.runtime,
                {
                    "type": "skill_reading",
                    "skill_id": skill_id,
                    "file": file_path,
                },
            )

            # Rewrite the file path to point to the actual workspace location
            # This handles cases where AI has stale paths in context
            if tool_name == "read_file" and self._backend is not None:
                new_path = self._resolve_skill_file_path(file_path, skill_id)
                if new_path and new_path != file_path:
                    logger.info(f"Rewriting skill file path: {file_path} -> {new_path}")
                    tool_input["file_path"] = new_path
                    tool_call["input"] = tool_input

        return await handler(request)

    def _resolve_skill_file_path(self, file_path: str, skill_id: str | None) -> str | None:
        """Resolve a skill file path to the actual workspace path.

        Handles cases where the AI has stale paths in its context that don't
        match the actual workspace structure.
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self._backend:
            return None

        filename = file_path.split("/")[-1] if "/" in file_path else file_path

        # Try to find the actual skill directory by listing
        try:
            ls_result = self._backend.ls("/skills/")
            if ls_result.error or not ls_result.entries:
                return None

            for entry in ls_result.entries:
                if not entry.get("is_dir"):
                    continue
                entry_path = entry.get("path", "")

                # Check if this is the skill we're looking for by ID
                if skill_id and skill_id in entry_path:
                    logger.info(f"_resolve_skill_file_path: matched by skill_id {skill_id} -> {entry_path}")
                    return f"{entry_path}/{filename}"

            # No direct ID match - try to find any valid skill directory
            # and use it (for single-skill execution, there's only one skill anyway)
            for entry in ls_result.entries:
                if not entry.get("is_dir"):
                    continue
                entry_path = entry.get("path", "")

                # Try to read SKILL.md from this directory
                skill_md_path = f"{entry_path}/SKILL.md"
                try:
                    read_result = self._backend.read(skill_md_path)
                    if read_result.file_data is None or read_result.error:
                        continue

                    content = read_result.file_data.get("content", "")

                    # Check if this skill's name matches what the AI is looking for
                    # skill_id from _is_skill_file_access extracts the path component
                    # which could be "daily-ai-news" from "/skills/daily-ai-news/SKILL.md"
                    if skill_id:
                        # Check if skill_id appears in the content (as name or slug)
                        if skill_id.lower() in content.lower():
                            logger.info(f"_resolve_skill_file_path: matched by slug '{skill_id}' in content")
                            return f"{entry_path}/{filename}"

                    # For single-skill execution, just return the first valid skill
                    # This handles cases where AI uses wrong path but there's only one skill
                    logger.info(f"_resolve_skill_file_path: using first available skill at {entry_path}")
                    return f"{entry_path}/{filename}"
                except Exception as e:
                    logger.warning(f"_resolve_skill_file_path: error reading {skill_md_path}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error resolving skill file path: {e}")

        return None
