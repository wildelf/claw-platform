"""Agent API routes."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage, UserId
from app.application.agent_service import AgentService
from app.domain.agent import Agent, AgentStatus

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=Agent)
async def create_agent(
    agent: Agent,
    storage: Storage,
    user_id: UserId,
) -> Agent:
    """Create a new agent."""
    agent.user_id = user_id
    service = AgentService(storage)
    return await service.create(agent)


@router.get("", response_model=List[Agent])
async def list_agents(
    storage: Storage,
    user_id: UserId,
    offset: int = 0,
    limit: int = 100,
) -> List[Agent]:
    """List agents for current user."""
    service = AgentService(storage)
    return await service.list_by_user(user_id, offset, limit)


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    storage: Storage,
) -> Agent:
    """Get agent by ID."""
    service = AgentService(storage)
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    data: dict,
    storage: Storage,
) -> Agent:
    """Update agent."""
    service = AgentService(storage)
    agent = await service.update(agent_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    storage: Storage,
) -> dict:
    """Delete agent."""
    service = AgentService(storage)
    deleted = await service.delete(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"ok": True}


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    task: str,
    storage: Storage,
) -> dict:
    """Run agent task.

    TODO: Implement actual agent execution via deepagents.
    """
    service = AgentService(storage)
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # TODO: Integrate with deepagents
    return {"status": "todo", "message": "Agent execution not yet implemented"}


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    storage: Storage,
) -> dict:
    """Stop running agent."""
    # TODO: Implement agent stop
    return {"status": "todo", "message": "Agent stop not yet implemented"}