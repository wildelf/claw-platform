import pytest
from datetime import datetime, timezone
from app.domain.base import EntityId
from app.domain.scheduled_task import ScheduledTask, ScheduleType, ScheduledTaskStatus

def test_scheduled_task_creation():
    task = ScheduledTask(
        name="Daily Report",
        agent_id=EntityId("agent-123"),
        user_id=EntityId("user-456"),
        schedule_type=ScheduleType.CRON,
        cron_expression="0 9 * * *",
        task_input="生成日报",
        status=ScheduledTaskStatus.ACTIVE
    )
    assert task.name == "Daily Report"
    assert task.schedule_type == ScheduleType.CRON
    assert task.cron_expression == "0 9 * * *"

def test_schedule_type_enum():
    assert ScheduleType.ONCE.value == "once"
    assert ScheduleType.CRON.value == "cron"
    assert ScheduleType.INTERVAL.value == "interval"

def test_status_enum():
    assert ScheduledTaskStatus.ACTIVE.value == "active"
    assert ScheduledTaskStatus.PAUSED.value == "paused"
    assert ScheduledTaskStatus.COMPLETED.value == "completed"
    assert ScheduledTaskStatus.FAILED.value == "failed"