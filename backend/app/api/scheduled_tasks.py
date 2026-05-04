"""Scheduled Task API routes."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import Storage, UserId
from app.domain.base import EntityId
from app.domain.scheduled_task import ScheduledTask, ScheduleType, ScheduledTaskStatus

router = APIRouter(prefix="/scheduled-tasks", tags=["scheduled_tasks"])


class CreateScheduledTask(BaseModel):
    name: str = Field(max_length=100)
    description: str = Field(max_length=500, default="")
    agent_id: str
    schedule_type: ScheduleType
    cron_expression: str | None = None
    interval_seconds: int | None = None
    run_at: datetime | None = None
    task_input: str = Field(max_length=5000, default="")
    model_config_id: str | None = None


class UpdateScheduledTask(BaseModel):
    name: str | None = None
    description: str | None = None
    schedule_type: ScheduleType | None = None
    cron_expression: str | None = None
    interval_seconds: int | None = None
    run_at: datetime | None = None
    task_input: str | None = None
    model_config_id: str | None = None
    status: ScheduledTaskStatus | None = None


@router.post("", response_model=ScheduledTask)
async def create_scheduled_task(
    data: CreateScheduledTask,
    storage: Storage,
    user_id: UserId,
) -> ScheduledTask:
    """Create a new scheduled task."""
    # Import here to avoid circular imports - service created in Task 4
    from app.application.scheduled_task_service import ScheduledTaskService

    task = ScheduledTask(
        name=data.name,
        description=data.description,
        agent_id=EntityId(data.agent_id),
        user_id=user_id,
        schedule_type=data.schedule_type,
        cron_expression=data.cron_expression,
        interval_seconds=data.interval_seconds,
        run_at=data.run_at,
        task_input=data.task_input,
        model_config_id=EntityId(data.model_config_id) if data.model_config_id else None,
    )
    service = ScheduledTaskService(storage)
    return await service.create(task)


@router.get("", response_model=List[ScheduledTask])
async def list_scheduled_tasks(
    storage: Storage,
    user_id: UserId,
    offset: int = 0,
    limit: int = 100,
) -> List[ScheduledTask]:
    """List scheduled tasks for current user."""
    from app.application.scheduled_task_service import ScheduledTaskService

    service = ScheduledTaskService(storage)
    return await service.list_by_user(user_id, offset, limit)


@router.get("/{task_id}", response_model=ScheduledTask)
async def get_scheduled_task(
    task_id: str,
    storage: Storage,
    user_id: UserId,
) -> ScheduledTask:
    """Get scheduled task by ID."""
    from app.application.scheduled_task_service import ScheduledTaskService

    service = ScheduledTaskService(storage)
    task = await service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    return task


@router.put("/{task_id}", response_model=ScheduledTask)
async def update_scheduled_task(
    task_id: str,
    data: UpdateScheduledTask,
    storage: Storage,
    user_id: UserId,
) -> ScheduledTask:
    """Update scheduled task."""
    from app.application.scheduled_task_service import ScheduledTaskService

    service = ScheduledTaskService(storage)
    task = await service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    updated = await service.update(task_id, data.model_dump(exclude_unset=True))
    return updated


@router.delete("/{task_id}")
async def delete_scheduled_task(
    task_id: str,
    storage: Storage,
    user_id: UserId,
) -> dict:
    """Delete scheduled task."""
    from app.application.scheduled_task_service import ScheduledTaskService

    service = ScheduledTaskService(storage)
    task = await service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    deleted = await service.delete(task_id)
    return {"ok": True}


@router.post("/{task_id}/trigger")
async def trigger_scheduled_task(
    task_id: str,
    storage: Storage,
    user_id: UserId,
) -> dict:
    """Immediately trigger a scheduled task."""
    from app.application.scheduled_task_service import ScheduledTaskService

    service = ScheduledTaskService(storage)
    task = await service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")

    # Scheduler will be integrated in Task 4 - for now just return success
    return {"status": "triggered", "task_id": task_id}