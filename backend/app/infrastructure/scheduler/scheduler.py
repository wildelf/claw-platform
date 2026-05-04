"""APScheduler integration for task scheduling."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

if TYPE_CHECKING:
    from app.domain.scheduled_task import ScheduledTask

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


def setup_scheduler(storage, runner_factory):
    """Setup scheduler with storage and runner factory.

    Args:
        storage: Storage adapter instance
        runner_factory: Callable that creates DeepAgentsRunner for an agent
    """
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

    def job_executed(event):
        """Called after job execution."""
        if event.exception:
            logger.error(f"Scheduled job {event.job_id} failed: {event.exception}")
            asyncio.create_task(update_task_error(event.job_id, str(event.exception)))

    def job_error(event):
        """Called when job raises an exception."""
        logger.error(f"Scheduled job {event.job_id} error: {event.exception}")

    scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_error, EVENT_JOB_ERROR)

    # Load all active scheduled tasks from storage
    asyncio.create_task(load_active_tasks(storage, runner_factory))

    scheduler.start()


async def load_active_tasks(storage, runner_factory):
    """Load and schedule all active tasks from storage."""
    from app.domain.scheduled_task import ScheduledTaskStatus

    tasks = await storage.list_scheduled_tasks(user_id=None)
    for task in tasks:
        if task.status == ScheduledTaskStatus.ACTIVE:
            schedule_task(task, storage, runner_factory)


def schedule_task(task: "ScheduledTask", storage, runner_factory):
    """Schedule a single task."""
    from app.domain.scheduled_task import ScheduleType

    job_id = task.id

    if task.schedule_type == ScheduleType.CRON and task.cron_expression:
        trigger = CronTrigger.from_crontab(task.cron_expression)
    elif task.schedule_type == ScheduleType.INTERVAL and task.interval_seconds:
        trigger = IntervalTrigger(seconds=task.interval_seconds)
    elif task.schedule_type == ScheduleType.ONCE and task.run_at:
        trigger = DateTrigger(run_date=task.run_at)
    else:
        logger.error(f"Invalid schedule config for task {task.id}")
        return

    scheduler.add_job(
        run_scheduled_task,
        trigger=trigger,
        id=job_id,
        args=[task.id, storage, runner_factory],
        next_run_time=task.next_run_at,
        replace_existing=True,
    )
    logger.info(f"Scheduled task {task.name} ({task.id}) with {task.schedule_type}")


async def run_scheduled_task(task_id: str, storage, runner_factory):
    """Execute a scheduled task."""
    from app.domain.scheduled_task import ScheduledTaskStatus

    task = await storage.get_scheduled_task(task_id)
    if not task:
        logger.error(f"Scheduled task {task_id} not found")
        return

    logger.info(f"Running scheduled task: {task.name} ({task_id})")

    try:
        # Get agent
        agent = await storage.get_agent(task.agent_id)
        if not agent:
            raise ValueError(f"Agent {task.agent_id} not found")

        # Create runner and execute
        runner = runner_factory(agent, storage, task.model_config_id)
        await runner.create()

        async for event in runner.run(task.task_input):
            pass

        await runner.stop()

        # Update task status
        task.last_run_at = datetime.now(timezone.utc)
        task.run_count += 1
        task.last_error = None
        await storage.save_scheduled_task(task)

        logger.info(f"Scheduled task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Scheduled task {task_id} failed: {e}")
        task.last_error = str(e)
        await storage.save_scheduled_task(task)

        if task.schedule_type == ScheduleType.ONCE:
            task.status = ScheduledTaskStatus.FAILED
            await storage.save_scheduled_task(task)


async def update_task_error(task_id: str, error: str):
    """Update task error status."""
    task = await storage.get_scheduled_task(task_id)
    if task:
        task.last_error = error
        await storage.save_scheduled_task(task)


def trigger_now(task_id: str):
    """Trigger a task to run immediately."""
    if scheduler.get_job(task_id):
        scheduler.modify_job(task_id, next_run_time=datetime.now(timezone.utc))
    else:
        # Job not in scheduler - run it directly
        logger.warning(f"Task {task_id} not found in scheduler, running directly")