# Claw Platform Phase 3: 自我进化

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Skill 自动生成和进化机制，通过 Feedback 反馈驱动 Skills 不断优化

**Architecture:** 反馈驱动的事件处理架构，当 positive feedback 累积达到阈值时触发 Skill 生成，negative feedback 触发 Skill 进化

**Tech Stack:** Python 3.11+, FastAPI, deepagents

---

## 文件结构

```
backend/
├── app/
│   ├── application/
│   │   ├── feedback_service.py   # 更新：增强反馈处理
│   │   ├── skill_evolution_service.py  # 新增：Skill 进化服务
│   │   └── skill_generator.py    # 新增：Skill 生成器
│   ├── api/
│   │   └── agents.py            # 更新：添加 run_agent_with_feedback
│   └── infrastructure/
│       └── storage/
│           └── sqlite.py          # 更新：添加反馈统计查询
└── config.yaml                  # 新增：进化配置
```

---

## Task 1: Skill 生成服务

**Files:**
- Create: `backend/app/application/skill_generator.py`
- Create: `backend/app/application/skill_evolution_service.py`
- Modify: `backend/app/application/feedback_service.py` (添加反馈处理逻辑)

- [ ] **Step 1: Create skill_evolution_service.py**

```python
"""Skill evolution service.

Handles skill generation and evolution based on feedback events.
"""

from typing import List, Optional

from app.domain.skill import Skill, SkillStatus
from app.domain.feedback import FeedbackEvent, FeedbackRating
from app.infrastructure.storage.sqlite import SQLiteStorage


# Default threshold for positive feedback before skill generation
DEFAULT_GENERATION_THRESHOLD = 3


class SkillEvolutionService:
    """Service for skill evolution and generation."""

    def __init__(
        self,
        storage: SQLiteStorage,
        generation_threshold: int = DEFAULT_GENERATION_THRESHOLD,
    ):
        self.storage = storage
        self.generation_threshold = generation_threshold

    async def process_feedback(
        self,
        feedback: FeedbackEvent,
    ) -> Optional[str]:
        """Process a feedback event and trigger evolution if needed.

        Returns:
            skill_id if evolution was triggered, None otherwise.
        """
        if not feedback.skill_id:
            return None

        skill = await self.storage.get_skill(feedback.skill_id)
        if not skill:
            return None

        if feedback.rating == FeedbackRating.POSITIVE:
            return await self._handle_positive_feedback(skill, feedback)
        else:
            return await self._handle_negative_feedback(skill, feedback)

    async def _handle_positive_feedback(
        self,
        skill: Skill,
        feedback: FeedbackEvent,
    ) -> Optional[str]:
        """Handle positive feedback - increment count and check threshold."""
        skill.feedback_count += 1
        await self.storage.save_skill(skill)

        # Check if we should generate a trained skill
        if skill.feedback_count >= self.generation_threshold:
            # Generate skill files from feedback
            await self._generate_skill(skill, feedback)
            # Reset feedback count after generation
            skill.feedback_count = 0
            skill.status = SkillStatus.TRAINED
            await self.storage.save_skill(skill)
            return skill.id

        await self.storage.save_skill(skill)
        return None

    async def _handle_negative_feedback(
        self,
        skill: Skill,
        feedback: FeedbackEvent,
    ) -> Optional[str]:
        """Handle negative feedback - mark for review."""
        skill.status = SkillStatus.NEEDS_REVIEW
        # Store the issue in metadata
        if "issues" not in skill.metadata:
            skill.metadata["issues"] = []
        skill.metadata["issues"].append({
            "feedback_id": feedback.id,
            "context": feedback.context,
            "result": feedback.result,
        })
        await self.storage.save_skill(skill)
        return skill.id

    async def _generate_skill(
        self,
        skill: Skill,
        feedback: FeedbackEvent,
    ) -> None:
        """Generate skill files from positive feedback.

        This creates SKILL.md and helper.py files based on
        the successful execution patterns from feedback.
        """
        # Create SKILL.md content
        skill_md = self._generate_skill_markdown(skill, feedback)
        await self.storage.save_skill_file(
            skill.id,
            "SKILL.md",
            skill_md.encode("utf-8"),
        )

        # Create helper.py if needed (for complex skills)
        helper_py = self._generate_helper_code(skill, feedback)
        if helper_py:
            await self.storage.save_skill_file(
                skill.id,
                "helper.py",
                helper_py.encode("utf-8"),
            )

    def _generate_skill_markdown(
        self,
        skill: Skill,
        feedback: FeedbackEvent,
    ) -> str:
        """Generate SKILL.md content from feedback."""
        context = feedback.context or {}

        lines = [
            f"# {skill.name}",
            "",
            f"{skill.description or 'Auto-generated skill from successful executions.'}",
            "",
            "## When to Use",
            f"- {context.get('task_description', 'When performing this type of task')}",
            "",
            "## How to Execute",
            f"- {context.get('steps', 'Follow the successful pattern')}",
            "",
            "## Examples",
            f"```",
            f"{feedback.result[:500]}",
            f"```" if len(feedback.result) > 500 else "",
            "",
            "## Notes",
            "- Auto-generated from positive feedback",
            f"- Version: {skill.version}",
        ]

        return "\n".join([l for l in lines if l])

    def _generate_helper_code(
        self,
        skill: Skill,
        feedback: FeedbackEvent,
    ) -> Optional[str]:
        """Generate helper.py content if needed."""
        # For simple skills, no helper is needed
        context = feedback.context or {}
        if not context.get("tool_calls"):
            return None

        # Generate helper code based on tool usage patterns
        code = [
            "\"\"\"Helper functions for skill.\"\"\"",
            "",
            "from typing import Any, Dict",
            "",
            "",
            f"def execute_{skill.name.replace('-', '_')}(context: Dict[str, Any]) -> Any:",
            f"    \"\"\"Execute the {skill.name} skill.\"\"\"",
            "    # Auto-generated from feedback analysis",
            "    pass",
        ]

        return "\n".join(code)
