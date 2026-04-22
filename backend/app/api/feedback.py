"""Feedback API routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage
from app.application.feedback_service import FeedbackService
from app.domain.feedback import FeedbackEvent, FeedbackRating
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feedback", tags=["feedback"])


class CreateFeedbackRequest(BaseModel):
    agent_id: str
    skill_id: Optional[str] = None
    task_id: str
    result: str
    rating: FeedbackRating
    context: dict = Field(default_factory=dict)


@router.post("", response_model=FeedbackEvent)
async def create_feedback(
    request: CreateFeedbackRequest,
    storage: Storage,
) -> FeedbackEvent:
    """Submit a feedback event."""
    feedback = FeedbackEvent(
        agent_id=request.agent_id,
        skill_id=request.skill_id,
        task_id=request.task_id,
        result=request.result,
        rating=request.rating,
        context=request.context,
    )
    service = FeedbackService(storage)
    return await service.create(feedback)


@router.get("", response_model=List[FeedbackEvent])
async def list_feedback(
    storage: Storage,
    skill_id: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> List[FeedbackEvent]:
    """List feedback events."""
    service = FeedbackService(storage)
    if skill_id:
        return await service.list_by_skill(skill_id, offset, limit)
    return await service.list_all(offset, limit)


@router.get("/{feedback_id}", response_model=FeedbackEvent)
async def get_feedback(
    feedback_id: str,
    storage: Storage,
) -> FeedbackEvent:
    """Get feedback by ID."""
    service = FeedbackService(storage)
    feedback = await service.get(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback
