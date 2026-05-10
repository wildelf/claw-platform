# Self-Nudge Agent Evolution System — Design Spec

## Context

基于 Hermes Agent 的自我进化机制，为 claw-platform 设计一套 **Self-Nudge + 跨会话记忆 + 自动技能创建** 的完整闭环系统。

**参考架构：** Hermes Agent 三层记忆体系 + 闭环学习回路

---

## 目标

让 Agent 能够：
1. **自我提醒** — 主动识别值得持久化的信息
2. **记忆召回** — 跨会话检索上下文
3. **技能进化** — 从经验中自动生成可复用技能

---

## 架构图

```dot
digraph SelfNudgeArchitecture {
    rankdir=LR;
    splines=ortho;

    subgraph cluster_agent {
        label="Agent Core";
        style=filled;
        color=lightgrey;

        reasoning["Reasoning Layer\n(scratchpad)"];
        tools["Tool Executor"];
    }

    subgraph cluster_nudge_system {
        label="Self-Nudge System";
        style=filled;
        color="#e8f4e8";

        rule_matcher["RuleMatcher\n(预判层)"];
        reasoning_judge["ReasoningJudge\n(推理判断层)"];
        nudge_executor["NudgeExecutor\n(执行层)"];
       复合指标["复合指标检测器"];
    }

    subgraph cluster_memory {
        label="Memory Storage";
        style=filled;
        color="#e8f0f8";

        memory_md["MEMORY.md\nAgent笔记"];
        user_md["USER.md\n用户模型"];
        skills_cache["skills_cache/\n技能缓存"];
        conv_memory["ConversationMemory\n会话记忆"];
    }

    subgraph cluster_skill_evolution {
        label="Skill Evolution";
        style=filled;
        color="#fff4e8";

        skill_generator["SkillGenerator\n(技能生成器)"];
        skill_tracker["SkillTracker\n(使用追踪)"];
        skill_curator["SkillCurator\n(生命周期管理)"];
    }

    -- 数据流 --
    reasoning -> rule_matcher;
    reasoning -> reasoning_judge;
    rule_matcher -> reasoning_judge;
    reasoning_judge -> nudge_executor;
    reasoning_judge -> 复合指标;
    复合指标 -> skill_generator;

    nudge_executor -> memory_md;
    nudge_executor -> user_md;
    nudge_executor -> conv_memory;

    skill_generator -> skills_cache;
    skill_tracker -> skill_curator;
    skill_curator -> skills_cache;

    tools <--> reasoning;
}

digraph SelfNudgeFlow {
    rankdir=TB;
    splines=polyline;

    node [shape=box];

    start["用户请求"];
    rule_check["规则预判\nRuleMatcher"];
    reasoning_check["推理判断\nReasoningJudge"];
    nudge_write["执行写入\nMEMORY.md / USER.md"];
    skill_trigger["复合指标检测"];
    skill_create["创建新技能\nSKILL.md"];
    end["返回结果"];

    start -> rule_check;
    rule_check -> reasoning_check [label="命中规则"];
    rule_check -> end [label="未命中"];
    reasoning_check -> nudge_write [label="触发 nudge"];
    reasoning_check -> skill_trigger [label="符合进化条件"];
    nudge_write -> end;
    skill_trigger -> skill_create [label="阈值达成"];
    skill_create -> end;
}
```

---

## 核心组件

### 1. SelfNudgeService

**职责：** 编排 self-nudge 完整流程

**接口：**
```python
class SelfNudgeService:
    async def process(
        self,
        agent_id: str,
        session_id: str,
        reasoning: str,          # scratchpad 内容
        user_input: str,
        agent_output: str,
    ) -> NudgeResult
```

**返回：**
```python
@dataclass
class NudgeResult:
    nudge_triggered: bool
    memory_written: list[str]   # ['MEMORY.md', 'USER.md']
    skill_created: bool
    skill_id: Optional[str]
```

### 2. RuleMatcher (规则预判层)

**职责：** 快速检测 nudges 触发模式

**规则列表（可配置）：**
```
- "应该记住" / "should remember"
- "important" / "重要"
- "下次需要" / "next time need"
- "注意" / "note"
- "经验总结" / "lesson learned"
- "配置" / "config" + 环境信息
- 用户明确要求："请记住"
```

**实现：** 正则匹配 + 关键词打分

### 3. ReasoningJudge (推理判断层)

**职责：** LLM 推理判断是否真正需要 nudge

**Prompt 模板：**
```
你是一个记忆决策专家。判断以下 Agent 推理过程是否包含值得持久化的信息。

Agent 推理：
{reasoning}

用户输入：{user_input}

判断标准：
1. 包含环境配置或技术发现？
2. 包含用户偏好或沟通习惯？
3. 包含可复用的执行模式？
4. 包含重要的错误教训？

输出 JSON：
{
  "should_nudge": true/false,
  "nudge_type": "memory" | "skill" | "both",
  "priority": "high" | "medium" | "low",
  "summary": "一句话总结"
}
```

### 4. 复合指标检测器

**触发技能自动创建的条件：**

