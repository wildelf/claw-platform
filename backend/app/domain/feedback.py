"""Feedback domain entities."""

from app.domain.base import BaseEntity
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any


class FeedbackRating(Enum):
    """Feedback rating values."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FeedbackEvent(BaseEntity):
    """Feedback event entity."""

    def __init__(
        self,
        id: str,
        agent_id: str,
        task_id: str,
        result: str,
        rating: FeedbackRating,
        created_at: datetime,
        skill_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.agent_id = agent_id
        self.skill_id = skill_id
        self.task_id = task_id
        self.result = result
        self.rating = rating
        self.context = context or {}
        self.created_at = created_at
