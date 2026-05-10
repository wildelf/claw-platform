from dataclasses import dataclass
from enum import Enum
from typing import List


class NudgeType(str, Enum):
    MEMORY = "memory"
    SKILL = "skill"


@dataclass
class NudgeCandidate:
    type: NudgeType  # "memory" | "skill"
    matched_pattern: str
    matched_text: str
    score: float  # 0.0 - 1.0


class RuleMatcher:
    """规则预判层：快速检测 nudges 触发模式"""

    # 记忆类模式
    MEMORY_PATTERNS = [
        (r"应该记住|should remember|记住这个|remember this", 0.9),
        (r"重要|important|关键|critical", 0.7),
        (r"下次需要|next time|下次注意", 0.8),
        (r"配置|config|设置", 0.6),
        (r"经验教训?|lesson learned?|学到", 0.8),
        (r"请记住|please remember", 1.0),
    ]

    # 技能类模式
    SKILL_PATTERNS = [
        (r"可以抽象成.{0,20}技能|abstract.{0,20}skill", 0.9),
        (r"可复用|reusable|复用", 0.7),
        (r"\d+.{0,5}次.{0,5}工具调用|\d+.{0,5}tool calls", 0.8),
        (r"复杂任务|complex task|这个任务", 0.6),
        (r"经常做|often repeat|重复.{0,10}任务", 0.7),
    ]

    def match(self, reasoning: str) -> List[NudgeCandidate]:
        """检测 reasoning 中的 nudge 候选"""
        candidates = []
        import re

        # 检测记忆类模式
        for pattern, score in self.MEMORY_PATTERNS:
            if re.search(pattern, reasoning, re.IGNORECASE):
                match = re.search(pattern, reasoning, re.IGNORECASE)
                candidates.append(NudgeCandidate(
                    type=NudgeType.MEMORY,
                    matched_pattern=pattern,
                    matched_text=match.group() if match else "",
                    score=score,
                ))

        # 检测技能类模式
        for pattern, score in self.SKILL_PATTERNS:
            if re.search(pattern, reasoning, re.IGNORECASE):
                match = re.search(pattern, reasoning, re.IGNORECASE)
                candidates.append(NudgeCandidate(
                    type=NudgeType.SKILL,
                    matched_pattern=pattern,
                    matched_text=match.group() if match else "",
                    score=score,
                ))

        return candidates