import logging
from dataclasses import dataclass
from typing import Optional, List

from app.application.nudge.rule_matcher import RuleMatcher
from app.application.nudge.reasoning_judge import ReasoningJudge, NudgeDecision
from app.application.memory.memory_persistence import MemoryPersistence, MemoryType
from app.domain.nudge_record import NudgeRecord

logger = logging.getLogger(__name__)


@dataclass
class NudgeResult:
    nudge_triggered: bool
    memory_written: List[str]  # ["MEMORY.md", "USER.md"]
    skill_created: bool
    skill_id: Optional[str]
    decision: Optional[NudgeDecision]


class SelfNudgeService:
    """Self-Nudge 核心编排服务"""

    def __init__(
        self,
        storage,
        memory_persistence: MemoryPersistence = None,
    ):
        self.storage = storage
        self.rule_matcher = RuleMatcher()
        self.reasoning_judge = ReasoningJudge()
        self.memory_persistence = memory_persistence or MemoryPersistence()

    async def process(
        self,
        agent_id: str,
        session_id: str,
        reasoning: str,
        user_input: str,
        agent_output: str,
    ) -> NudgeResult:
        """处理 self-nudge 完整流程"""
        memory_written = []
        skill_created = False
        skill_id = None

        # Step 1: 规则预判
        rule_candidates = self.rule_matcher.match(reasoning)
        has_rule_match = len(rule_candidates) > 0

        # Step 2: LLM 推理判断
        decision = await self.reasoning_judge.judge(
            reasoning=reasoning,
            user_input=user_input,
            agent_output=agent_output,
        )

        # 如果规则命中但 LLM 判断不触发，以 LLM 为准
        if not decision.should_nudge and not has_rule_match:
            return NudgeResult(
                nudge_triggered=False,
                memory_written=[],
                skill_created=False,
                skill_id=None,
                decision=decision,
            )

        # Step 3: 执行写入
        if decision.should_nudge or has_rule_match:
            if decision.nudge_type in ["memory", "both"]:
                memory_file = await self._write_memory(agent_id, decision.summary)
                memory_written.append(memory_file)

            if decision.nudge_type in ["skill", "both"]:
                # 技能创建在 Phase 2 实现
                pass

        # 记录 nudge（如果有存储）
        if hasattr(self.storage, 'save_nudge_record'):
            await self._record_nudge(
                agent_id=agent_id,
                session_id=session_id,
                memory_type=",".join(memory_written) if memory_written else "skill",
                content=decision.summary,
                trigger_reason="reasoning" if has_rule_match else "rule",
                priority=decision.priority,
            )

        return NudgeResult(
            nudge_triggered=True,
            memory_written=memory_written,
            skill_created=skill_created,
            skill_id=skill_id,
            decision=decision,
        )

    async def _write_memory(self, agent_id: str, content: str) -> str:
        """写入记忆文件"""
        # 判断写入哪个文件
        memory_type = MemoryType.MEMORY_MD
        if "偏好" in content or "喜欢" in content or "preference" in content.lower():
            memory_type = MemoryType.USER_MD

        await self.memory_persistence.save(
            agent_id=agent_id,
            memory_type=memory_type,
            content=f"- {content}",
            append=True,
        )
        return memory_type.value

    async def _record_nudge(
        self,
        agent_id: str,
        session_id: str,
        memory_type: str,
        content: str,
        trigger_reason: str,
        priority: str,
    ) -> None:
        """记录 nudge 事件"""
        if hasattr(self.storage, 'save_nudge_record'):
            from app.domain.nudge_record import NudgeRecord as NR, NudgePriority
            from app.domain.base import EntityId
            record = NR.create(
                agent_id=EntityId(agent_id),
                session_id=session_id,
                memory_type=memory_type,
                content=content,
                trigger_reason=trigger_reason,
                priority=NudgePriority(priority),
            )
            await self.storage.save_nudge_record(record)