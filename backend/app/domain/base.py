"""Base classes for domain entities."""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EntityId(str):
    """Type-safe entity ID."""

    @classmethod
    def generate(cls) -> "EntityId":
        return cls(str(uuid.uuid4()))


class BaseEntity(BaseModel):
    """Base class for all domain entities."""

    model_config = {"arbitrary_types_allowed": True}

    id: EntityId = Field(default_factory=EntityId.generate)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __states: Any) -> None:
        """Update updated_at on init."""
        object.__setattr__(self, "updated_at", datetime.now(timezone.utc))