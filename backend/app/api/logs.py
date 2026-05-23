"""Log API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import Storage, UserId
from app.application.agent_service import AgentService
from app.application.log_service import LogService
from app.domain.log import LogEntry, LogActionType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


class LogEntryResponse(BaseModel):
    id: str
    agent_id: str
    session_id: str
    timestamp: str
    action_type: str
    tool_name: str | None
    input_json: str | None
    output_json: str | None
    decision_context: str | None
    error: str | None

    @classmethod
    def from_entry(cls, entry: LogEntry) -> "LogEntryResponse":
        return cls(
            id=entry.id,
            agent_id=entry.agent_id,
            session_id=entry.session_id,
            timestamp=entry.timestamp.isoformat(),
            action_type=entry.action_type,
            tool_name=entry.tool_name,
            input_json=entry.input_json,
            output_json=entry.output_json,
            decision_context=entry.decision_context,
            error=entry.error,
        )


@router.get("", response_model=List[LogEntryResponse])
async def query_logs(
    storage: Storage,
    user_id: UserId,
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    tool_name: Optional[str] = Query(None, description="Filter by tool name"),
    offset: int = 0,
    limit: int = 100,
) -> List[LogEntryResponse]:
    """Query log entries with optional filters. IT uses this for audit/debugging."""
    service = LogService(storage)
    agent_service = AgentService(storage)

    # If agent_id filter is provided, verify ownership first
    if agent_id:
        agent = await agent_service.get(agent_id)
        if not agent or agent.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access logs for this agent")

    entries = await service.query(
        agent_id=agent_id,
        session_id=session_id,
        action_type=action_type,
        tool_name=tool_name,
        offset=offset,
        limit=limit,
    )

    # If no agent_id filter, verify each entry's agent ownership
    if not agent_id:
        user_agent_ids = set()
        filtered = []
        for entry in entries:
            if entry.agent_id not in user_agent_ids:
                agent = await agent_service.get(entry.agent_id)
                if agent and agent.user_id == user_id:
                    user_agent_ids.add(entry.agent_id)
            if entry.agent_id in user_agent_ids:
                filtered.append(entry)
        entries = filtered

    return [LogEntryResponse.from_entry(e) for e in entries]


@router.post("", response_model=LogEntryResponse)
async def create_log(
    storage: Storage,
    user_id: UserId,
    agent_id: str,
    session_id: str,
    action_type: str,
    tool_name: str | None = None,
    input_json: str | None = None,
    output_json: str | None = None,
    decision_context: str | None = None,
    error: str | None = None,
) -> LogEntryResponse:
    """Write a log entry. Used by agent runtime to emit events."""
    agent_service = AgentService(storage)
    agent = await agent_service.get(agent_id)
    if not agent or agent.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to create logs for this agent")
    service = LogService(storage)
    entry = await service.emit(
        agent_id=agent_id,
        session_id=session_id,
        action_type=LogActionType(action_type),
        tool_name=tool_name,
        input_json=input_json,
        output_json=output_json,
        decision_context=decision_context,
        error=error,
    )
    return LogEntryResponse.from_entry(entry)
