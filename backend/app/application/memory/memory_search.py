import logging
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    memory_type: str  # "MEMORY.md" | "USER.md"
    content: str
    relevance_score: float
    agent_id: str
    session_id: Optional[str]
    created_at: str


class MemorySearch:
    """基于 FTS5 的跨会话记忆搜索"""

    def __init__(self, storage):
        self.storage = storage

    async def index_memory(
        self,
        agent_id: str,
        memory_type: str,
        content: str,
        session_id: Optional[str] = None,
    ) -> None:
        """索引一条记忆到 FTS5 表"""
        await self.storage.index_memory(
            agent_id=agent_id,
            memory_type=memory_type,
            content=content,
            session_id=session_id or "",
            created_at=datetime.now().isoformat(),
        )

    async def search(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
    ) -> List[SearchResult]:
        """搜索记忆

        Args:
            agent_id: Agent ID
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            搜索结果列表，按相关性排序
        """
        results = await self.storage.search_memories(
            agent_id=agent_id,
            query=query,
            limit=limit,
        )
        return [
            SearchResult(
                memory_type=r["memory_type"],
                content=r["content"],
                relevance_score=r["rank"],
                agent_id=r["agent_id"],
                session_id=r.get("session_id"),
                created_at=r["created_at"],
            )
            for r in results
        ]

    async def reindex_all_memories(self, agent_id: str) -> int:
        """重新索引指定 Agent 的所有记忆

        从 MEMORY.md 和 USER.md 文件读取内容并重建 FTS5 索引
        """
        from app.application.memory.memory_persistence import MemoryPersistence, MemoryType

        persistence = MemoryPersistence()

        # 读取所有记忆
        memories = await persistence.get_all_memories(agent_id)

        count = 0
        for memory_type, content in memories.items():
            if content.strip():
                await self.index_memory(
                    agent_id=agent_id,
                    memory_type=memory_type,
                    content=content,
                    session_id=None,
                )
                count += 1

        logger.info(f"Reindexed {count} memories for agent {agent_id}")
        return count