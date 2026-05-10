"""Tests for SkillCurator."""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from app.application.skill_curator import bump_use, SkillCurator


def test_bump_use_increments_count(tmp_path):
    """Test that bump_use correctly increments use count"""
    # Mock settings
    with patch("app.config.settings", type("Settings", (), {
        "skills_cache_path": str(tmp_path)
    })()):
        skill_name = "test-skill"
        bump_use(skill_name)

        usage_file = tmp_path / f"{skill_name}.usage.json"
        assert usage_file.exists()

        data = json.loads(usage_file.read_text())
        assert data["use_count"] == 1
        assert data["last_used_at"] is not None


def test_bump_use_multiple_calls(tmp_path):
    """Test multiple bump_use calls accumulate correctly"""
    with patch("app.config.settings", type("Settings", (), {
        "skills_cache_path": str(tmp_path)
    })()):
        skill_name = "test-skill-2"
        bump_use(skill_name)
        bump_use(skill_name)
        bump_use(skill_name)

        usage_file = tmp_path / f"{skill_name}.usage.json"
        data = json.loads(usage_file.read_text())
        assert data["use_count"] == 3


@pytest.mark.asyncio
async def test_curator_returns_active_for_recent_skill(tmp_path):
    """Test curator returns 'active' for recently used skills"""
    from app.domain.skill import Skill, SkillStatus
    from app.domain.base import EntityId

    mock_storage = MagicMock()
    mock_storage.get_skill = AsyncMock(return_value=Skill(
        id=EntityId.generate(),
        name="recent-skill",
        description="Test",
        path="",
        status=SkillStatus.TRAINED,
        feedback_count=0,
        version=1,
        metadata={},
        user_id=EntityId("user-1"),
    ))

    # Create a recently used usage file
    with patch("app.config.settings", type("Settings", (), {
        "skills_cache_path": str(tmp_path)
    })()):
        usage_file = tmp_path / "recent-skill.usage.json"
        usage_file.write_text(json.dumps({
            "use_count": 5,
            "last_used_at": datetime.now(timezone.utc).isoformat()
        }))

        curator = SkillCurator(storage=mock_storage)
        result = await curator.check_and_curate("recent-skill-id")

        assert result == "active"


@pytest.mark.asyncio
async def test_curator_returns_not_found_for_missing_skill(tmp_path):
    """Test curator returns 'not_found' for non-existent skills"""
    mock_storage = MagicMock()
    mock_storage.get_skill = AsyncMock(return_value=None)

    curator = SkillCurator(storage=mock_storage)
    result = await curator.check_and_curate("nonexistent-id")

    assert result == "not_found"