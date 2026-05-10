import pytest
from app.application.nudge.composite_metrics import CompositeMetrics, MetricsResult


def test_composite_score_calculation():
    metrics = CompositeMetrics()
    result = metrics.calculate(
        tool_call_count=5,
        success_rate=0.9,
        positive_feedback=3,
    )
    # 5*2 + 0.9*5 + 3*3 = 10 + 4.5 + 9 = 23.5 >= 10
    assert result.score >= 10
    assert result.should_trigger_skill is True


def test_threshold_not_met():
    metrics = CompositeMetrics()
    result = metrics.calculate(
        tool_call_count=2,
        success_rate=0.5,
        positive_feedback=1,
    )
    # 2*2 + 0.5*5 + 1*3 = 4 + 2.5 + 3 = 9.5 < 10
    assert result.score < 10
    assert result.should_trigger_skill is False


def test_tool_call_threshold_not_met():
    metrics = CompositeMetrics()
    result = metrics.calculate(
        tool_call_count=3,  # Less than 5
        success_rate=1.0,
        positive_feedback=5,
    )
    # Even with high score, tool_call < 5 should not trigger
    assert result.should_trigger_skill is False


def test_high_success_rate():
    metrics = CompositeMetrics()
    result = metrics.calculate(
        tool_call_count=5,
        success_rate=1.0,  # 100%
        positive_feedback=2,
    )
    # 5*2 + 1.0*5 + 2*3 = 10 + 5 + 6 = 21 >= 10
    assert result.should_trigger_skill is True