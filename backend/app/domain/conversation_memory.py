from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domain.base import EntityId


@dataclass
class ConversationMemory:
    id: EntityId
    agent_id: EntityId
    session_id: str  # 用于会话隔离
    user_input: str
    agent_output: str
    summary: str
    created_at: datetime

    @staticmethod
    def create(agent_id: str, session_id: str, user_input: str, agent_output: str, summary: str = "") -> "ConversationMemory":
        return ConversationMemory(
            id=EntityId.generate(),
            agent_id=EntityId(agent_id),
            session_id=session_id,
            user_input=user_input,
            agent_output=agent_output,
            summary=summary,
            created_at=datetime.now(timezone.utc),
        )