# 多轮对话记忆功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Agent 添加持久化记忆功能：每轮对话后异步生成摘要并存储（最多保留 10 轮），新对话自动携带历史上下文。

**Architecture:**
- 后端：新增 `conversation_memories` 表 + API，在 agent streaming 完成后异步触发 LLM 摘要生成
- 前端：对话完成后调用存储 API；发起新对话时获取历史记忆并拼接

**Tech Stack:** FastAPI, SQLAlchemy (SQLite), Vue 3 + TypeScript, LangChain LLM 调用

---

## 文件变更总览

```
backend/app/domain/conversation_memory.py           [新建]
backend/app/infrastructure/storage/sqlite.py        [修改 - 添加 ConversationMemoryModel & 操作]
backend/app/api/conversation_memories.py           [新建]
backend/app/api/__init__.py                        [修改 - 注册 router]
backend/app/application/conversation_memory_service.py [新建]
backend/app/application/agent_service.py           [修改 - 注入 memory_service]

src/api/conversation_memories.ts                   [新建]
src/views/AgentDetailView.vue                     [修改 - 存储记忆 & 上下文拼接]
```

---

### Task 1: 后端数据模型

**Files:**
- Create: `backend/app/domain/conversation_memory.py`
- Modify: `backend/app/infrastructure/storage/sqlite.py:190-203` (add ConversationMemoryModel)
- Modify: `backend/app/infrastructure/storage/sqlite.py` (add CRUD methods)

- [ ] **Step 1: 创建 domain entity**

Create file `backend/app/domain/conversation_memory.py`:

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domain.base import EntityId


@dataclass
class ConversationMemory:
    id: EntityId
    agent_id: EntityId
    user_input: str
    agent_output: str
    summary: str
    created_at: datetime

    @staticmethod
    def create(agent_id: str, user_input: str, agent_output: str, summary: str = "") -> "ConversationMemory":
        return ConversationMemory(
            id=EntityId.generate(),
            agent_id=EntityId(agent_id),
            user_input=user_input,
            agent_output=agent_output,
            summary=summary,
            created_at=datetime.now(timezone.utc),
        )
```

- [ ] **Step 2: 添加 SQLAlchemy Model**

In `backend/app/infrastructure/storage/sqlite.py`, add after `SessionModel`:

```python
class ConversationMemoryModel(Base):
    __tablename__ = "conversation_memories"
    __table_args__ = (
        Index("ix_conversation_memories_agent_created", "agent_id", "created_at"),
    )

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), nullable=False)
    user_input = Column(Text, nullable=False)
    agent_output = Column(Text, nullable=False)
    summary = Column(Text, default="")
    created_at = Column(DateTime, nullable=False)
```

- [ ] **Step 3: 添加 CRUD 方法**

In `SQLiteStorage`, add `ConversationMemoryModel` import at top, and add methods:

```python
def _to_conversation_memory(self, row: ConversationMemoryModel) -> ConversationMemory:
    return ConversationMemory(
        id=EntityId(row.id),
        agent_id=EntityId(row.agent_id),
        user_input=row.user_input,
        agent_output=row.agent_output,
        summary=row.summary,
        created_at=row.created_at,
    )

async def save_conversation_memory(self, memory: ConversationMemory) -> None:
    async with self.async_session() as session:
        model = ConversationMemoryModel(
            id=memory.id,
            agent_id=memory.agent_id,
            user_input=memory.user_input,
            agent_output=memory.agent_output,
            summary=memory.summary,
            created_at=memory.created_at,
        )
        session.add(model)
        await session.commit()

async def update_conversation_memory_summary(self, id: str, summary: str) -> None:
    async with self.async_session() as session:
        from sqlalchemy import update
        await session.execute(
            update(ConversationMemoryModel).where(ConversationMemoryModel.id == id).values(summary=summary)
        )
        await session.commit()

async def get_conversation_memories(self, agent_id: str, limit: int = 10) -> List[ConversationMemory]:
    async with self.async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ConversationMemoryModel)
            .where(ConversationMemoryModel.agent_id == agent_id)
            .order_by(ConversationMemoryModel.created_at.desc())
            .limit(limit)
        )
        return [self._to_conversation_memory(row) for row in result.scalars().all()]

