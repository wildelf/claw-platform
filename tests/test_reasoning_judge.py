import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.application.nudge.reasoning_judge import ReasoningJudge, NudgeDecision

@pytest.mark.asyncio
async def test_reasoning_judge_decides_nudge():
    judge = ReasoningJudge()

    # Mock the LLM client
    mock_response = MagicMock()
    mock_response.content = '{"should_nudge": true, "nudge_type": "memory", "priority": "high", "summary": "记住这个配置"}'

    with patch.object(judge, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        decision = await judge.judge(
            reasoning="我应该记住这个配置：项目路径是 /Users/wilde/project",
            user_input="设置项目路径",
            agent_output="已设置项目路径为 /Users/wilde/project",
        )

        assert decision.should_nudge is True
        assert decision.nudge_type == "memory"
        assert decision.priority == "high"
        assert decision.summary == "记住这个配置"

@pytest.mark.asyncio
async def test_reasoning_judge_rejects_noise():
    judge = ReasoningJudge()

    mock_response = MagicMock()
    mock_response.content = '{"should_nudge": false, "nudge_type": "memory", "priority": "low", "summary": ""}'

    with patch.object(judge, '_get_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        decision = await judge.judge(
            reasoning="1 + 1 = 2",
            user_input="计算 1+1",
            agent_output="结果是 2",
        )

        assert decision.should_nudge is False