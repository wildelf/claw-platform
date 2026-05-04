"""Tests for ScheduledTask storage adapter."""

import pytest
from datetime import datetime, timezone

from app.domain.base import EntityId
from app.domain.scheduled_task import ScheduledTask, ScheduleType, ScheduledTaskStatus


@pytest.fixture
def sample_scheduled_task():
    """Create a sample scheduled task for testing."""
    return ScheduledTask(
        id=EntityId.generate(),
        name="test-scheduled-task",
        description="A test scheduled task",
        agent_id=EntityId.generate(),
        user_id=EntityId.generate(),
        schedule_type=ScheduleType.CRON,
        cron_expression="0 9 * * *",
        task_input='{"prompt": "test"}',
        status=ScheduledTaskStatus.ACTIVE,
    )


@pytest.fixture
def sample_scheduled_task_interval():
    """Create a sample scheduled task with interval schedule."""
    return ScheduledTask(
        id=EntityId.generate(),
        name="interval-task",
        description="An interval-based task",
        agent_id=EntityId.generate(),
        user_id=EntityId.generate(),
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=3600,
        task_input='{"action": "run"}',
        status=ScheduledTaskStatus.ACTIVE,
    )


@pytest.fixture
def sample_scheduled_task_once():
    """Create a sample scheduled task with one-time schedule."""
    run_at = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
    return ScheduledTask(
        id=EntityId.generate(),
        name="once-task",
        description="A one-time task",
        agent_id=EntityId.generate(),
        user_id=EntityId.generate(),
        schedule_type=ScheduleType.ONCE,
        run_at=run_at,
        task_input='{"action": "once"}',
        status=ScheduledTaskStatus.ACTIVE,
    )