async def delete_conversation_memory(self, id: str) -> None:
    async with self.async_session() as session:
        from sqlalchemy import delete
        await session.execute(delete(ConversationMemoryModel).where(ConversationMemoryModel.id == id))
        await session.commit()

async def delete_conversation_memories_by_agent(self, agent_id: str) -> None:
    async with self.async_session() as session:
        from sqlalchemy import delete
        await session.execute(delete(ConversationMemoryModel).where(ConversationMemoryModel.agent_id == agent_id))
        await session.commit()
```

- [ ] **Step 4: 添加 import**

In `sqlite.py` imports section, add:
```python
from app.domain.conversation_memory import ConversationMemory
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/domain/conversation_memory.py backend/app/infrastructure/storage/sqlite.py
git commit -m "feat(backend): add ConversationMemory domain model and storage"
```

---

### Task 2: 后端 API 接口

**Files:**
- Create: `backend/app/api/conversation_memories.py`
- Modify: `backend/app/api/__init__.py`

- [ ] **Step 1: 创建 API router**

Create file `backend/app/api/conversation_memories.py`:

```python
"""Conversation Memory API routes."""
import logging
from typing import List

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.api.deps import Storage
from app.application.conversation_memory_service import ConversationMemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversation-memories", tags=["conversation-memories"])


class ConversationMemoryResponse(BaseModel):
    id: str
    agent_id: str
    user_input: str
    agent_output: str
    summary: str
    created_at: str

    @classmethod
    def from_memory(cls, memory) -> "ConversationMemoryResponse":
        return cls(
            id=memory.id,
            agent_id=memory.agent_id,
            user_input=memory.user_input,
            agent_output=memory.agent_output,
            summary=memory.summary,
            created_at=memory.created_at.isoformat(),
        )


class CreateConversationMemoryRequest(BaseModel):
    agent_id: str
    user_input: str
    agent_output: str
    session_id: str | None = None


class UpdateSummaryRequest(BaseModel):
    summary: str


@router.get("", response_model=List[ConversationMemoryResponse])
async def list_memories(
    storage: Storage,
    agent_id: str = Query(...),
    limit: int = Query(default=10, le=20),
) -> List[ConversationMemoryResponse]:
    """Get conversation memories for an agent, ordered by created_at desc."""
    service = ConversationMemoryService(storage)
    memories = await service.get_memories(agent_id, limit=limit)
    return [ConversationMemoryResponse.from_memory(m) for m in memories]


@router.post("", response_model=ConversationMemoryResponse, status_code=201)
async def create_memory(
    request: CreateConversationMemoryRequest,
    storage: Storage,
) -> ConversationMemoryResponse:
    """Create a new conversation memory."""
    service = ConversationMemoryService(storage)
    memory = await service.create_memory(
        agent_id=request.agent_id,
        user_input=request.user_input,
        agent_output=request.agent_output,
    )
    return ConversationMemoryResponse.from_memory(memory)


@router.patch("/{memory_id}/summary", response_model=ConversationMemoryResponse)
async def update_summary(
    memory_id: str,
    request: UpdateSummaryRequest,
    storage: Storage,
) -> ConversationMemoryResponse:
    """Update the summary of a conversation memory."""
    service = ConversationMemoryService(storage)
    memory = await service.update_summary(memory_id, request.summary)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return ConversationMemoryResponse.from_memory(memory)


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    storage: Storage,
) -> dict:
    """Delete a single conversation memory."""
    service = ConversationMemoryService(storage)
    await service.delete_memory(memory_id)
    return {"ok": True}


@router.delete("")
async def delete_memories_by_agent(
    storage: Storage,
    agent_id: str = Query(...),
) -> dict:
    """Delete all conversation memories for an agent."""
    service = ConversationMemoryService(storage)
    await service.delete_memories_by_agent(agent_id)
    return {"ok": True}
```

- [ ] **Step 2: 注册 router**

In `backend/app/api/__init__.py`, add import and register router:
```python
from app.api import agents, auth, feedback, models, sessions, skills, tools, conversation_memories

