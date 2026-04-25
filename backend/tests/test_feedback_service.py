"""Tests for feedback service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.feedback_service import FeedbackService
from app.domain.feedback import FeedbackEvent, FeedbackRating
from app.domain.base import EntityId


@pytest.fixture
def mock_storage():
    """Create a mock storage."""
    storage = MagicMock()
    storage.save_feedback = AsyncMock(return_value=None)
    storage.get_feedback = AsyncMock()
    storage.list_feedback = AsyncMock(return_value=[])
    return storage


@pytest.fixture
def sample_feedback():
    """Create a sample feedback event for testing."""
    return FeedbackEvent(
        agent_id="agent-1",
        task_id="task-1",
        result="Successfully executed",
        rating=FeedbackRating.POSITIVE,
        context={"task_description": "Test task", "steps": "Step 1, Step 2"},
    )


class TestFeedbackService:
    """Tests for FeedbackService."""

    @pytest.mark.asyncio
    async def test_create_feedback(self, mock_storage, sample_feedback):
        """Creating feedback should save it to storage."""
        service = FeedbackService(mock_storage)
        await service.create(sample_feedback)
        mock_storage.save_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_feedback_returns_none_when_not_found(self, mock_storage):
        """get_feedback should return None for non-existent feedback."""
        mock_storage.get_feedback.return_value = None
        service = FeedbackService(mock_storage)
        result = await service.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_feedback_returns_feedback(self, mock_storage, sample_feedback):
        """get_feedback should return feedback when found."""
        mock_storage.get_feedback.return_value = sample_feedback
        service = FeedbackService(mock_storage)
        result = await service.get(sample_feedback.id)
        assert result == sample_feedback

    @pytest.mark.asyncio
    async def test_list_by_skill(self, mock_storage, sample_feedback):
        """list_by_skill should return feedback for a specific skill."""
        sample_feedback.skill_id = "skill-123"
        mock_storage.list_feedback.return_value = [sample_feedback]
        service = FeedbackService(mock_storage)
        result = await service.list_by_skill("skill-123", 0, 10)
        assert len(result) == 1
        assert result[0].skill_id == "skill-123"

    @pytest.mark.asyncio
    async def test_list_all_feedback(self, mock_storage, sample_feedback):
        """list_all should return all feedback."""
        mock_storage.list_feedback.return_value = [sample_feedback]
        service = FeedbackService(mock_storage)
        result = await service.list_all(0, 10)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_by_skill_empty_when_no_matches(self, mock_storage):
        """list_by_skill should return empty list when no matches."""
        mock_storage.list_feedback.return_value = []
        service = FeedbackService(mock_storage)
        result = await service.list_by_skill("nonexistent", 0, 10)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_submit_with_evolution(self, mock_storage, sample_feedback):
        """submit_with_evolution should call create and return skill_id."""
        service = FeedbackService(mock_storage)
        result = await service.submit_with_evolution(sample_feedback)
        assert mock_storage.save_feedback.called

    @pytest.mark.asyncio
    async def test_feedback_with_negative_rating(self, mock_storage):
        """Feedback with negative rating should be handled correctly."""
        feedback = FeedbackEvent(
            agent_id="agent-1",
            task_id="task-1",
            result="Failed: connection timeout",
            rating=FeedbackRating.NEGATIVE,
            skill_id="skill-456",
        )
        mock_storage.save_feedback.return_value = None
        service = FeedbackService(mock_storage)
        await service.create(feedback)
        mock_storage.save_feedback.assert_called()


class TestFeedbackRating:
    """Tests for FeedbackRating enum."""

    def test_positive_rating_value(self):
        """Positive rating should have correct value."""
        assert FeedbackRating.POSITIVE.value == "positive"

    def test_negative_rating_value(self):
        """Negative rating should have correct value."""
        assert FeedbackRating.NEGATIVE.value == "negative"

    def test_all_ratings_defined(self):
        """All expected ratings should be defined."""
        assert hasattr(FeedbackRating, "POSITIVE")
        assert hasattr(FeedbackRating, "NEGATIVE")