from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domain.base import EntityId


@dataclass
class Session:
    id: EntityId
    name: str
    agent_id: EntityId
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    @staticmethod
    def create(agent_id: str, name: Optional[str] = None) -> "Session":
        now = datetime.now(timezone.utc)
        return Session(
            id=EntityId.generate(),
            name=name or "",
            agent_id=EntityId(agent_id),
            created_at=now,
            updated_at=now,
            message_count=0,
        )