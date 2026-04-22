"""Dependency injection for API routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.base import EntityId
from app.domain.user import User, UserRole
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.application.skill_service import SkillService


# Global storage instance
_storage: SQLiteStorage | None = None


async def get_storage() -> SQLiteStorage:
    """Get storage instance."""
    global _storage
    if _storage is None:
        _storage = SQLiteStorage(settings.storage.sqlite.path)
        await _storage.init_db()
    return _storage


# Type alias for dependency injection
Storage = Annotated[SQLiteStorage, Depends(get_storage)]


async def get_skill_service(storage: Storage) -> SkillService:
    """Get skill service instance."""
    return SkillService(storage)


SkillServiceDep = Annotated[SkillService, Depends(get_skill_service)]


async def get_current_user_id() -> EntityId:
    """Get current user ID from auth context.

    TODO: Implement actual auth (JWT/OAuth2).
    For now, returns a default user ID for development.
    """
    # TODO: Extract from JWT token
    return EntityId("dev-user-id")


UserId = Annotated[EntityId, Depends(get_current_user_id)]