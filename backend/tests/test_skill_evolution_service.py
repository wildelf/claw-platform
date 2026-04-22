"""Tests for skill evolution service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.skill_evolution_service import SkillEvolutionService, DEFAULT_GENERATION_THRESHOLD
from app.domain.skill import Skill, SkillStatus
from app.domain.feedback import FeedbackEvent, FeedbackRating
from app.domain.base import EntityId


@pytest.fixture
def mock_storage():
    """Create a mock storage."""
    storage = MagicMock()
    storage.get_skill = AsyncMock()
    storage.save_skill = AsyncMock(return_value=None)
    storage.save_skill_file = AsyncMock(return_value=None)
    storage.get_skill_file = AsyncMock(return_value=None)
    return storage


@pytest.fixture
def sample_skill():
    """Create a sample skill for testing."""
    return Skill(
        name="test-skill",
        description="A test skill",
        status=SkillStatus.PENDING,
        feedback_count=0,
        version=1,
        user_id=EntityId.generate(),
    )


@pytest.fixture
def positive_feedback():
    """Create a positive feedback event."""
    return FeedbackEvent(
        agent_id="agent-1",
        task_id="task-1",
        result="Successfully executed",
        rating=FeedbackRating.POSITIVE,
        context={"task_description": "Test task", "steps": "Step 1, Step 2"},
    )


@pytest.fixture
def negative_feedback():
    """Create a negative feedback event."""
    return FeedbackEvent(
        agent_id="agent-1",
        task_id="task-1",
        result="Failed to execute",
        rating=FeedbackRating.NEGATIVE,
        context={"error": "Some error occurred"},
    )


class TestSkillEvolutionService:
    """Tests for SkillEvolutionService."""

    @pytest.mark.asyncio
    async def test_process_feedback_returns_none_when_no_skill_id(self, mock_storage):
        """Feedback without skill_id should return None."""
        service = SkillEvolutionService(mock_storage)
        feedback = FeedbackEvent(
            agent_id="agent-1",
            task_id="task-1",
            result="result",
            rating=FeedbackRating.POSITIVE,
        )

        result = await service.process_feedback(feedback)

        assert result is None
        mock_storage.get_skill.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_feedback_returns_none_when_skill_not_found(self, mock_storage):
        """Feedback for non-existent skill should return None."""
        mock_storage.get_skill.return_value = None
        service = SkillEvolutionService(mock_storage)
        feedback = FeedbackEvent(
            agent_id="agent-1",
            task_id="task-1",
            result="result",
            rating=FeedbackRating.POSITIVE,
            skill_id="nonexistent",
        )

        result = await service.process_feedback(feedback)

        assert result is None

    @pytest.mark.asyncio
    async def test_process_positive_feedback_increments_count(self, mock_storage, sample_skill, positive_feedback):
        """Positive feedback should increment feedback_count."""
        positive_feedback.skill_id = sample_skill.id
        mock_storage.get_skill.return_value = sample_skill
        service = SkillEvolutionService(mock_storage)

        await service.process_feedback(positive_feedback)

        assert sample_skill.feedback_count == 1
        assert mock_storage.save_skill.called

    @pytest.mark.asyncio
    async def test_process_positive_feedback_below_threshold_returns_none(self, mock_storage, sample_skill, positive_feedback):
        """Positive feedback below threshold should not trigger evolution."""
        positive_feedback.skill_id = sample_skill.id
        mock_storage.get_skill.return_value = sample_skill
        service = SkillEvolutionService(mock_storage, generation_threshold=3)

        result = await service.process_feedback(positive_feedback)

        assert result is None
        assert sample_skill.status == SkillStatus.PENDING

    @pytest.mark.asyncio
    async def test_process_positive_feedback_at_threshold_generates_skill(self, mock_storage, sample_skill, positive_feedback):
        """Positive feedback at threshold should generate skill files."""
        sample_skill.feedback_count = 2  # One away from threshold
        positive_feedback.skill_id = sample_skill.id
        mock_storage.get_skill.return_value = sample_skill
        service = SkillEvolutionService(mock_storage, generation_threshold=3)

        result = await service.process_feedback(positive_feedback)

        assert result == sample_skill.id
        assert sample_skill.feedback_count == 0
        assert sample_skill.status == SkillStatus.TRAINED
        mock_storage.save_skill.assert_called()

    @pytest.mark.asyncio
    async def test_process_negative_feedback_marks_for_review(self, mock_storage, sample_skill, negative_feedback):
        """Negative feedback should mark skill for review."""
        negative_feedback.skill_id = sample_skill.id
        mock_storage.get_skill.return_value = sample_skill
        service = SkillEvolutionService(mock_storage)

        result = await service.process_feedback(negative_feedback)

        assert result == sample_skill.id
        assert sample_skill.status == SkillStatus.NEEDS_REVIEW

    @pytest.mark.asyncio
    async def test_process_negative_feedback_stores_issue_in_metadata(self, mock_storage, sample_skill, negative_feedback):
        """Negative feedback should store issue in metadata."""
        negative_feedback.skill_id = sample_skill.id
        mock_storage.get_skill.return_value = sample_skill
        service = SkillEvolutionService(mock_storage)

        await service.process_feedback(negative_feedback)

        assert "issues" in sample_skill.metadata
        assert len(sample_skill.metadata["issues"]) == 1
        assert sample_skill.metadata["issues"][0]["feedback_id"] == negative_feedback.id

    @pytest.mark.asyncio
    async def test_evolve_skill_updates_version(self, mock_storage, sample_skill):
        """evolve_skill should increment version."""
        mock_storage.get_skill.return_value = sample_skill
        service = SkillEvolutionService(mock_storage)
        improvements = {"positive_patterns": ["pattern1"]}

        result = await service.evolve_skill(sample_skill.id, improvements)

        assert result.version == 2

    @pytest.mark.asyncio
    async def test_evolve_skill_stores_evolution_in_metadata(self, mock_storage, sample_skill):
        """evolve_skill should store evolution record in metadata."""
        mock_storage.get_skill.return_value = sample_skill
        service = SkillEvolutionService(mock_storage)
        improvements = {"positive_patterns": ["pattern1"]}

        await service.evolve_skill(sample_skill.id, improvements)

        assert "evolutions" in sample_skill.metadata
        assert len(sample_skill.metadata["evolutions"]) == 1

    @pytest.mark.asyncio
    async def test_evolve_skill_clears_needs_review_status(self, mock_storage, sample_skill):
        """evolve_skill should clear NEEDS_REVIEW status."""
        sample_skill.status = SkillStatus.NEEDS_REVIEW
        mock_storage.get_skill.return_value = sample_skill
        service = SkillEvolutionService(mock_storage)
        improvements = {"positive_patterns": ["pattern1"]}

        result = await service.evolve_skill(sample_skill.id, improvements)

        assert result.status == SkillStatus.EVOLVED

    @pytest.mark.asyncio
    async def test_evolve_skill_raises_for_nonexistent_skill(self, mock_storage):
        """evolve_skill should raise ValueError for nonexistent skill."""
        mock_storage.get_skill.return_value = None
        service = SkillEvolutionService(mock_storage)

        with pytest.raises(ValueError, match="Skill not found"):
            await service.evolve_skill("nonexistent", {})

    @pytest.mark.asyncio
    async def test_evolve_skill_updates_skill_files(self, mock_storage, sample_skill):
        """evolve_skill should update SKILL.md file."""
        mock_storage.get_skill.return_value = sample_skill
        mock_storage.get_skill_file.return_value = None
        service = SkillEvolutionService(mock_storage)
        improvements = {"positive_patterns": ["good pattern"], "negative_patterns": ["bad pattern"]}

        await service.evolve_skill(sample_skill.id, improvements)

        mock_storage.save_skill_file.assert_called()
        call_args = mock_storage.save_skill_file.call_args_list
        assert any("SKILL.md" in str(call) for call in call_args)