class TestScheduledTaskAdapter:
    """Tests for ScheduledTask storage adapter."""

    @pytest.mark.asyncio
    async def test_save_scheduled_task(self, storage, sample_scheduled_task):
        """Saving a scheduled task should persist it."""
        await storage.save_scheduled_task(sample_scheduled_task)

        retrieved = await storage.get_scheduled_task(sample_scheduled_task.id)
        assert retrieved is not None
        assert retrieved.id == sample_scheduled_task.id
        assert retrieved.name == sample_scheduled_task.name
        assert retrieved.schedule_type == sample_scheduled_task.schedule_type
        assert retrieved.cron_expression == sample_scheduled_task.cron_expression

    @pytest.mark.asyncio
    async def test_save_and_update_scheduled_task(self, storage, sample_scheduled_task):
        """Updating a scheduled task should persist changes."""
        await storage.save_scheduled_task(sample_scheduled_task)

        sample_scheduled_task.name = "updated-name"
        sample_scheduled_task.status = ScheduledTaskStatus.PAUSED
        await storage.save_scheduled_task(sample_scheduled_task)

        retrieved = await storage.get_scheduled_task(sample_scheduled_task.id)
        assert retrieved.name == "updated-name"
        assert retrieved.status == ScheduledTaskStatus.PAUSED

    @pytest.mark.asyncio
    async def test_get_scheduled_task_not_found(self, storage):
        """Getting a non-existent scheduled task should return None."""
        result = await storage.get_scheduled_task("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_scheduled_tasks(self, storage, sample_scheduled_task, sample_scheduled_task_interval):
        """Listing scheduled tasks should return tasks for user."""
        user_id = sample_scheduled_task.user_id

        await storage.save_scheduled_task(sample_scheduled_task)
        await storage.save_scheduled_task(sample_scheduled_task_interval)

        tasks = await storage.list_scheduled_tasks(user_id)
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_list_scheduled_tasks_pagination(self, storage):
        """Listing scheduled tasks should support pagination."""
        user_id = EntityId.generate()

        # Create 5 tasks
        for i in range(5):
            task = ScheduledTask(
                id=EntityId.generate(),
                name=f"task-{i}",
                description=f"Task {i}",
                agent_id=EntityId.generate(),
                user_id=user_id,
                schedule_type=ScheduleType.INTERVAL,
                interval_seconds=60,
            )
            await storage.save_scheduled_task(task)

        # Test offset and limit
        tasks = await storage.list_scheduled_tasks(user_id, offset=0, limit=3)
        assert len(tasks) == 3

        tasks = await storage.list_scheduled_tasks(user_id, offset=3, limit=3)
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_list_scheduled_tasks_user_isolation(self, storage, sample_scheduled_task):
        """Listing scheduled tasks should only return tasks for specified user."""
        user_id = sample_scheduled_task.user_id
        other_user_id = EntityId.generate()

        await storage.save_scheduled_task(sample_scheduled_task)

        # Create task for other user
        other_task = ScheduledTask(
            id=EntityId.generate(),
            name="other-user-task",
            description="Task for other user",
            agent_id=EntityId.generate(),
            user_id=other_user_id,
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
        )
        await storage.save_scheduled_task(other_task)

        tasks = await storage.list_scheduled_tasks(user_id)
        assert len(tasks) == 1
        assert tasks[0].id == sample_scheduled_task.id

    @pytest.mark.asyncio
    async def test_delete_scheduled_task(self, storage, sample_scheduled_task):
        """Deleting a scheduled task should remove it."""
        await storage.save_scheduled_task(sample_scheduled_task)

        await storage.delete_scheduled_task(sample_scheduled_task.id)

        retrieved = await storage.get_scheduled_task(sample_scheduled_task.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_scheduled_task_not_found(self, storage):
        """Deleting a non-existent task should not raise error."""
        await storage.delete_scheduled_task("nonexistent-id")

    @pytest.mark.asyncio
    async def test_scheduled_task_all_fields(self, storage):
        """Test that all ScheduledTask fields are properly persisted."""
        now = datetime.now(timezone.utc)
        task = ScheduledTask(
            id=EntityId.generate(),
            name="full-fields-task",
            description="Task with all fields",
            agent_id=EntityId.generate(),
            user_id=EntityId.generate(),
            schedule_type=ScheduleType.CRON,
            cron_expression="0 9 * * *",
            interval_seconds=None,
            run_at=None,
            task_input='{"key": "value"}',
            model_config_id=EntityId.generate(),
            status=ScheduledTaskStatus.ACTIVE,
            last_run_at=now,
            next_run_at=now,
            run_count=5,
            last_error=None,
            created_at=now,
            updated_at=now,
        )

        await storage.save_scheduled_task(task)
        retrieved = await storage.get_scheduled_task(task.id)

        assert retrieved is not None
        assert retrieved.name == "full-fields-task"
        assert retrieved.description == "Task with all fields"
        assert retrieved.schedule_type == ScheduleType.CRON
        assert retrieved.cron_expression == "0 9 * * *"
        assert retrieved.task_input == '{"key": "value"}'
        assert retrieved.model_config_id == task.model_config_id
        assert retrieved.status == ScheduledTaskStatus.ACTIVE
        assert retrieved.run_count == 5
        assert retrieved.last_error is None

    @pytest.mark.asyncio
    async def test_scheduled_task_interval_type(self, storage, sample_scheduled_task_interval):
        """Test interval-based scheduled task storage."""
        await storage.save_scheduled_task(sample_scheduled_task_interval)

        retrieved = await storage.get_scheduled_task(sample_scheduled_task_interval.id)
        assert retrieved is not None
        assert retrieved.schedule_type == ScheduleType.INTERVAL
        assert retrieved.interval_seconds == 3600

    @pytest.mark.asyncio
    async def test_scheduled_task_once_type(self, storage, sample_scheduled_task_once):
        """Test one-time scheduled task storage."""
        await storage.save_scheduled_task(sample_scheduled_task_once)

        retrieved = await storage.get_scheduled_task(sample_scheduled_task_once.id)
        assert retrieved is not None
        assert retrieved.schedule_type == ScheduleType.ONCE
        assert retrieved.run_at is not None