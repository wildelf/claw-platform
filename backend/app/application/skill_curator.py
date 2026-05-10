import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def bump_use(skill_name: str) -> None:
    """原子递增技能使用计数"""
    from app.config import settings
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

        from app.config import settings
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
            from app.domain.skill import SkillStatus
            skill.status = SkillStatus.EVOLVED  # Use EVOLVED as proxy for stale
            await self.storage.save_skill(skill)
            return "marked_stale"

        return "active"

    async def _archive_skill(self, skill) -> None:
        """归档技能到 .archive/"""
        from app.config import settings
        archive_dir = Path(settings.skills_cache_path) / ".archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        skill_dir = Path(settings.skills_cache_path) / skill.name
        if skill_dir.exists():
            import shutil
            shutil.move(str(skill_dir), str(archive_dir / skill.name))

        from app.domain.skill import SkillStatus
        skill.status = SkillStatus.NEEDS_REVIEW  # Use NEEDS_REVIEW as proxy for archived
        await self.storage.save_skill(skill)
        logger.info(f"Archived skill {skill.name}")