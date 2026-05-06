"""Session service for business logic operations."""

from typing import List, Optional
from datetime import datetime, timezone

from app.domain.session import Session
from app.infrastructure.storage.base import StorageAdapter


class SessionService:
    """Application service for session operations."""

    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    async def create_session(self, agent_id: str, name: Optional[str] = None) -> Session:
        """Create a new session."""
        session = Session.create(agent_id=agent_id, name=name)
        await self.storage.save_session(session)
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return await self.storage.get_session(session_id)

    async def list_sessions(self, offset: int = 0, limit: int = 100) -> List[Session]:
        """List sessions with pagination."""
        return await self.storage.list_sessions(offset=offset, limit=limit)

    async def update_session(self, session_id: str, name: str) -> Optional[Session]:
        """Update a session's name."""
        session = await self.storage.get_session(session_id)
        if not session:
            return None
        session.name = name
        session.updated_at = datetime.now(timezone.utc)
        await self.storage.save_session(session)
        return session

    async def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        await self.storage.delete_session(session_id)

    async def increment_message_count(self, session_id: str) -> None:
        """Increment the message count for a session."""
        session = await self.storage.get_session(session_id)
        if session:
            session.message_count += 1
            session.updated_at = datetime.now(timezone.utc)
            await self.storage.save_session(session)
