"""User domain entity."""

from enum import Enum

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseEntity):
    """User entity."""

    username: str = Field(max_length=50)
    email: str = Field(max_length=255)
    password_hash: str = Field(max_length=255)
    role: UserRole = UserRole.USER
    is_active: bool = True

    class Config:
        use_enum_values = True