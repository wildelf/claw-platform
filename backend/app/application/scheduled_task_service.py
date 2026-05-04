"""Scheduled Task Service."""

from datetime import datetime, timezone
from typing import List, Optional

from app.domain.scheduled_task import ScheduledTask, ScheduledTaskStatus, ScheduleType
from app.domain.base import EntityId


class ScheduledTaskService:
    """Service for managing scheduled tasks."""

    def __init__(self, storage):
        self.storage = storage

    async def create(self, task: ScheduledTask) -> ScheduledTask:
        """Create a new scheduled task."""
        if task.status == ScheduledTaskStatus.ACTIVE:
            task.next_run_at = self._calculate_next_run(task)

        await self.storage.save_scheduled_task(task)

        from app.infrastructure.scheduler.scheduler import scheduler, schedule_task
        if task.status == ScheduledTaskStatus.ACTIVE:
            schedule_task(task, self.storage, None)

        return task

    async def get(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a scheduled task by ID."""
        return await self.storage.get_scheduled_task(task_id)

    async def list_by_user(
        self, user_id: EntityId, offset: int = 0, limit: int = 100
    ) -> List[ScheduledTask]:
        """List scheduled tasks for a user."""
        return await self.storage.list_scheduled_tasks(user_id, offset, limit)

    async def update(self, task_id: str, data: dict) -> Optional[ScheduledTask]:
        """Update a scheduled task."""
        task = await self.storage.get_scheduled_task(task_id)
        if not task:
            return None

        for key, value in data.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)

        if any(k in data for k in ['schedule_type', 'cron_expression', 'interval_seconds', 'run_at']):
            task.next_run_at = self._calculate_next_run(task)

        await self.storage.save_scheduled_task(task)

        from app.infrastructure.scheduler.scheduler import scheduler, schedule_task
        if scheduler.get_job(task_id):
            scheduler.remove_job(task_id)

        if task.status == ScheduledTaskStatus.ACTIVE:
            schedule_task(task, self.storage, None)

        return task

    async def delete(self, task_id: str) -> bool:
        """Delete a scheduled task."""
        task = await self.storage.get_scheduled_task(task_id)
        if not task:
            return False

        from app.infrastructure.scheduler.scheduler import scheduler
        if scheduler.get_job(task_id):
            scheduler.remove_job(task_id)

        await self.storage.delete_scheduled_task(task_id)
        return True

    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate next run time based on schedule type."""
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.date import DateTrigger

        try:
            if task.schedule_type == ScheduleType.CRON and task.cron_expression:
                trigger = CronTrigger.from_crontab(task.cron_expression)
                return trigger.get_next_fire_time(None, None)
            elif task.schedule_type == ScheduleType.INTERVAL and task.interval_seconds:
                trigger = IntervalTrigger(seconds=task.interval_seconds)
                return trigger.get_next_fire_time(None, None)
            elif task.schedule_type == ScheduleType.ONCE and task.run_at:
                return task.run_at
        except Exception:
            return None
        return None