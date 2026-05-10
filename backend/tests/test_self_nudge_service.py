import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.self_nudge_service import SelfNudgeService, NudgeResult
from app.application.memory.memory_persistence import MemoryPersistence, MemoryType


@pytest.fixture
def temp_mem_dir():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def service(temp_mem_dir):
    mock_storage = MagicMock()
    mock_storage.save_nudge_record = AsyncMock()
    memory_persistence = MemoryPersistence(base_dir=temp_mem_dir)
    return SelfNudgeService(storage=mock_storage, memory_persistence=memory_persistence)


@pytest.mark.asyncio
async def test_process_triggers_nudge(service):
    # Mock LLM decision
    mock_decision = MagicMock()
    mock_decision.should_nudge = True
    mock_decision.nudge_type = "memory"
    mock_decision.priority = "high"
    mock_decision.summary = "记住这个配置"

    with patch.object(service.reasoning_judge, 'judge', return_value=mock_decision):
        result = await service.process(
            agent_id="agent-123",
            session_id="session-456",
            reasoning="我应该记住这个配置",
            user_input="设置项目路径",
            agent_output="已设置",
        )

        assert result.nudge_triggered is True
        assert len(result.memory_written) >= 1
        assert result.memory_written[0] == "MEMORY.md"


@pytest.mark.asyncio
async def test_process_no_trigger(service):
    # Mock LLM decision - no nudge
    mock_decision = MagicMock()
    mock_decision.should_nudge = False
    mock_decision.nudge_type = "memory"
    mock_decision.priority = "low"
    mock_decision.summary = ""

    with patch.object(service.reasoning_judge, 'judge', return_value=mock_decision):
        result = await service.process(
            agent_id="agent-123",
            session_id="session-456",
            reasoning="1 + 1 = 2",
            user_input="计算 1+1",
            agent_output="结果是 2",
        )

        assert result.nudge_triggered is False
        assert len(result.memory_written) == 0