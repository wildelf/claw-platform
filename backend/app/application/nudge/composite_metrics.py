from dataclasses import dataclass


@dataclass
class MetricsResult:
    score: float
    should_trigger_skill: bool
    tool_call_count: int
    success_rate: float
    positive_feedback: int


class CompositeMetrics:
    """复合指标检测器：计算技能自动创建触发条件"""

    # 阈值
    SCORE_THRESHOLD = 10
    TOOL_CALL_THRESHOLD = 5

    # 权重
    TOOL_CALL_WEIGHT = 2
    SUCCESS_RATE_WEIGHT = 5
    POSITIVE_FEEDBACK_WEIGHT = 3

    def calculate(
        self,
        tool_call_count: int,
        success_rate: float,
        positive_feedback: int,
    ) -> MetricsResult:
        """计算复合得分

        计算公式：
        score = tool_call_count * TOOL_CALL_WEIGHT
              + success_rate * SUCCESS_RATE_WEIGHT
              + positive_feedback * POSITIVE_FEEDBACK_WEIGHT

        触发条件：score >= 10 AND tool_call_count >= 5
        """
        score = (
            tool_call_count * self.TOOL_CALL_WEIGHT +
            success_rate * self.SUCCESS_RATE_WEIGHT +
            positive_feedback * self.POSITIVE_FEEDBACK_WEIGHT
        )

        should_trigger = (
            score >= self.SCORE_THRESHOLD and
            tool_call_count >= self.TOOL_CALL_THRESHOLD
        )

        return MetricsResult(
            score=score,
            should_trigger_skill=should_trigger,
            tool_call_count=tool_call_count,
            success_rate=success_rate,
            positive_feedback=positive_feedback,
        )