"""Tests for skill service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.skill_service import SkillService
from app.domain.skill import Skill, SkillStatus
from app.domain.base import EntityId


@pytest.fixture
def mock_storage():
    """Create a mock storage."""
    storage = MagicMock()
    storage.get_skill = AsyncMock()
    storage.save_skill = AsyncMock(return_value=None)
    storage.delete_skill = AsyncMock(return_value=None)
    storage.list_skill_files = AsyncMock(return_value=[])
    storage.get_skill_file = AsyncMock(return_value=None)
    storage.save_skill_file = AsyncMock(return_value=None)
    storage.delete_skill_file = AsyncMock(return_value=None)
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


class TestSkillService:
    """Tests for SkillService."""

    @pytest.mark.asyncio
    async def test_create_skill(self, mock_storage, sample_skill):
        """Creating a skill should save it to storage."""
        service = SkillService(mock_storage)
        result = await service.create(sample_skill)
        assert result.name == sample_skill.name
        mock_storage.save_skill.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_skill_returns_none_when_not_found(self, mock_storage):
        """get_skill should return None for non-existent skill."""
        mock_storage.get_skill.return_value = None
        service = SkillService(mock_storage)
        result = await service.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_skill_returns_skill(self, mock_storage, sample_skill):
        """get_skill should return skill when found."""
        mock_storage.get_skill.return_value = sample_skill
        service = SkillService(mock_storage)
        result = await service.get(sample_skill.id)
        assert result == sample_skill

    @pytest.mark.asyncio
    async def test_update_skill(self, mock_storage, sample_skill):
        """Updating a skill should save it."""
        mock_storage.get_skill.return_value = sample_skill
        service = SkillService(mock_storage)
        result = await service.update(sample_skill.id, {"name": "updated-name"})
        assert result.name == "updated-name"
        mock_storage.save_skill.assert_called()

    @pytest.mark.asyncio
    async def test_update_skill_returns_none_when_not_found(self, mock_storage):
        """update_skill should return None for non-existent skill."""
        mock_storage.get_skill.return_value = None
        service = SkillService(mock_storage)
        result = await service.update("nonexistent", {"name": "test"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_skill_returns_true_when_found(self, mock_storage, sample_skill):
        """delete_skill should return True when skill exists."""
        mock_storage.get_skill.return_value = sample_skill
        mock_storage.delete_skill.return_value = True
        service = SkillService(mock_storage)
        result = await service.delete("skill-id")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_skill_returns_false_when_not_found(self, mock_storage):
        """delete_skill should return False when skill doesn't exist."""
        mock_storage.get_skill.return_value = None
        service = SkillService(mock_storage)
        result = await service.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_file(self, mock_storage, sample_skill):
        """get_file should return file content."""
        mock_storage.get_skill_file.return_value = b"file content"
        service = SkillService(mock_storage)
        result = await service.get_file(sample_skill.id, "test.txt")
        assert result == b"file content"

    @pytest.mark.asyncio
    async def test_get_file_returns_none_when_not_found(self, mock_storage):
        """get_file should return None for non-existent file."""
        mock_storage.get_skill_file.return_value = None
        service = SkillService(mock_storage)
        result = await service.get_file("nonexistent", "test.txt")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_files(self, mock_storage, sample_skill):
        """list_files should return list of filenames."""
        mock_storage.list_skill_files.return_value = ["file1.txt", "file2.txt"]
        service = SkillService(mock_storage)
        result = await service.list_files(sample_skill.id)
        assert len(result) == 2
        assert "file1.txt" in result

    @pytest.mark.asyncio
    async def test_save_file(self, mock_storage, sample_skill):
        """save_file should save file to storage."""
        service = SkillService(mock_storage)
        await service.save_file(sample_skill.id, "test.txt", b"content")
        mock_storage.save_skill_file.assert_called_once_with(
            sample_skill.id, "test.txt", b"content"
        )

    @pytest.mark.asyncio
    async def test_delete_file(self, mock_storage, sample_skill):
        """delete_file should delete file from storage."""
        service = SkillService(mock_storage)
        await service.delete_file(sample_skill.id, "test.txt")
        mock_storage.delete_skill_file.assert_called_once_with(
            sample_skill.id, "test.txt"
        )