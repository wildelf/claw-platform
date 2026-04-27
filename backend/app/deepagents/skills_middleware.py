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

        return await handler(request)
