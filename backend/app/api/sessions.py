"""Session API routes."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.api.deps import Storage
from app.application.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionResponse(BaseModel):
    id: str
    name: str
    agent_id: str
    created_at: str
    updated_at: str
    message_count: int

    @classmethod
    def from_session(cls, session) -> "SessionResponse":
        return cls(
            id=session.id,
            name=session.name,
            agent_id=session.agent_id,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=session.message_count,
        )


class CreateSessionRequest(BaseModel):
    agent_id: str
    name: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    name: str


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    storage: Storage,
    offset: int = 0,
    limit: int = 100,
) -> List[SessionResponse]:
    """List all sessions, ordered by updated_at desc."""
    service = SessionService(storage)
    sessions = await service.list_sessions(offset=offset, limit=limit)
    return [SessionResponse.from_session(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    storage: Storage,
) -> SessionResponse:
    """Get a single session by ID."""
    service = SessionService(storage)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.from_session(session)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    storage: Storage,
) -> SessionResponse:
    """Create a new session."""
    service = SessionService(storage)
    session = await service.create_session(agent_id=request.agent_id, name=request.name)
    return SessionResponse.from_session(session)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    storage: Storage,
) -> SessionResponse:
    """Update session name."""
    service = SessionService(storage)
    session = await service.update_session(session_id, name=request.name)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.from_session(session)


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    storage: Storage,
) -> dict:
    """Delete a session."""
    service = SessionService(storage)
    await service.delete_session(session_id)
    return {"ok": True}