"""Feedback API routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage
from app.application.feedback_service import FeedbackService
from app.domain.feedback import FeedbackEvent, FeedbackRating
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feedback", tags=["feedback"])


class CreateFeedbackRequest(BaseModel):
    agent_id: str = Field(..., max_length=36)
    skill_id: Optional[str] = Field(None, max_length=36)
    task_id: str = Field(..., max_length=36)
    result: str = Field(..., max_length=10000)
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


@router.post("/{feedback_id}/process")
async def process_feedback(
    feedback_id: str,
    storage: Storage,
) -> dict:
    """Process a feedback event and trigger evolution if needed.

    This endpoint is for manually triggering evolution processing
    on a feedback event (e.g., after reviewing the feedback).
    """
    service = FeedbackService(storage)
    feedback = await service.get(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    _, evolved_skill_id = await service.submit_with_evolution(feedback)

    return {
        "feedback_id": feedback_id,
        "evolved_skill_id": evolved_skill_id,
        "evolution_triggered": evolved_skill_id is not None,
    }


@router.get("/skills/{skill_id}/evolution-history")
async def get_skill_evolution_history(
    skill_id: str,
    storage: Storage,
    offset: int = 0,
    limit: int = 50,
) -> List[FeedbackEvent]:
    """Get feedback history for a skill that contributed to evolution."""
    service = FeedbackService(storage)
    feedbacks = await service.list_by_skill(skill_id, offset, limit)
    return [f for f in feedbacks if f.rating == FeedbackRating.POSITIVE.value]
