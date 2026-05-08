"""Conversation Memory Service."""
from typing import List, Optional

from app.domain.conversation_memory import ConversationMemory
from app.infrastructure.storage.base import StorageAdapter


class ConversationMemoryService:
    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    async def get_memories(self, agent_id: str, limit: int = 10) -> List[ConversationMemory]:
        return await self.storage.get_conversation_memories(agent_id, limit=limit)

    async def create_memory(
        self, agent_id: str, user_input: str, agent_output: str
    ) -> ConversationMemory:
        memory = ConversationMemory.create(
            agent_id=agent_id,
            user_input=user_input,
            agent_output=agent_output,
            summary="",
        )
        await self.storage.save_conversation_memory(memory)
        return memory

    async def update_summary(self, memory_id: str, summary: str) -> Optional[ConversationMemory]:
        await self.storage.update_conversation_memory_summary(memory_id, summary)
        return None  # Simplified - caller doesn't need the object back for this use case

    async def delete_memory(self, memory_id: str) -> None:
        await self.storage.delete_conversation_memory(memory_id)

    async def delete_memories_by_agent(self, agent_id: str) -> None:
        await self.storage.delete_conversation_memories_by_agent(agent_id)