"""Conversation Memory Service."""
import asyncio
import logging
from typing import List, Optional

from app.config import settings
from app.domain.conversation_memory import ConversationMemory
from app.infrastructure.storage.base import StorageAdapter

logger = logging.getLogger(__name__)


async def summarize_conversation_task(memory_id: str, user_input: str, agent_output: str, storage: StorageAdapter):
    """Background task to generate summary using LLM."""
    try:
        # Build prompt for summarization
        prompt = f"""请用500字以内总结以下对话的核心内容。

用户输入: {user_input}

助手回复: {agent_output}

摘要:"""

        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model=settings.models.default.model,
            api_key=settings.models.default.api_key,
            base_url=settings.models.default.base_url,
        )

        response = await model.ainvoke(prompt)
        summary = response.content.strip()

        # Update the memory with summary
        await storage.update_conversation_memory_summary(memory_id, summary)
        logger.info(f"Summary generated for memory {memory_id}: {summary[:100]}...")
    except Exception as e:
        logger.error(f"Failed to generate summary for memory {memory_id}: {e}")
        # Don't re-raise - summary failure should not affect main flow


class ConversationMemoryService:
    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    async def get_memory_by_id(self, memory_id: str) -> Optional[ConversationMemory]:
        return await self.storage.get_conversation_memory(memory_id)

    async def get_memories(self, agent_id: str, session_id: str, limit: int = 10) -> List[ConversationMemory]:
        return await self.storage.get_conversation_memories(agent_id, session_id, limit=limit)

    async def create_memory(
        self, agent_id: str, session_id: str, user_input: str, agent_output: str
    ) -> ConversationMemory:
        memory = ConversationMemory.create(
            agent_id=agent_id,
            session_id=session_id,
            user_input=user_input,
            agent_output=agent_output,
            summary="",
        )
        await self.storage.save_conversation_memory(memory)
        return memory

    async def update_summary(self, memory_id: str, summary: str) -> Optional[ConversationMemory]:
        await self.storage.update_conversation_memory_summary(memory_id, summary)
        return None

    async def delete_memory(self, memory_id: str) -> None:
        await self.storage.delete_conversation_memory(memory_id)

    async def delete_memories_by_agent(self, agent_id: str) -> None:
        await self.storage.delete_conversation_memories_by_agent(agent_id)

    async def delete_memories_by_session(self, agent_id: str, session_id: str) -> None:
        await self.storage.delete_conversation_memories_by_session(agent_id, session_id)
