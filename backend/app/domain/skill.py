"""Skill domain entity."""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class SkillStatus(str, Enum):
    PENDING = "pending"
    TRAINED = "trained"
    EVOLVED = "evolved"
    NEEDS_REVIEW = "needs_review"


class FileType(str, Enum):
    MARKDOWN = "markdown"
    PYTHON = "python"
    OTHER = "other"


class SkillFile(BaseEntity):
    """File within a skill."""

    filename: str = Field(max_length=255)
    content: bytes = b""
    file_type: FileType = FileType.OTHER

    class Config:
        use_enum_values = True


class Skill(BaseEntity):
    """Skill entity representing an agent capability."""

    name: str = Field(max_length=64)
    description: str = Field(max_length=1024, default="")
    path: str = Field(max_length=500, default="")
    status: SkillStatus = SkillStatus.PENDING
    feedback_count: int = 0
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_id: EntityId

    class Config:
        use_enum_values = True