"""Skill application service."""

from typing import List, Optional

from app.domain.skill import Skill, SkillFile
from app.infrastructure.storage.sqlite import SQLiteStorage


class SkillService:
    """Service for skill operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, skill: Skill) -> Skill:
        """Create a new skill."""
        await self.storage.save_skill(skill)
        return skill

    async def get(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID."""
        return await self.storage.get_skill(skill_id)

    async def list_by_user(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Skill]:
        """List skills for a user."""
        return await self.storage.list_skills(user_id, offset, limit)

    async def update(self, skill_id: str, data: dict) -> Optional[Skill]:
        """Update skill fields."""
        skill = await self.storage.get_skill(skill_id)
        if not skill:
            return None

        for key, value in data.items():
            if hasattr(skill, key):
                setattr(skill, key, value)

        await self.storage.save_skill(skill)
        return skill

    async def delete(self, skill_id: str) -> bool:
        """Delete a skill."""
        skill = await self.storage.get_skill(skill_id)
        if not skill:
            return False
        await self.storage.delete_skill(skill_id)
        return True

    async def get_file(self, skill_id: str, filename: str) -> Optional[bytes]:
        """Get skill file content."""
        return await self.storage.get_skill_file(skill_id, filename)

    async def list_files(self, skill_id: str) -> List[str]:
        """List skill files."""
        return await self.storage.list_skill_files(skill_id)

    async def save_file(self, skill_id: str, filename: str, content: bytes) -> None:
        """Save skill file."""
        await self.storage.save_skill_file(skill_id, filename, content)

    async def delete_file(self, skill_id: str, filename: str) -> None:
        """Delete skill file."""
        await self.storage.delete_skill_file(skill_id, filename)