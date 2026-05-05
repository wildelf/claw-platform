"""Log domain entity for centralized logging."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class LogActionType(str, Enum):
    MCP_CALL = "mcp_call"
    SKILL_READING = "skill_reading"
    DECISION_BRANCH = "decision_branch"
    LLM_RESPONSE = "llm_response"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"


class LogEntry(BaseEntity):
    """Log entry for audit trail and debugging."""

    agent_id: EntityId
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action_type: LogActionType
    tool_name: str | None = None
    input_json: str | None = None  # JSON string, sanitized
    output_json: str | None = None  # JSON string, sanitized
    decision_context: str | None = None  # Decision tree node ID
    error: str | None = None

    # Extra fields for flexible metadata
    extra: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
