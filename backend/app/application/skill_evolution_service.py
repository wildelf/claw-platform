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
        if skill.metadata is None:
            skill.metadata = {}
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
            "```",
            f"{feedback.result[:500]}",
            "```",
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