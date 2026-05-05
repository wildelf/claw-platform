"""LogService for centralized logging."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from app.domain.base import EntityId
from app.domain.log import LogActionType, LogEntry
from app.infrastructure.storage.base import StorageAdapter

logger = logging.getLogger(__name__)


class LogService:
    """Service for writing and querying centralized logs."""

    def __init__(self, storage: StorageAdapter):
        self._storage = storage

    async def write(self, entry: LogEntry) -> None:
        """Write a log entry. Retries 3x on DB failure, then falls back to file."""
        import json
        import asyncio
        from pathlib import Path

        fallback_path = Path("logs/fallback.log")
        max_retries = 3

        for attempt in range(max_retries):
            try:
                await self._storage.save_log(entry)
                return
            except Exception as e:
                logger.warning(f"Log write attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    # Final fallback: write to file
                    fallback_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(fallback_path, "a") as f:
                        f.write(json.dumps({
                            "id": entry.id,
                            "agent_id": entry.agent_id,
                            "session_id": entry.session_id,
                            "timestamp": entry.timestamp.isoformat(),
                            "action_type": entry.action_type,
                            "tool_name": entry.tool_name,
                            "input_json": entry.input_json,
                            "output_json": entry.output_json,
                            "decision_context": entry.decision_context,
                            "error": entry.error,
                        }) + "\n")
                    logger.error(f"Log write failed after {max_retries} attempts, wrote to fallback file: {fallback_path}")
                else:
                    await asyncio.sleep(0.1 * (attempt + 1))  # brief backoff

    async def query(
        self,
        agent_id: str | None = None,
        session_id: str | None = None,
        action_type: str | None = None,
        tool_name: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[LogEntry]:
        """Query log entries with filters."""
        return await self._storage.query_logs(
            agent_id=agent_id,
            session_id=session_id,
            action_type=action_type,
            tool_name=tool_name,
            offset=offset,
            limit=limit,
        )

    async def emit(
        self,
        agent_id: str,
        session_id: str,
        action_type: LogActionType,
        tool_name: str | None = None,
        input_json: str | None = None,
        output_json: str | None = None,
        decision_context: str | None = None,
        error: str | None = None,
        extra: dict | None = None,
    ) -> LogEntry:
        """Convenience method to create and write a log entry."""
        entry = LogEntry(
            agent_id=EntityId(agent_id),
            session_id=session_id,
            action_type=action_type,
            tool_name=tool_name,
            input_json=input_json,
            output_json=output_json,
            decision_context=decision_context,
            error=error,
            extra=extra or {},
        )
        await self.write(entry)
        return entry
