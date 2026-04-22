"""Feedback domain entities."""

from app.domain.base import BaseEntity
from enum import Enum
from typing import Optional, Dict, Any


class FeedbackRating(Enum):
    """Feedback rating values."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FeedbackEvent(BaseEntity):
    """Feedback event entity."""

    agent_id: str
    task_id: str
    result: str
    rating: FeedbackRating
    skill_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
