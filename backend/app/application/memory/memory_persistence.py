import logging
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    MEMORY_MD = "MEMORY.md"
    USER_MD = "USER.md"


class MemoryPersistence:
    """多文件持久化：MEMORY.md / USER.md"""

    def __init__(self, base_dir: Path = None):
        from app.config import settings
        if base_dir is None:
            base_dir = Path(settings.memory_storage_path)
        self.base_dir = Path(base_dir).expanduser()
        # Ensure base_dir exists
        self.base_dir.mkdir(parents=True, exist_ok=True)

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