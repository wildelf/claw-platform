# Self-Nudge Agent Evolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Hermes-inspired 的自我进化系统，包括 Self-Nudge 机制、跨会话记忆召回和自动技能创建

**Architecture:** 混合触发（规则预判 + 推理判断）+ 多文件持久化（MEMORY.md/USER.md/skills_cache）+ 复合指标驱动的技能自动生成

**Tech Stack:** Python (FastAPI), SQLite, LLM (GPT-4o/mini), 文件系统

---

## File Structure

```
backend/app/
├── domain/
│   ├── nudge_record.py          # 新增: NudgeRecord 实体
│   ├── skill.py                 # 已有，扩展 auto_created/use_count
│   └── conversation_memory.py   # 已有，扩展 tool_call_count/success_flag
├── application/
│   ├── self_nudge_service.py    # 新增: 核心编排服务
│   ├── nudge/
│   │   ├── __init__.py
│   │   ├── rule_matcher.py      # 新增: 规则预判层
│   │   ├── reasoning_judge.py    # 新增: LLM推理判断层
│   │   └── composite_metrics.py  # 新增: 复合指标检测器
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── memory_persistence.py # 新增: 多文件持久化
│   │   └── memory_search.py      # 新增: FTS5 搜索
│   ├── skill_generator.py        # 新增: 技能生成器
│   └── skill_curator.py          # 新增: 技能生命周期管理
├── infrastructure/
│   └── storage/
│       ├── sqlite.py             # 修改: 增加 nudge_records 表
│       └── file_storage.py       # 新增: MEMORY.md/USER.md 文件操作
├── api/
│   └── agents.py                 # 修改: 增加 /memories endpoints
└── main.py                      # 修改: 注册新路由
```

---

## Phase 1: Self-Nudge 基础

### Task 1: NudgeRecord 数据模型

**Files:**
- Create: `backend/app/domain/nudge_record.py`
- Modify: `backend/app/domain/__init__.py`
- Test: `tests/test_nudge_record.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_nudge_record.py
import pytest
from app.domain.nudge_record import NudgeRecord, NudgeType, NudgePriority

def test_nudge_record_create():
    record = NudgeRecord.create(
        agent_id="agent-123",
        session_id="session-456",
        memory_type="MEMORY.md",
        content="记住这个重要配置",
        trigger_reason="reasoning",
        priority=NudgePriority.HIGH,
    )
    assert record.agent_id == "agent-123"
    assert record.memory_type == "MEMORY.md"
    assert record.priority == NudgePriority.HIGH
    assert record.trigger_reason == "reasoning"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_nudge_record.py -v`
Expected: FAIL - NudgeRecord not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/domain/nudge_record.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.domain.base import BaseEntity, EntityId


class NudgeType(str, Enum):
    MEMORY = "memory"
    SKILL = "skill"
    BOTH = "both"


class NudgePriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NudgeRecord(BaseEntity):
    agent_id: EntityId
    session_id: str
    memory_type: str  # "MEMORY.md" | "USER.md" | "skill"
    content: str
    trigger_reason: str  # "rule" | "reasoning" | "composite"
    priority: str  # "high" | "medium" | "low"

    @staticmethod
    def create(
        agent_id: str,
        session_id: str,
        memory_type: str,
        content: str,
        trigger_reason: str,
        priority: str = "medium",
    ) -> "NudgeRecord":
        return NudgeRecord(
            id=EntityId.generate(),
            agent_id=EntityId(agent_id),
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            trigger_reason=trigger_reason,
            priority=priority,
            created_at=datetime.now(timezone.utc),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_nudge_record.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/domain/nudge_record.py backend/app/domain/__init__.py tests/test_nudge_record.py
git commit -m "feat(domain): add NudgeRecord entity"
```

---

### Task 2: RuleMatcher 规则预判层

**Files:**
- Create: `backend/app/application/nudge/rule_matcher.py`
- Create: `backend/app/application/nudge/__init__.py`
- Test: `tests/test_rule_matcher.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_rule_matcher.py
import pytest
from app.application.nudge.rule_matcher import RuleMatcher, NudgeCandidate

def test_rule_matcher_detects_memory_pattern():
    matcher = RuleMatcher()
    reasoning = "我应该记住这个配置：项目路径是 /Users/wilde/project"
    candidates = matcher.match(reasoning)
    assert len(candidates) >= 1
    assert any(c.type == "memory" for c in candidates)

def test_rule_matcher_detects_skill_pattern():
    matcher = RuleMatcher()
    reasoning = "这个复杂任务涉及5个工具调用，可以抽象成一个可复用技能"
    candidates = matcher.match(reasoning)
    assert len(candidates) >= 1
    assert any(c.type == "skill" for c in candidates)

def test_rule_matcher_no_match():
    matcher = RuleMatcher()
    reasoning = "简单的加法计算：1 + 1 = 2"
    candidates = matcher.match(reasoning)
    assert len(candidates) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_rule_matcher.py -v`
Expected: FAIL - RuleMatcher not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/application/nudge/__init__.py
from app.application.nudge.rule_matcher import RuleMatcher, NudgeCandidate

__all__ = ["RuleMatcher", "NudgeCandidate"]
```

```python
# backend/app/application/nudge/rule_matcher.py
from dataclasses import dataclass
from enum import Enum
from typing import List


class NudgeType(str, Enum):
    MEMORY = "memory"
    SKILL = "skill"
    BOTH = "both"


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

        # 检测记忆类模式
        for pattern, score in self.MEMORY_PATTERNS:
            import re
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
            import re
            if re.search(pattern, reasoning, re.IGNORECASE):
                match = re.search(pattern, reasoning, re.IGNORECASE)
                candidates.append(NudgeCandidate(
                    type=NudgeType.SKILL,
                    matched_pattern=pattern,
                    matched_text=match.group() if match else "",
                    score=score,
                ))

        return candidates
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_rule_matcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/application/nudge/__init__.py backend/app/application/nudge/rule_matcher.py tests/test_rule_matcher.py
git commit -m "feat(nudge): add RuleMatcher for pattern-based pre-check"
```

---

### Task 3: ReasoningJudge LLM 推理判断层

**Files:**
- Create: `backend/app/application/nudge/reasoning_judge.py`
- Test: `tests/test_reasoning_judge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reasoning_judge.py
import pytest
from app.application.nudge.reasoning_judge import ReasoningJudge, NudgeDecision

@pytest.mark.asyncio
async def test_reasoning_judge_decides_nudge():
    judge = ReasoningJudge()
    decision = await judge.judge(
        reasoning="我应该记住这个配置：项目路径是 /Users/wilde/project，这是重要的环境信息",
        user_input="设置项目路径",
        agent_output="已设置项目路径为 /Users/wilde/project",
    )
    assert decision.should_nudge is True
    assert decision.nudge_type in ["memory", "skill", "both"]

@pytest.mark.asyncio
async def test_reasoning_judge_rejects_noise():
    judge = ReasoningJudge()
    decision = await judge.judge(
        reasoning="1 + 1 = 2",
        user_input="计算 1+1",
        agent_output="结果是 2",
    )
    assert decision.should_nudge is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_reasoning_judge.py -v`
Expected: FAIL - ReasoningJudge not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/application/nudge/reasoning_judge.py
import json
import logging
from dataclasses import dataclass
from typing import Optional

from app.config import settings
from app.domain.base import EntityId

logger = logging.getLogger(__name__)


@dataclass
class NudgeDecision:
    should_nudge: bool
    nudge_type: str  # "memory" | "skill" | "both"
    priority: str  # "high" | "medium" | "low"
    summary: str


class ReasoningJudge:
    """LLM 推理判断层：最终判断是否需要 nudge"""

    SYSTEM_PROMPT = """你是一个记忆决策专家。判断以下 Agent 推理过程是否包含值得持久化的信息。

判断标准：
1. 包含环境配置或技术发现？→ memory
2. 包含用户偏好或沟通习惯？→ memory
3. 包含可复用的执行模式？→ skill
4. 包含重要的错误教训？→ memory
5. 复杂任务（5+工具调用）可以抽象成技能？→ skill

输出 JSON：
{
  "should_nudge": true/false,
  "nudge_type": "memory" | "skill" | "both",
  "priority": "high" | "medium" | "low",
  "summary": "一句话总结"
}"""

    USER_PROMPT = """Agent 推理：
{reasoning}

用户输入：{user_input}

Agent 回复：{agent_output}"""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from langchain_openai import ChatOpenAI
            self._client = ChatOpenAI(
                model=settings.models.default.model,
                api_key=settings.models.default.api_key,
                base_url=settings.models.default.base_url,
            )
        return self._client

    async def judge(
        self,
        reasoning: str,
        user_input: str,
        agent_output: str,
    ) -> NudgeDecision:
        """判断是否触发 nudge"""
        try:
            client = self._get_client()
            user_prompt = self.USER_PROMPT.format(
                reasoning=reasoning,
                user_input=user_input,
                agent_output=agent_output,
            )

            response = await client.ainvoke(
                [{"role": "system", "content": self.SYSTEM_PROMPT},
                 {"role": "user", "content": user_prompt}]
            )

            content = response.content.strip()
            # 尝试解析 JSON
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content)

            return NudgeDecision(
                should_nudge=result.get("should_nudge", False),
                nudge_type=result.get("nudge_type", "memory"),
                priority=result.get("priority", "medium"),
                summary=result.get("summary", ""),
            )
        except Exception as e:
            logger.error(f"ReasoningJudge failed: {e}")
            return NudgeDecision(
                should_nudge=False,
                nudge_type="memory",
                priority="low",
                summary="",
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_reasoning_judge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/application/nudge/reasoning_judge.py tests/test_reasoning_judge.py
git commit -m "feat(nudge): add ReasoningJudge LLM-based decision layer"
```

---

### Task 4: MemoryPersistence 多文件持久化

**Files:**
- Create: `backend/app/application/memory/memory_persistence.py`
- Create: `backend/app/application/memory/__init__.py`
- Create: `backend/app/infrastructure/storage/file_storage.py`
- Modify: `backend/app/config.py` (添加记忆存储路径配置)
- Test: `tests/test_memory_persistence.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_memory_persistence.py
import pytest
import tempfile
import shutil
from pathlib import Path
from app.application.memory.memory_persistence import MemoryPersistence, MemoryType

@pytest.fixture
def temp_mem_dir():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

def test_save_to_memory_md(temp_mem_dir):
    persistence = MemoryPersistence(base_dir=temp_mem_dir)
    await persistence.save(
        agent_id="agent-123",
        memory_type=MemoryType.MEMORY_MD,
        content="# Test Memory\n记住这个配置",
    )
    memory_file = temp_mem_dir / "agent-123" / "MEMORY.md"
    assert memory_file.exists()
    assert "Test Memory" in memory_file.read_text()

def test_save_to_user_md(temp_mem_dir):
    persistence = MemoryPersistence(base_dir=temp_mem_dir)
    await persistence.save(
        agent_id="agent-123",
        memory_type=MemoryType.USER_MD,
        content="# User Preferences\n用户喜欢中文",
    )
    user_file = temp_mem_dir / "agent-123" / "USER.md"
    assert user_file.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_memory_persistence.py -v`
Expected: FAIL - MemoryPersistence not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/application/memory/__init__.py
from app.application.memory.memory_persistence import MemoryPersistence, MemoryType

__all__ = ["MemoryPersistence", "MemoryType"]
```

```python
# backend/app/application/memory/memory_persistence.py
import logging
from pathlib import Path
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    MEMORY_MD = "MEMORY.md"
    USER_MD = "USER.md"


class MemoryPersistence:
    """多文件持久化：MEMORY.md / USER.md"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(settings.memory_storage_path)

    def _get_agent_dir(self, agent_id: str) -> Path:
        return self.base_dir / agent_id

    async def save(
        self,
        agent_id: str,
        memory_type: MemoryType,
        content: str,
        append: bool = True,
    ) -> Path:
        """保存记忆到文件"""
        agent_dir = self._get_agent_dir(agent_id)
        agent_dir.mkdir(parents=True, exist_ok=True)

        file_path = agent_dir / memory_type.value

        if append and file_path.exists():
            existing = file_path.read_text()
            # 避免重复追加
            if content not in existing:
                file_path.write_text(existing + "\n" + content)
        else:
            file_path.write_text(content)

        logger.info(f"Saved {memory_type.value} for agent {agent_id}")
        return file_path

    async def read(
        self,
        agent_id: str,
        memory_type: MemoryType,
    ) -> str:
        """读取记忆文件内容"""
        file_path = self._get_agent_dir(agent_id) / memory_type.value
        if file_path.exists():
            return file_path.read_text()
        return ""

    async def get_all_memories(self, agent_id: str) -> dict:
        """获取该 Agent 的所有记忆"""
        return {
            "MEMORY.md": await self.read(agent_id, MemoryType.MEMORY_MD),
            "USER.md": await self.read(agent_id, MemoryType.USER_MD),
        }
```

```python
# backend/app/infrastructure/storage/file_storage.py
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FileStorage:
    """文件系统存储工具"""

    @staticmethod
    def ensure_dir(path: Path) -> None:
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def write(path: Path, content: str, append: bool = False) -> None:
        """写入文件"""
        if append and path.exists():
            path.write_text(path.read_text() + "\n" + content)
        else:
            path.write_text(content)

    @staticmethod
    def read(path: Path) -> str:
        """读取文件"""
        if path.exists():
            return path.read_text()
        return ""

    @staticmethod
    def delete(path: Path) -> bool:
        """删除文件"""
        if path.exists():
            path.unlink()
            return True
        return False

    @staticmethod
    def list_files(dir_path: Path, pattern: str = "*") -> list[Path]:
        """列出目录下文件"""
        if dir_path.exists():
            return list(dir_path.glob(pattern))
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_memory_persistence.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/application/memory/__init__.py backend/app/application/memory/memory_persistence.py backend/app/infrastructure/storage/file_storage.py tests/test_memory_persistence.py
git commit -m "feat(memory): add MemoryPersistence for MEMORY.md/USER.md files"
```

---

### Task 5: SelfNudgeService 核心编排

**Files:**
- Create: `backend/app/application/self_nudge_service.py`
- Modify: `backend/app/domain/conversation_memory.py` (扩展字段)
- Test: `tests/test_self_nudge_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_self_nudge_service.py
import pytest
from app.application.self_nudge_service import SelfNudgeService, NudgeResult

@pytest.fixture
def service():
    from app.infrastructure.storage.sqlite import SQLiteStorage
    storage = SQLiteStorage(db_path=":memory:")
    return SelfNudgeService(storage=storage)

@pytest.mark.asyncio
async def test_process_triggers_nudge(service):
    result = await service.process(
        agent_id="agent-123",
        session_id="session-456",
        reasoning="我应该记住这个配置：项目路径是 /Users/wilde/project",
        user_input="设置项目路径",
        agent_output="已设置项目路径",
    )
    assert isinstance(result, NudgeResult)
    assert result.nudge_triggered is True
    assert len(result.memory_written) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_self_nudge_service.py -v`
Expected: FAIL - SelfNudgeService not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/application/self_nudge_service.py
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

        # 记录 nudge
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
        record = NudgeRecord.create(
            agent_id=agent_id,
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            trigger_reason=trigger_reason,
            priority=priority,
        )
        await self.storage.save_nudge_record(record)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_self_nudge_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/application/self_nudge_service.py tests/test_self_nudge_service.py
git commit -m "feat(nudge): add SelfNudgeService orchestration layer"
```

---

## Phase 2: 技能自动创建

### Task 6: 复合指标检测器

**Files:**
- Create: `backend/app/application/nudge/composite_metrics.py`
- Test: `tests/test_composite_metrics.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_composite_metrics.py
import pytest
from app.application.nudge.composite_metrics import CompositeMetrics, MetricsResult

def test_composite_score_calculation():
    metrics = CompositeMetrics()
    result = metrics.calculate(
        tool_call_count=5,
        success_rate=0.9,
        positive_feedback=3,
    )
    assert result.score >= 10
    assert result.should_trigger_skill

def test_threshold_not_met():
    metrics = CompositeMetrics()
    result = metrics.calculate(
        tool_call_count=2,
        success_rate=0.5,
        positive_feedback=1,
    )
    assert result.score < 10
    assert result.should_trigger_skill is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_composite_metrics.py -v`
Expected: FAIL - CompositeMetrics not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/application/nudge/composite_metrics.py
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
        """计算复合得分"""
        score = (
            tool_call_count * self.TOOL_CALL_WEIGHT +
            success_rate * 100 * self.SUCCESS_RATE_WEIGHT / 100 +
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_composite_metrics.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/application/nudge/composite_metrics.py tests/test_composite_metrics.py
git commit -m "feat(metrics): add CompositeMetrics detector for skill creation"
```

---

### Task 7: SkillGenerator 技能生成器

**Files:**
- Create: `backend/app/application/skill_generator.py`
- Test: `tests/test_skill_generator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_skill_generator.py
import pytest
from app.application.skill_generator import SkillGenerator

@pytest.fixture
def generator():
    from app.infrastructure.storage.sqlite import SQLiteStorage
    storage = SQLiteStorage(db_path=":memory:")
    return SkillGenerator(storage=storage)

@pytest.mark.asyncio
async def test_generate_skill_md(generator):
    skill = await generator.generate_from_conversation(
        agent_id="agent-123",
        session_id="session-456",
        skill_name="test-skill",
        description="Test skill description",
    )
    assert skill is not None
    assert skill.name == "test-skill"
    assert skill.auto_created is True
    assert skill.status.value == "trained"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_skill_generator.py -v`
Expected: FAIL - SkillGenerator not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/application/skill_generator.py
import logging
from typing import Optional

from app.domain.skill import Skill, SkillStatus
from app.domain.conversation_memory import ConversationMemory
from app.infrastructure.storage.base import StorageAdapter

logger = logging.getLogger(__name__)


class SkillGenerator:
    """从经验中自动生成技能"""

    SKILL_MD_TEMPLATE = """---
name: {name}
description: {description}
platforms: [claw-platform]
created_from: experience
auto_created: true
---

# {name}

## When to Use
- {when_to_use}

## How to Execute
{how_to_execute}

## Examples
```
{examples}
```

## Notes
- 自动生成 from conversation experience
- Version: 1
"""

    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    async def generate_from_conversation(
        self,
        agent_id: str,
        session_id: str,
        skill_name: str,
        description: str,
    ) -> Optional[Skill]:
        """从会话生成技能"""
        try:
            # 收集相关对话记忆
            memories = await self.storage.get_conversation_memories(
                agent_id=agent_id,
                session_id=session_id,
                limit=5,
            )

            # 生成 SKILL.md 内容
            skill_md = self._generate_skill_md(
                skill_name=skill_name,
                description=description,
                memories=memories,
            )

            # 创建技能实体
            skill = Skill(
                id=self.storage.generate_id(),
                name=skill_name,
                description=description,
                path=f"skills_cache/{skill_name}",
                status=SkillStatus.TRAINED,
                feedback_count=0,
                version=1,
                metadata={},
                user_id=agent_id,
                auto_created=True,
                use_count=0,
            )

            await self.storage.save_skill(skill)

            # 保存 SKILL.md 文件
            await self.storage.save_skill_file(
                skill.id,
                "SKILL.md",
                skill_md.encode("utf-8"),
            )

            logger.info(f"Generated skill {skill_name} from conversation")
            return skill

        except Exception as e:
            logger.error(f"Failed to generate skill: {e}")
            return None

    def _generate_skill_md(
        self,
        skill_name: str,
        description: str,
        memories: list[ConversationMemory],
    ) -> str:
        """生成 SKILL.md 内容"""
        # 从对话记忆提取示例
        examples = []
        for mem in memories[:3]:
            examples.append(f"User: {mem.user_input}\nAgent: {mem.agent_output}")

        example_text = "\n\n".join(examples) if examples else "待补充"

        return self.SKILL_MD_TEMPLATE.format(
            name=skill_name,
            description=description,
            when_to_use=f"执行 {skill_name} 相关任务时",
            how_to_execute="- 步骤1\n- 步骤2\n- 步骤3",
            examples=example_text,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_skill_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/application/skill_generator.py tests/test_skill_generator.py
git commit -m "feat(skill): add SkillGenerator for auto-creating skills from experience"
```

---

### Task 8: bump_use + SkillTracker 使用追踪

**Files:**
- Create: `backend/app/application/skill_curator.py`
- Test: `tests/test_skill_curator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_skill_curator.py
import pytest
import tempfile
from pathlib import Path
from app.application.skill_curator import SkillCurator, bump_use

@pytest.fixture
def temp_skills_dir():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    import shutil
    shutil.rmtree(tmp)

def test_bump_use_increments_count(temp_skills_dir, monkeypatch):
    # Mock settings
    monkeypatch.setattr("app.config.settings", type("Settings", (), {
        "skills_cache_path": str(temp_skills_dir)
    })())

    skill_name = "test-skill"
    bump_use(skill_name)

    usage_file = temp_skills_dir / f"{skill_name}.usage.json"
    assert usage_file.exists()

    import json
    data = json.loads(usage_file.read_text())
    assert data["use_count"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_skill_curator.py -v`
Expected: FAIL - bump_use not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/application/skill_curator.py
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def bump_use(skill_name: str) -> None:
    """原子递增技能使用计数"""
    skills_cache = Path(settings.skills_cache_path)
    usage_file = skills_cache / f"{skill_name}.usage.json"

    # 读取现有数据
    if usage_file.exists():
        data = json.loads(usage_file.read_text())
    else:
        data = {"use_count": 0, "last_used_at": None}

    # 递增
    data["use_count"] = data.get("use_count", 0) + 1
    data["last_used_at"] = datetime.now(timezone.utc).isoformat()

    # 原子写入
    skills_cache.mkdir(parents=True, exist_ok=True)
    temp_file = usage_file.with_suffix(".tmp")
    temp_file.write_text(json.dumps(data, indent=2))
    temp_file.replace(usage_file)


class SkillCurator:
    """技能生命周期管理：stale/archive"""

    STALE_AFTER_DAYS = 30
    ARCHIVE_AFTER_DAYS = 90

    def __init__(self, storage):
        self.storage = storage

    async def check_and_curate(self, skill_id: str) -> str:
        """检查技能状态，返回处理结果"""
        skill = await self.storage.get_skill(skill_id)
        if not skill:
            return "not_found"

        usage_file = Path(settings.skills_cache_path) / f"{skill.name}.usage.json"
        if not usage_file.exists():
            return "no_usage_data"

        data = json.loads(usage_file.read_text())
        last_used = datetime.fromisoformat(data["last_used_at"])
        days_since_use = (datetime.now(timezone.utc) - last_used).days

        if days_since_use >= self.ARCHIVE_AFTER_DAYS:
            await self._archive_skill(skill)
            return "archived"
        elif days_since_use >= self.STALE_AFTER_DAYS:
            skill.status = "stale"
            await self.storage.save_skill(skill)
            return "marked_stale"

        return "active"

    async def _archive_skill(self, skill) -> None:
        """归档技能到 .archive/"""
        archive_dir = Path(settings.skills_cache_path) / ".archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        skill_dir = Path(settings.skills_cache_path) / skill.name
        if skill_dir.exists():
            import shutil
            shutil.move(str(skill_dir), str(archive_dir / skill.name))

        skill.status = "archived"
        await self.storage.save_skill(skill)
        logger.info(f"Archived skill {skill.name}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_skill_curator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/application/skill_curator.py tests/test_skill_curator.py
git commit -m "feat(skill): add bump_use and SkillCurator lifecycle management"
```

---

### Task 9: Storage 扩展

**Files:**
- Modify: `backend/app/infrastructure/storage/sqlite.py`
- Modify: `backend/app/config.py`
- Test: `tests/test_storage_extension.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_storage_extension.py
import pytest
from app.infrastructure.storage.sqlite import SQLiteStorage

@pytest.mark.asyncio
async def test_save_and_get_nudge_record():
    storage = SQLiteStorage(db_path=":memory:")
    from app.domain.nudge_record import NudgeRecord
    record = NudgeRecord.create(
        agent_id="agent-123",
        session_id="session-456",
        memory_type="MEMORY.md",
        content="Test content",
        trigger_reason="reasoning",
        priority="medium",
    )
    await storage.save_nudge_record(record)
    retrieved = await storage.get_nudge_record(record.id)
    assert retrieved is not None
    assert retrieved.content == "Test content"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_storage_extension.py -v`
Expected: FAIL - save_nudge_record not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/config.py (添加)
memory_storage_path: str = "~/.claw/memories"
skills_cache_path: str = "~/.claw/memories/skills_cache"
```

```python
# backend/app/infrastructure/storage/sqlite.py (添加方法)
async def save_nudge_record(self, record: NudgeRecord) -> None:
    self.cur.execute("""
        INSERT INTO nudge_records (id, agent_id, session_id, memory_type, content, trigger_reason, priority, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(record.id),
        str(record.agent_id),
        record.session_id,
        record.memory_type,
        record.content,
        record.trigger_reason,
        record.priority,
        record.created_at.isoformat(),
    ))
    self.conn.commit()

async def get_nudge_record(self, record_id: str) -> Optional[NudgeRecord]:
    self.cur.execute("SELECT * FROM nudge_records WHERE id = ?", (record_id,))
    row = self.cur.fetchone()
    if row:
        return NudgeRecord(**dict(row))
    return None

async def get_nudge_records_by_agent(self, agent_id: str, limit: int = 100) -> List[NudgeRecord]:
    self.cur.execute(
        "SELECT * FROM nudge_records WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
        (agent_id, limit)
    )
    return [NudgeRecord(**dict(row)) for row in self.cur.fetchall()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_storage_extension.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/infrastructure/storage/sqlite.py backend/app/config.py tests/test_storage_extension.py
git commit -m "feat(storage): extend SQLite storage for nudge_records"
```

---

### Task 10: API Endpoints

**Files:**
- Modify: `backend/app/api/agents.py`
- Test: `tests/test_memory_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_memory_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_agent_memories():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/agents/agent-123/memories")
        # 初始为空
        assert response.status_code == 200
        data = response.json()
        assert "memory_md" in data
        assert "user_md" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_memory_api.py -v`
Expected: FAIL - endpoint not defined

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/api/agents.py (添加路由)
@router.get("/api/agents/{agent_id}/memories")
async def get_agent_memories(agent_id: str):
    """获取该 Agent 的所有记忆"""
    from app.application.memory.memory_persistence import MemoryPersistence
    persistence = MemoryPersistence()
    memories = await persistence.get_all_memories(agent_id)
    return memories


@router.get("/api/agents/{agent_id}/memories/search")
async def search_agent_memories(agent_id: str, q: str):
    """跨会话搜索记忆"""
    # TODO: 实现 FTS5 搜索
    return {"results": []}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wilde/workplace/projects/claw-platform && python -m pytest tests/test_memory_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/agents.py tests/test_memory_api.py
git commit -m "feat(api): add /api/agents/{id}/memories endpoints"
```

---

## Phase 3: 跨会话记忆搜索 (可选，后续实现)

### Task 11: FTS5 全文搜索

- 实现 FTS5 虚拟表
- 实现 `search_agent_memories` 端点

---

## 验证标准

- [ ] SelfNudgeService 能正确触发 nudge 并写入 MEMORY.md/USER.md
- [ ] 复合指标达到阈值后自动创建 SKILL.md
- [ ] bump_use 能正确追踪技能使用次数
- [ ] 长时间未使用的技能被标记为 stale/archive
- [ ] API 能返回指定 Agent 的所有记忆

---

## 依赖关系

```
Task 1 (NudgeRecord) ──┬── Task 5 (SelfNudgeService)
                       │
Task 2 (RuleMatcher) ──┘
Task 3 (ReasoningJudge) │
Task 4 (MemoryPersistence) │
                        │
Task 6 (CompositeMetrics) ── Task 7 (SkillGenerator) ── Task 8 (SkillCurator)
                                                       │
Task 9 (Storage Extension) ───────────────────────────┘
Task 10 (API Endpoints)
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-11-self-nudge-agent-evolution-plan.md`**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**