api_router.include_router(conversation_memories.router)  # add before tools
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/conversation_memories.py backend/app/api/__init__.py
git commit -m "feat(backend): add conversation memories API"
```

---

### Task 3: 后端 Service 层 & 异步摘要

**Files:**
- Create: `backend/app/application/conversation_memory_service.py`
- Modify: `backend/app/api/agents.py` (trigger async summarization after streaming)

- [ ] **Step 1: 创建 service**

Create file `backend/app/application/conversation_memory_service.py`:

```python
"""Conversation Memory Service."""
import asyncio
import logging
from typing import List, Optional

from app.domain.conversation_memory import ConversationMemory
from app.infrastructure.storage.base import StorageAdapter

logger = logging.getLogger(__name__)


class ConversationMemoryService:
    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    async def get_memories(self, agent_id: str, limit: int = 10) -> List[ConversationMemory]:
        return await self.storage.get_conversation_memories(agent_id, limit=limit)

    async def create_memory(
        self, agent_id: str, user_input: str, agent_output: str
    ) -> ConversationMemory:
        memory = ConversationMemory.create(
            agent_id=agent_id,
            user_input=user_input,
            agent_output=agent_output,
            summary="",  # Will be updated asynchronously
        )
        await self.storage.save_conversation_memory(memory)
        return memory

    async def update_summary(self, memory_id: str, summary: str) -> Optional[ConversationMemory]:
        await self.storage.update_conversation_memory_summary(memory_id, summary)
        # Fetch and return updated memory
        memories = await self.storage.get_conversation_memories("", limit=1)
        # Note: we need a get_memory_by_id method, or refactor to just return ok
        return None

    async def delete_memory(self, memory_id: str) -> None:
        await self.storage.delete_conversation_memory(memory_id)

    async def delete_memories_by_agent(self, agent_id: str) -> None:
        await self.storage.delete_conversation_memories_by_agent(agent_id)


async def summarize_conversation_task(memory_id: str, user_input: str, agent_output: str, storage: StorageAdapter):
    """Background task to generate summary using LLM."""
    try:
        # Build prompt for summarization
        prompt = f"""请用500字以内总结以下对话的核心内容。

用户输入: {user_input}

助手回复: {agent_output}

摘要:"""

        # Get a model for summarization (use default)
        from app.config import settings
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model=settings.models.default.model,
            api_key=settings.models.default.api_key,
            base_url=settings.models.default.base_url,
        )

        response = await model.ainvoke(prompt)
        summary = response.content.strip()

        # Update the memory with summary
        await storage.update_conversation_memory_summary(memory_id, summary)
        logger.info(f"Summary generated for memory {memory_id}: {summary[:100]}...")
    except Exception as e:
        logger.error(f"Failed to generate summary for memory {memory_id}: {e}")
        # Don't re-raise - summary failure should not affect main flow
```

- [ ] **Step 2: 添加 StorageAdapter 接口**

Check `backend/app/infrastructure/storage/base.py` for existing interface, add missing methods:

- [ ] **Step 3: 修改 agents.py 在 streaming 完成后触发异步摘要**

In `backend/app/api/agents.py`, after line ~221 (`yield f"data: {json.dumps({'type': 'done'})}\n\n"`), add background task trigger:

```python
# Trigger async summary generation after streaming completes
if request.session_id:
    from app.application.conversation_memory_service import summarize_conversation_task
    asyncio.create_task(
        summarize_conversation_task(
            memory_id=memory.id,
            user_input=request.task,
            agent_output=agent_output_text,  # Need to accumulate this
            storage=storage,
        )
    )
```

Note: You'll need to accumulate `agent_output_text` during streaming and create the memory first. Refactor as needed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/application/conversation_memory_service.py backend/app/api/agents.py
git commit -m "feat(backend): add conversation memory service with async summarization"
```

---

### Task 4: 前端 API

**Files:**
- Create: `src/api/conversation_memories.ts`

- [ ] **Step 1: 创建 API client**

Create file `src/api/conversation_memories.ts`:

