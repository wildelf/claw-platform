"""Conversation Memory API routes."""
import logging
from typing import List

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.api.deps import Storage
from app.application.conversation_memory_service import ConversationMemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversation-memories", tags=["conversation-memories"])


class ConversationMemoryResponse(BaseModel):
    id: str
    agent_id: str
    user_input: str
    agent_output: str
    summary: str
    created_at: str

    @classmethod
    def from_memory(cls, memory) -> "ConversationMemoryResponse":
        return cls(
            id=memory.id,
            agent_id=memory.agent_id,
            user_input=memory.user_input,
            agent_output=memory.agent_output,
            summary=memory.summary,
            created_at=memory.created_at.isoformat(),
        )


class CreateConversationMemoryRequest(BaseModel):
    agent_id: str
    user_input: str
    agent_output: str
    session_id: str | None = None


class UpdateSummaryRequest(BaseModel):
    summary: str


@router.get("", response_model=List[ConversationMemoryResponse])
async def list_memories(
    storage: Storage,
    agent_id: str = Query(...),
    limit: int = Query(default=10, le=20),
) -> List[ConversationMemoryResponse]:
    """Get conversation memories for an agent, ordered by created_at desc."""
    service = ConversationMemoryService(storage)
    memories = await service.get_memories(agent_id, limit=limit)
    return [ConversationMemoryResponse.from_memory(m) for m in memories]


@router.post("", response_model=ConversationMemoryResponse, status_code=201)
async def create_memory(
    request: CreateConversationMemoryRequest,
    storage: Storage,
) -> ConversationMemoryResponse:
    """Create a new conversation memory."""
    service = ConversationMemoryService(storage)
    memory = await service.create_memory(
        agent_id=request.agent_id,
        user_input=request.user_input,
        agent_output=request.agent_output,
    )
    return ConversationMemoryResponse.from_memory(memory)


@router.patch("/{memory_id}/summary", response_model=ConversationMemoryResponse)
async def update_summary(
    memory_id: str,
    request: UpdateSummaryRequest,
    storage: Storage,
) -> ConversationMemoryResponse:
    """Update the summary of a conversation memory."""
    service = ConversationMemoryService(storage)
    memory = await service.update_summary(memory_id, request.summary)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return ConversationMemoryResponse.from_memory(memory)


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    storage: Storage,
) -> dict:
    """Delete a single conversation memory."""
    service = ConversationMemoryService(storage)
    await service.delete_memory(memory_id)
    return {"ok": True}


@router.delete("")
async def delete_memories_by_agent(
    storage: Storage,
    agent_id: str = Query(...),
) -> dict:
    """Delete all conversation memories for an agent."""
    service = ConversationMemoryService(storage)
    await service.delete_memories_by_agent(agent_id)
    return {"ok": True}