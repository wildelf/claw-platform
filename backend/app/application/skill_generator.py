"""Skill generator - auto-create skills from conversation experience."""

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
            if hasattr(self.storage, 'get_conversation_memories'):
                memories = await self.storage.get_conversation_memories(
                    agent_id=agent_id,
                    session_id=session_id,
                    limit=5,
                )
            else:
                memories = []

            # 生成 SKILL.md 内容
            skill_md = self._generate_skill_md(
                skill_name=skill_name,
                description=description,
                memories=memories,
            )

            # 创建技能实体
            from app.domain.base import EntityId
            skill = Skill(
                id=EntityId.generate(),
                name=skill_name,
                description=description,
                path=f"skills_cache/{skill_name}",
                status=SkillStatus.TRAINED,
                feedback_count=0,
                version=1,
                metadata={"auto_created": True},
                user_id=EntityId(agent_id),
            )

            await self.storage.save_skill(skill)

            # 保存 SKILL.md 文件
            if hasattr(self.storage, 'save_skill_file'):
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
        memories: list,
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