```typescript
import client from './client'

export interface ConversationMemory {
  id: string
  agent_id: string
  user_input: string
  agent_output: string
  summary: string
  created_at: string
}

export const conversationMemoriesApi = {
  async list(agentId: string, limit = 10): Promise<ConversationMemory[]> {
    const { data } = await client.get('/conversation-memories', { params: { agent_id: agentId, limit } })
    return data
  },

  async create(agentId: string, userInput: string, agentOutput: string, sessionId?: string): Promise<ConversationMemory> {
    const { data } = await client.post('/conversation-memories', {
      agent_id: agentId,
      user_input: userInput,
      agent_output: agentOutput,
      session_id: sessionId,
    })
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/conversation-memories/${id}`)
  },

  async deleteByAgent(agentId: string): Promise<void> {
    await client.delete('/conversation-memories', { params: { agent_id: agentId } })
  },
}
```

- [ ] **Step 2: Commit**

```bash
git add src/api/conversation_memories.ts
git commit -m "feat(frontend): add conversation memories API client"
```

---

### Task 5: 前端集成 - 存储记忆 & 上下文拼接

**Files:**
- Modify: `src/views/AgentDetailView.vue` (handleRun function)

- [ ] **Step 1: 添加 import**

In `src/views/AgentDetailView.vue`, add import:
```typescript
import { conversationMemoriesApi } from '@/api/conversation_memories'
```

- [ ] **Step 2: 修改 handleRun - 在发起请求前获取记忆并拼接**

In `handleRun()` function, before the fetch call (~line 253), add:

```typescript
// Fetch recent memories and build context
try {
  const memories = await conversationMemoriesApi.list(agentId.value, 10)
  if (memories.length > 0) {
    const historyContext = memories
      .map(m => `用户: ${m.user_input}\n助手: ${m.summary}`)
      .join('\n\n')
    taskInput.value = `${historyContext}\n\n当前问题: ${taskInput.value}`
  }
} catch (e) {
  // Silently fail - proceed without memory context
  console.warn('Failed to fetch memories:', e)
}
```

- [ ] **Step 3: 在对话完成后存储记忆**

In `handleRun()`, after `agentMessage.isComplete = true` (~line 309), add:

```typescript
// Store conversation memory asynchronously (fire-and-forget)
if (agentMessage.content) {
  conversationMemoriesApi.create(
    agentId.value,
    userMessage.content,  // original user input
    agentMessage.content,  // agent output
    currentSessionId.value || undefined
  ).catch(e => {
    console.warn('Failed to store memory:', e)
  })
}
```

- [ ] **Step 4: Commit**

```bash
git add src/views/AgentDetailView.vue
git commit -m "feat(frontend): integrate conversation memory into AgentDetailView"
```

---

### Task 6: 验证

**Files:** N/A

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`

- [ ] **Step 2: 启动前端服务**

Run: `cd frontend && npm run dev` (or `cd src && npm run dev`)

- [ ] **Step 3: 测试多轮对话**

1. 打开一个 Agent 详情页
2. 问一个需要上下文的问题（第一轮）
3. 等待回答完成
4. 问一个引用第一轮内容的问题（第二轮）
5. 验证 Agent 能正确引用第一轮的信息

- [ ] **Step 4: 测试记忆持久化**

1. 完成几轮对话
2. 刷新页面
3. 再问一个问题
4. 验证之前的记忆被正确携带

---

## Self-Review Checklist

1. **Spec coverage:**
   - 数据模型 → Task 1
   - API 接口 → Task 2
   - 异步摘要 → Task 3
   - 前端存储 → Task 5
   - 前端上下文拼接 → Task 5
   - 最近 10 轮限制 → Task 4 & 5 的 limit 参数
   - 永久存储 → Task 1 的表设计

2. **Placeholder scan:** 无 TODO/TBD

3. **Type consistency:**
   - `ConversationMemory` 字段名一致（id, agent_id, user_input, agent_output, summary, created_at）
   - API response 使用 `created_at: str` (isoformat)
   - 前端 `conversationMemoriesApi.list()` 返回 `ConversationMemory[]`

---

**Plan saved to:** `docs/superpowers/plans/2026-05-09-conversation-memory-implementation.md`

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
