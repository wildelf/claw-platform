"""Dependency injection for API routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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


security = HTTPBearer()


class AuthContext:
    """Auth context containing the current user."""
    def __init__(self, user_id: EntityId, username: str, role: str):
        self.user_id = user_id
        self.username = username
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthContext:
    """Extract and validate JWT token, returning auth context.

    Depends on HTTPBearer to extract the token from Authorization header.
    """
    from app.application.auth_service import AuthService

    token = credentials.credentials
    auth_service = AuthService()
    payload = auth_service.verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")

    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthContext(
        user_id=EntityId(user_id),
        username=username,
        role=role,
    )


async def get_current_user_id_from_auth(
    auth: AuthContext = Depends(get_current_user),
) -> EntityId:
    """Get current user ID from auth context."""
    return auth.user_id


UserId = Annotated[EntityId, Depends(get_current_user_id_from_auth)]