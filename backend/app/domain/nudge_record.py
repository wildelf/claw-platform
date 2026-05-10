from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.domain.base import BaseEntity, EntityId


class NudgeType(str, Enum):
    MEMORY = "memory"
    SKILL = "skill"
    BOTH = "both"


class NudgePriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NudgeRecord(BaseEntity):
    agent_id: EntityId
    session_id: str
    memory_type: str  # "MEMORY.md" | "USER.md" | "skill"
    content: str
    trigger_reason: str  # "rule" | "reasoning" | "composite"
    priority: str  # "high" | "medium" | "low"

    @staticmethod
    def create(
        agent_id: str,
        session_id: str,
        memory_type: str,
        content: str,
        trigger_reason: str,
        priority: str = "medium",
    ) -> "NudgeRecord":
        return NudgeRecord(
            id=EntityId.generate(),
            agent_id=EntityId(agent_id),
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            trigger_reason=trigger_reason,
            priority=priority,
            created_at=datetime.now(timezone.utc),
        )