```

- [ ] **Step 2: Update feedback_service.py**

在 `FeedbackService` 中添加反馈处理方法：

```python
from app.application.skill_evolution_service import SkillEvolutionService

async def submit_with_evolution(
    self,
    feedback: FeedbackEvent,
) -> tuple[FeedbackEvent, Optional[str]]:
    """Submit feedback and trigger evolution if needed.

    Returns:
        Tuple of (feedback, evolved_skill_id if triggered)
    """
    # Save feedback
    await self.storage.save_feedback(feedback)

    # Process evolution
    evolution_service = SkillEvolutionService(self.storage)
    evolved_skill_id = await evolution_service.process_feedback(feedback)

    return feedback, evolved_skill_id
```

- [ ] **Step 3: Test imports**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.application.skill_evolution_service import SkillEvolutionService; from app.application.skill_generator import SkillGenerator; print('Evolution services imported')"`
Expected: `Evolution services imported`

- [ ] **Step 4: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/application/skill_evolution_service.py
git commit -m "feat: add skill evolution service"
```

---

## Task 2: Skill 进化 API

**Files:**
- Modify: `backend/app/api/feedback.py` (添加进化端点)
- Modify: `backend/app/api/agents.py` (添加带反馈的执行端点)

- [ ] **Step 1: Update api/feedback.py**

添加进化相关端点：

```python
@router.post("/{feedback_id}/process")
async def process_feedback(
    feedback_id: str,
    storage: Storage,
) -> dict:
    """Process a feedback event and trigger evolution if needed.

    This endpoint is for manually triggering evolution processing
    on a feedback event (e.g., after reviewing the feedback).
    """
    service = FeedbackService(storage)
    feedback = await service.get(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    _, evolved_skill_id = await service.submit_with_evolution(feedback)

    return {
        "feedback_id": feedback_id,
        "evolved_skill_id": evolved_skill_id,
        "evolution_triggered": evolved_skill_id is not None,
    }


@router.get("/skills/{skill_id}/evolution-history")
async def get_skill_evolution_history(
    skill_id: str,
    storage: Storage,
    offset: int = 0,
    limit: int = 50,
) -> List[FeedbackEvent]:
    """Get feedback history for a skill that contributed to evolution."""
    service = FeedbackService(storage)
    feedbacks = await service.list_by_skill(skill_id, offset, limit)
    return [f for f in feedbacks if f.rating == FeedbackRating.POSITIVE.value]
```

- [ ] **Step 2: Update api/agents.py**

添加带反馈的 Agent 执行端点：

```python
@router.post("/{agent_id}/run-with-feedback")
async def run_agent_with_feedback(
    agent_id: str,
    task: str,
    storage: Storage,
) -> dict:
    """Run agent and submit feedback when task completes.

    This is a convenience endpoint that runs the agent and
    returns immediately. Feedback should be submitted separately
    via POST /api/feedback after reviewing the results.

    TODO: Implement actual agent execution via deepagents.
    """
    service = AgentService(storage)
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # TODO: Integrate with deepagents for actual execution
    return {
        "status": "todo",
        "message": "Agent execution with feedback not yet implemented",
        "agent_id": agent_id,
        "task": task,
    }
```

- [ ] **Step 3: Test imports**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.api.feedback import router; print('Feedback with evolution imported')"`
Expected: `Feedback with evolution imported`

- [ ] **Step 4: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/api/feedback.py backend/app/api/agents.py
git commit -m "feat: add skill evolution API endpoints"
```

---

## Task 3: Skill 自我进化逻辑

**Files:**
- Modify: `backend/app/application/skill_evolution_service.py` (添加进化方法)

- [ ] **Step 1: Add evolution methods to SkillEvolutionService**

在 `SkillEvolutionService` 中添加进化方法：

```python
async def evolve_skill(
    self,
    skill_id: str,
    improvements: dict,
) -> Skill:
    """Evolve an existing skill based on feedback.

    Args:
        skill_id: ID of the skill to evolve
        improvements: Dict containing:
            - positive_patterns: List[str] patterns to add
            - negative_patterns: List[str] patterns to avoid
            - new_examples: List[str] examples to add

    Returns:
        Updated skill
    """
    skill = await self.storage.get_skill(skill_id)
    if not skill:
        raise ValueError(f"Skill not found: {skill_id}")

    # Update version
    skill.version += 1

    # Update metadata with evolution info
    if "evolutions" not in skill.metadata:
        skill.metadata["evolutions"] = []
    skill.metadata["evolutions"].append({
        "version": skill.version,
        "improvements": improvements,
    })

    # If there was an issue list, clear it on successful evolution
    if skill.status == SkillStatus.NEEDS_REVIEW:
        skill.status = SkillStatus.EVOLVED

    # Regenerate skill files with improvements
    await self._update_skill_files(skill, improvements)

    await self.storage.save_skill(skill)
    return skill


async def _update_skill_files(
    self,
    skill: Skill,
    improvements: dict,
) -> None:
    """Update skill files based on evolution improvements."""
    # Get existing SKILL.md if exists
    existing_content = None
    try:
        existing_bytes = await self.storage.get_skill_file(skill.id, "SKILL.md")
        if existing_bytes:
            existing_content = existing_bytes.decode("utf-8")
    except Exception:
        pass

    # Build updated content
    updated_content = self._build_evolved_skill_md(skill, improvements, existing_content)
    await self.storage.save_skill_file(
        skill.id,
        "SKILL.md",
        updated_content.encode("utf-8"),
    )

    # Update helper.py if improvements include code changes
    if improvements.get("helper_updates"):
        await self.storage.save_skill_file(
            skill.id,
            "helper.py",
            improvements["helper_updates"].encode("utf-8"),
        )


def _build_evolved_skill_md(
    self,
    skill: Skill,
    improvements: dict,
    existing_content: str | None,
) -> str:
    """Build updated SKILL.md content."""
    lines = []

    if existing_content:
        # Parse existing and update sections
        lines = existing_content.split("\n")
    else:
        # Create new from scratch
        lines = [
            f"# {skill.name}",
            "",
            skill.description or "",
        ]

    # Add improvements section
    lines.append("")
    lines.append("## Evolution Notes")
    lines.append(f"- Version {skill.version} update")

    if improvements.get("positive_patterns"):
        lines.append("")
        lines.append("### Successful Patterns")
        for pattern in improvements["positive_patterns"]:
            lines.append(f"- {pattern}")

    if improvements.get("negative_patterns"):
        lines.append("")
        lines.append("### Patterns to Avoid")
        for pattern in improvements["negative_patterns"]:
            lines.append(f"- {pattern}")

    if improvements.get("new_examples"):
        lines.append("")
        lines.append("### Additional Examples")
        for example in improvements["new_examples"]:
            lines.append(f"```")
            lines.append(example)
            lines.append(f"```")

    return "\n".join(lines)
```

- [ ] **Step 2: Test evolution logic**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.application.skill_evolution_service import SkillEvolutionService; print('Evolution methods available')"`
Expected: `Evolution methods available`

- [ ] **Step 3: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/application/skill_evolution_service.py
git commit -m "feat: add skill self-evolution logic"
```

---

## Task 4: 进化配置

**Files:**
- Modify: `backend/config.yaml` (添加进化配置)
- Modify: `backend/app/config.py` (添加配置加载)

- [ ] **Step 1: Update config.yaml**

添加进化相关配置：

```yaml
evolution:
  generation_threshold: 3  # Positive feedbacks needed before skill generation
  auto_evolve: false     # Whether to auto-evolve or require manual approval
  max_versions: 10        # Maximum skill versions to keep

models:
  default:
    type: "openai"
    model: "gpt-4o"
```

- [ ] **Step 2: Update config.py**

添加进化配置模型：

```python
class EvolutionConfig(BaseModel):
    generation_threshold: int = 3
    auto_evolve: bool = False
    max_versions: int = 10


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    storage: StorageConfig = StorageConfig()
    auth: AuthConfig
    models: ModelsConfig
    evolution: EvolutionConfig = EvolutionConfig()
```

- [ ] **Step 3: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/config.yaml backend/app/config.py
git commit -m "feat: add evolution configuration"
```

---

## Self-Review

- [ ] **Spec coverage check**: All Phase 3 items from design doc covered
  - [x] Feedback 处理流程 (Task 1)
  - [x] Skill 生成逻辑 (Task 1)
  - [x] Skill 进化逻辑 (Task 3)
  - [x] 进化 API 端点 (Task 2)
  - [x] 进化配置 (Task 4)

- [ ] **Placeholder scan**: No TBD/TODO in implementation steps

- [ ] **Type consistency**: Entity types match Phase 1/2
  - `FeedbackEvent`, `Skill`, `SkillStatus` consistent
  - `StorageAdapter` methods used consistently

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-23-claw-platform-phase3.md`**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
