import pytest
from app.application.nudge.rule_matcher import RuleMatcher, NudgeCandidate


def test_rule_matcher_detects_memory_pattern():
    matcher = RuleMatcher()
    reasoning = "我应该记住这个配置：项目路径是 /Users/wilde/project"
    candidates = matcher.match(reasoning)
    assert len(candidates) >= 1
    assert any(c.type.value == "memory" for c in candidates)


def test_rule_matcher_detects_skill_pattern():
    matcher = RuleMatcher()
    reasoning = "这个复杂任务涉及5个工具调用，可以抽象成一个可复用技能"
    candidates = matcher.match(reasoning)
    assert len(candidates) >= 1
    assert any(c.type.value == "skill" for c in candidates)


def test_rule_matcher_no_match():
    matcher = RuleMatcher()
    reasoning = "简单的加法计算：1 + 1 = 2"
    candidates = matcher.match(reasoning)
    assert len(candidates) == 0