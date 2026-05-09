"""Agent API routes."""

import asyncio
import json
import logging
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.deps import Storage, UserId
from app.application.agent_service import AgentService
from app.application.conversation_memory_service import ConversationMemoryService, summarize_conversation_task
from app.domain.agent import Agent
from app.domain.base import EntityId
from app.infrastructure.redis_client import get_agent_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


class CreateAgent(BaseModel):
    """Payload for creating an agent."""

    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=1000)
    role: str = Field(default="", max_length=500)
    goal: str = Field(default="", max_length=1000)
    backstory: str = Field(default="", max_length=2000)
    skill_ids: List[str] = Field(default_factory=list)
    tool_ids: List[str] = Field(default_factory=list)
    enabled_builtin_tools: List[str] = Field(default_factory=list)
    text_model_config_id: str | None = None
    image_model_config_id: str | None = None
    video_model_config_id: str | None = None


class UpdateAgent(BaseModel):
    """Payload for updating an agent."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    role: str | None = Field(default=None, max_length=500)
    goal: str | None = Field(default=None, max_length=1000)
    backstory: str | None = Field(default=None, max_length=2000)
    skill_ids: List[str] | None = None
    tool_ids: List[str] | None = None
    enabled_builtin_tools: List[str] | None = None
    text_model_config_id: str | None = None
    image_model_config_id: str | None = None
    video_model_config_id: str | None = None
    status: str | None = None


@router.post("", response_model=Agent)
async def create_agent(
    data: CreateAgent,
    storage: Storage,
    user_id: UserId,
) -> Agent:
    """Create a new agent."""
    agent = Agent(
        name=data.name,
        description=data.description,
        role=data.role,
        goal=data.goal,
        backstory=data.backstory,
        skill_ids=data.skill_ids,
        tool_ids=data.tool_ids,
        enabled_builtin_tools=data.enabled_builtin_tools,
        text_model_config_id=EntityId(data.text_model_config_id) if data.text_model_config_id else None,
        image_model_config_id=EntityId(data.image_model_config_id) if data.image_model_config_id else None,
        video_model_config_id=EntityId(data.video_model_config_id) if data.video_model_config_id else None,
        user_id=user_id,
    )
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
    data: UpdateAgent,
    storage: Storage,
) -> Agent:
    """Update agent."""
    service = AgentService(storage)
    agent = await service.update(agent_id, data.model_dump(exclude_unset=True))
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


class RunAgentRequest(BaseModel):
    """Payload for running an agent."""
    task: str
    images: list[str] = Field(default_factory=list, description="Base64 encoded images")
    model_config_id: str | None = Field(default=None, description="临时覆盖默认模型")
    session_id: str | None = Field(default=None, description="会话ID，用于多轮对话继续")


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    request: RunAgentRequest,
    storage: Storage,
):
    """Run agent task.

    Executes the agent using deepagents and streams results.
    """
    from app.deepagents.wrapper import DeepAgentsRunner

    service = AgentService(storage)
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Validate model_config_id if provided
    if request.model_config_id:
        config = await storage.get_model_config(request.model_config_id)
        if not config:
            raise HTTPException(status_code=400, detail="Model config not found")

    runner = DeepAgentsRunner(agent, storage, override_model_config_id=request.model_config_id)

    try:
        await runner.create()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def stream_events():
        registry = get_agent_registry()
        # Register this agent as running
        await registry.register_agent(agent_id)

        task = request.task

        # Determine model name for start event
        model_name = "unknown"
        if request.model_config_id:
            model_config = await storage.get_model_config(request.model_config_id)
            if model_config:
                model_name = model_config.model
        elif agent.text_model_config_id:
            model_config = await storage.get_model_config(agent.text_model_config_id)
            if model_config:
                model_name = model_config.model

        async def run_with_cancel_check(runner, task, images):
            """Run agent with periodic cancel check."""
            results = []
            async for event in runner.run(task, images=images):
                if await registry.check_cancel_requested(agent_id):
                    break
                results.append(event)
            return results

        try:
            yield f"data: {json.dumps({'type': 'start', 'task': task, 'model': model_name, 'session_id': request.session_id})}\n\n"
            accumulated_output = ""
            for event in await run_with_cancel_check(runner, task, request.images):
                # Handle the new event dict format
                event_type = event.get("type", "content")
                if event_type == "content":
                    content = event.get("content", "")
                    # Remove thinking tags
                    content = content.replace("<think>", "").replace("</think>", "")
                    if content.strip():
                        accumulated_output += content
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                else:
                    # Forward other event types as-is
                    try:
                        yield f"data: {json.dumps(event)}\n\n"
                    except (TypeError, ValueError):
                        # Skip non-serializable events like Overwrite objects
                        pass
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # Create memory and trigger async summarization after streaming completes
            memory_service = ConversationMemoryService(storage)
            memory = await memory_service.create_memory(
                agent_id=agent_id,
                session_id=request.session_id or "",
                user_input=request.task,
                agent_output=accumulated_output,
            )
            if request.session_id:
                asyncio.create_task(
                    summarize_conversation_task(
                        memory_id=memory.id,
                        user_input=request.task,
                        agent_output=accumulated_output,
                        storage=storage,
                    )
                )
        except asyncio.CancelledError:
            yield f"data: {json.dumps({'type': 'cancelled'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            await registry.unregister_agent(agent_id)
            await registry.clear_cancel_flag(agent_id)
            await runner.stop()

    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
        },
    )


@router.post("/{agent_id}/run-with-feedback")
async def run_agent_with_feedback(
    agent_id: str,
    request: RunAgentRequest,
    storage: Storage,
):
    """Run agent and submit feedback when task completes.

    This is a convenience endpoint that runs the agent and
    returns immediately. Feedback should be submitted separately
    via POST /api/feedback after reviewing the results.
    """
    from app.deepagents.wrapper import DeepAgentsRunner

    service = AgentService(storage)
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Validate model_config_id if provided
    if request.model_config_id:
        config = await storage.get_model_config(request.model_config_id)
        if not config:
            raise HTTPException(status_code=400, detail="Model config not found")

    runner = DeepAgentsRunner(agent, storage, override_model_config_id=request.model_config_id)
    try:
        await runner.create()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def stream_events():
        registry = get_agent_registry()
        # Register this agent as running
        await registry.register_agent(agent_id)

        task = request.task

        # Determine model name for start event
        model_name = "unknown"
        if request.model_config_id:
            model_config = await storage.get_model_config(request.model_config_id)
            if model_config:
                model_name = model_config.model
        elif agent.text_model_config_id:
            model_config = await storage.get_model_config(agent.text_model_config_id)
            if model_config:
                model_name = model_config.model

        async def run_with_cancel_check(runner, task, images):
            """Run agent with periodic cancel check."""
            results = []
            async for event in runner.run(task, images=images):
                if await registry.check_cancel_requested(agent_id):
                    break
                results.append(event)
            return results

        try:
            yield f"data: {json.dumps({'type': 'start', 'task': task, 'model': model_name})}\n\n"
            for event in await run_with_cancel_check(runner, task, request.images):
                # Handle the new event dict format
                event_type = event.get("type", "content")
                if event_type == "content":
                    content = event.get("content", "")
                    # Remove thinking tags
                    content = content.replace("<think>", "").replace("</think>", "")
                    if content.strip():
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                else:
                    # Forward other event types as-is
                    try:
                        yield f"data: {json.dumps(event)}\n\n"
                    except (TypeError, ValueError):
                        # Skip non-serializable events like Overwrite objects
                        pass
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except asyncio.CancelledError:
            yield f"data: {json.dumps({'type': 'cancelled'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            await registry.unregister_agent(agent_id)
            await registry.clear_cancel_flag(agent_id)
            await runner.stop()

    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
        },
    )


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
) -> dict:
    """Stop a running agent task.

    Signals the running task to cancel. The task running on any node
    will check the cancel flag and raise CancelledError.
    The streaming response will receive a 'cancelled' event.
    """
    registry = get_agent_registry()
    if await registry.request_agent_cancel(agent_id):
        return {"status": "stopped", "agent_id": agent_id}
    return {"status": "not_running", "agent_id": agent_id}