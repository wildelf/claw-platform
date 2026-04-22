"""Feedback application service."""

from typing import List, Optional

from app.domain.feedback import FeedbackEvent, FeedbackRating
from app.infrastructure.storage.sqlite import SQLiteStorage


class FeedbackService:
    """Service for feedback operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, feedback: FeedbackEvent) -> FeedbackEvent:
        """Create a new feedback event."""
        try:
            await self.storage.save_feedback(feedback)
        except Exception as e:
            raise RuntimeError(f"Failed to save feedback: {e}") from e
        return feedback

    async def submit_with_evolution(
        self,
        feedback: FeedbackEvent,
    ) -> tuple[FeedbackEvent, Optional[str]]:
        """Submit feedback and trigger evolution if needed.

        Returns:
            Tuple of (feedback, evolved_skill_id if triggered)
        """
        from app.application.skill_evolution_service import SkillEvolutionService

        # Save feedback
        await self.storage.save_feedback(feedback)

        # Process evolution
        evolution_service = SkillEvolutionService(self.storage)
        evolved_skill_id = await evolution_service.process_feedback(feedback)

        return feedback, evolved_skill_id

    async def get(self, feedback_id: str) -> Optional[FeedbackEvent]:
        """Get feedback by ID."""
        return await self.storage.get_feedback(feedback_id)

    async def list_by_skill(
        self,
        skill_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> List[FeedbackEvent]:
        """List feedback for a skill."""
        return await self.storage.list_feedback(skill_id=skill_id, offset=offset, limit=limit)

    async def list_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> List[FeedbackEvent]:
        """List all feedback."""
        return await self.storage.list_feedback(offset=offset, limit=limit)
