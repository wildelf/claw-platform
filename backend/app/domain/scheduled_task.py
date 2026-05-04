"""Scheduled task domain entity."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class ScheduleType(str, Enum):
    ONCE = "once"
    CRON = "cron"
    INTERVAL = "interval"


class ScheduledTaskStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduledTask(BaseEntity):
    """Scheduled task entity for agent execution scheduling."""

    name: str = Field(max_length=100)
    description: str = Field(max_length=500, default="")
    agent_id: EntityId
    user_id: EntityId

    # Schedule configuration
    schedule_type: ScheduleType
    cron_expression: Optional[str] = None  # For CRON type
    interval_seconds: Optional[int] = None  # For INTERVAL type
    run_at: Optional[datetime] = None  # For ONCE type

    # Task configuration
    task_input: str = Field(max_length=5000, default="")
    model_config_id: Optional[EntityId] = None  # Override default model

    # Status
    status: ScheduledTaskStatus = ScheduledTaskStatus.ACTIVE

    # Execution tracking
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    last_error: Optional[str] = None

    class Config:
        use_enum_values = True