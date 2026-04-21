"""Agent domain entity."""

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class AgentStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"


class Agent(BaseEntity):
    """Agent entity representing an AI agent."""

    name: str = Field(max_length=100)
    description: str = Field(max_length=1000, default="")
    role: str = Field(max_length=500, default="")
    goal: str = Field(max_length=1000, default="")
    backstory: str = Field(max_length=2000, default="")
    skill_ids: List[EntityId] = Field(default_factory=list)
    tool_ids: List[EntityId] = Field(default_factory=list)
    model_config_id: EntityId | None = None
    status: AgentStatus = AgentStatus.PENDING
    user_id: EntityId

    class Config:
        use_enum_values = True