| 指标 | 阈值 | 说明 |
|------|------|------|
| 工具调用数 | ≥5次 | 同一会话内的工具调用总数 |
| 成功率 | ≥80% | 最近3次执行成功率 |
| 正反馈数 | ≥3次 | 用户 positive feedback |
| 复合得分 | ≥10分 | 加权计算：调用数×2 + 成功率×5 + 正反馈×3 |

**计算公式：**
```python
score = tool_call_count * 2 + success_rate * 5 + positive_feedback * 3
if score >= 10 and tool_call_count >= 5:
    trigger_skill_creation()
```

### 5. MemoryPersistence (记忆持久化)

**存储结构：**
```
~/.claw/memories/
├── MEMORY.md         # Agent 个人笔记
├── USER.md           # 用户模型
└── skills_cache/     # 技能进化缓存
    └── {skill_id}/
        ├── SKILL.md
        └── .usage.json
```

**MEMORY.md 结构：**
```markdown
# Agent Memory

## Environment Config
- 项目路径: /path/to/project
- 默认模型: claude-sonnet

## Technical Findings
- 发现: 某种问题的解决方案

## Lessons Learned
- 教训: 避免使用 X 方式
```

**USER.md 结构：**
```markdown
# User Model

## Preferences
- 偏好中文沟通
- 喜欢简洁的回复

## Communication Style
- 直接给出结论
- 需要时提供详细解释
```

### 6. SkillGenerator (技能生成器)

**触发后的生成流程：**

1. 收集上下文 — 从 conversation_memory 提取相关对话
2. 生成 SKILL.md — LLM 生成技能文档
3. 生成 .usage.json — 初始化使用追踪
4. 更新数据库 — skill_evolution_service 处理

**SKILL.md 模板：**
```markdown
---
name: {skill_name}
description: {description}
platforms: [claw-platform]
created_from: experience
---

# {Skill Name}

## When to Use
- 场景描述

## How to Execute
- 执行步骤

## Examples
```
{示例代码}
```

## Notes
- 自动生成
- Version: 1
```

### 7. SkillTracker + SkillCurator (技能生命周期)

**bump_use 实现：**
```python
def bump_use(skill_name: str) -> None:
    # 原子递增 use_count 和 last_used_at
    # 写入 .usage.json sidecar
```

**Curator 规则：**
- `stale_after_days=30` → 标记为 `stale`
- `archive_after_days=90` → 移动到 `.archive/`

---

## 数据模型

### ConversationMemory (扩展)

```python
@dataclass
class ConversationMemory:
    id: EntityId
    agent_id: EntityId
    session_id: str
    user_input: str
    agent_output: str
    summary: str
    tool_call_count: int = 0      # 新增：工具调用数
    success_flag: bool = True     # 新增：执行成功标记
    nudge_candidates: list[str] = field(default_factory=list)  # 新增：nudge 候选
    created_at: datetime
```

### NudgeRecord (新增)

```python
@dataclass
class NudgeRecord:
    id: EntityId
    agent_id: EntityId
    session_id: str
    memory_type: str  # "MEMORY.md" | "USER.md" | "skill"
    content: str
    trigger_reason: str  # "rule" | "reasoning" | "composite"
    priority: str  # "high" | "medium" | "low"
    created_at: datetime
```

### Skill (已有，扩展)

```python
class Skill(BaseEntity):
    name: str
    description: str
    path: str
    status: SkillStatus  # PENDING | TRAINED | EVOLVED | NEEDS_REVIEW
    feedback_count: int
    version: int
    metadata: Dict[str, Any]
    user_id: EntityId
    # 新增字段
    auto_created: bool = False  # 是否自动创建
    use_count: int = 0
    last_used_at: Optional[datetime] = None
```

---

## API 接口

### POST /api/agents/{agent_id}/nudge

手动触发 nudge 检查（可选，供内部调用）

### GET /api/agents/{agent_id}/memories

获取该 Agent 的所有记忆

**响应：**
```json
{
  "memory_md": "...(内容)",
  "user_md": "...(内容)",
  "skills": [...]
}
```

### GET /api/agents/{agent_id}/memories/search?q={query}

跨会话搜索记忆

**响应：**
```json
{
  "results": [
    {
      "type": "memory",
      "file": "MEMORY.md",
      "content": "...",
      "relevance_score": 0.85
    }
  ]
}
```

---

## 实现计划

### Phase 1: Self-Nudge 基础
1. `SelfNudgeService` 核心编排
2. `RuleMatcher` 规则预判
3. `ReasoningJudge` LLM 判断
4. 写入 MEMORY.md / USER.md

### Phase 2: 技能自动创建
1. 复合指标检测器
2. `SkillGenerator` 从经验生成技能
3. `.usage.json` 使用追踪

### Phase 3: 技能生命周期
1. `SkillCurator` stale/archive 管理
2. 技能搜索和召回优化

---

## 验证标准

- [ ] Agent 完成复杂任务后自动写入 MEMORY.md
- [ ] 用户偏好信息自动写入 USER.md
- [ ] 复合指标达成后自动创建 SKILL.md
- [ ] 冷门技能自动归档到 .archive/
- [ ] 跨会话搜索能召回相关记忆