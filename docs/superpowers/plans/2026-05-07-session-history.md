# 历史会话功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在侧边栏提供可折叠的全局会话列表，支持跨 Agent 统一管理、会话切换、新建、编辑名称、删除。

**Architecture:**
- 后端：新建 `SessionModel` 表（SQLAlchemy）+ RESTful API（FastAPI），与 LogModel 解耦
- 前端：新建 Pinia Store 管理会话状态 + 抽屉组件，集成到 AgentDetailView

**Tech Stack:** FastAPI (backend), Vue 3 + Pinia + TypeScript (frontend), SQLAlchemy (ORM)

---

## 文件结构

```
backend/
├── app/domain/session.py          # 新建：Session domain model
├── app/api/sessions.py            # 新建：Session API routes
├── app/application/session_service.py  # 新建：Session business logic
└── app/infrastructure/storage/sqlite.py  # 修改：添加 SessionModel + CRUD

src/
├── api/sessions.ts               # 新建：sessions API client
├── stores/sessions.ts            # 新建：sessions Pinia store
├── components/SessionsDrawer.vue  # 新建：可折叠抽屉组件
└── views/AgentDetailView.vue     # 修改：集成会话切换逻辑
```

---

## Task 1: 后端 - Domain Model

**Files:**
- Create: `backend/app/domain/session.py`
- Test: `backend/tests/test_session_model.py`

- [ ] **Step 1: 创建 Session domain model**

```python
# backend/app/domain/session.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.domain.base import EntityId

@dataclass
class Session:
    id: EntityId
    name: str
    agent_id: EntityId
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    @staticmethod
    def create(agent_id: str, name: Optional[str] = None) -> "Session":
        now = datetime.now(timezone.utc)
        return Session(
            id=EntityId.generate(),
            name=name or "",
            agent_id=EntityId(agent_id),
            created_at=now,
            updated_at=now,
            message_count=0,
        )
```

- [ ] **Step 2: 创建测试文件**

```python
# backend/tests/test_session_model.py
import pytest
from datetime import datetime, timezone
from app.domain.session import Session

def test_session_create():
    session = Session.create(agent_id="agent-123", name="Test Session")
    assert session.agent_id.value == "agent-123"
    assert session.name == "Test Session"
    assert session.message_count == 0
    assert session.created_at is not None

def test_session_create_without_name():
    session = Session.create(agent_id="agent-123")
    assert session.name == ""
```

- [ ] **Step 3: 运行测试验证**

Run: `cd backend && python -m pytest tests/test_session_model.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add backend/app/domain/session.py backend/tests/test_session_model.py
git commit -m "feat(backend): add Session domain model"
```

---

## Task 2: 后端 - SQLAlchemy Model

**Files:**
- Modify: `backend/app/infrastructure/storage/sqlite.py` (添加 SessionModel)
- Test: `backend/tests/test_session_storage.py`

- [ ] **Step 1: 在 sqlite.py 添加 SessionModel**

在 `LogModel` 后添加：

```python
class SessionModel(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_updated_at", "updated_at"),
    )

    id = Column(String(36), primary_key=True)
    name = Column(String(255), default="")
    agent_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    message_count = Column(Integer, default=0)
```

- [ ] **Step 2: 在 SQLiteStorage 类添加 `_to_session` 方法**

在 `_to_log` 方法后添加：

```python
def _to_session(self, row: SessionModel) -> Session:
    return Session(
        id=EntityId(row.id),
        name=row.name,
        agent_id=EntityId(row.agent_id),
        created_at=row.created_at,
        updated_at=row.updated_at,
        message_count=row.message_count,
    )
```

- [ ] **Step 3: 在 SQLiteStorage 类添加 Session CRUD 方法**

在 `query_logs` 方法后添加：

```python
async def save_session(self, session: Session) -> None:
    async with self.async_session() as sess:
        from sqlalchemy import select
        result = await sess.execute(
            select(SessionModel).where(SessionModel.id == session.id)
        )
        existing = result.scalar_one_or_none()

        model = SessionModel(
            id=session.id,
            name=session.name,
            agent_id=session.agent_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=session.message_count,
        )

        if existing:
            for key in ['name', 'updated_at', 'message_count']:
                setattr(existing, key, getattr(model, key))
        else:
            sess.add(model)
        await sess.commit()

async def get_session(self, id: str) -> Optional[Session]:
    async with self.async_session() as sess:
        from sqlalchemy import select
        result = await sess.execute(select(SessionModel).where(SessionModel.id == id))
        row = result.scalar_one_or_none()
        return self._to_session(row) if row else None

async def list_sessions(self, offset: int = 0, limit: int = 100) -> List[Session]:
    async with self.async_session() as sess:
        from sqlalchemy import select
        result = await sess.execute(
            select(SessionModel)
            .order_by(SessionModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [self._to_session(row) for row in result.scalars().all()]

async def delete_session(self, id: str) -> None:
    async with self.async_session() as sess:
        from sqlalchemy import delete
        await sess.execute(delete(SessionModel).where(SessionModel.id == id))
        await sess.commit()
```

- [ ] **Step 4: 创建存储层测试**

```python
# backend/tests/test_session_storage.py
import pytest
from app.infrastructure.storage.sqlite import SQLiteStorage

@pytest.fixture
async def storage():
    s = SQLiteStorage(":memory:")
    await s.init_db()
    yield s
    await s.close()

@pytest.mark.asyncio
async def test_save_and_get_session(storage):
    from app.domain.session import Session
    session = Session.create(agent_id="agent-1", name="Test")
    await storage.save_session(session)

    retrieved = await storage.get_session(session.id)
    assert retrieved is not None
    assert retrieved.name == "Test"
    assert retrieved.agent_id.value == "agent-1"

@pytest.mark.asyncio
async def test_list_sessions(storage):
    from app.domain.session import Session
    for i in range(3):
        s = Session.create(agent_id=f"agent-{i}", name=f"Session {i}")
        await storage.save_session(s)

    sessions = await storage.list_sessions()
    assert len(sessions) == 3
    assert sessions[0].name == "Session 2"  # 最新优先
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/test_session_storage.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/infrastructure/storage/sqlite.py backend/tests/test_session_storage.py
git commit -m "feat(backend): add SessionModel and CRUD operations"
```

---

## Task 3: 后端 - Application Service

**Files:**
- Create: `backend/app/application/session_service.py`
- Test: `backend/tests/test_session_service.py`

- [ ] **Step 1: 创建 SessionService**

```python
# backend/app/application/session_service.py
from typing import List, Optional
from app.domain.session import Session
from app.infrastructure.storage.base import StorageAdapter

class SessionService:
    def __init__(self, storage: StorageAdapter):
        self.storage = storage

    async def create_session(self, agent_id: str, name: Optional[str] = None) -> Session:
        session = Session.create(agent_id=agent_id, name=name)
        await self.storage.save_session(session)
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        return await self.storage.get_session(session_id)

    async def list_sessions(self, offset: int = 0, limit: int = 100) -> List[Session]:
        return await self.storage.list_sessions(offset=offset, limit=limit)

    async def update_session(self, session_id: str, name: str) -> Optional[Session]:
        session = await self.storage.get_session(session_id)
        if not session:
            return None
        session.name = name
        from datetime import datetime, timezone
        session.updated_at = datetime.now(timezone.utc)
        await self.storage.save_session(session)
        return session

    async def delete_session(self, session_id: str) -> None:
        await self.storage.delete_session(session_id)

    async def increment_message_count(self, session_id: str) -> None:
        session = await self.storage.get_session(session_id)
        if session:
            session.message_count += 1
            from datetime import datetime, timezone
            session.updated_at = datetime.now(timezone.utc)
            await self.storage.save_session(session)
```

- [ ] **Step 2: 创建测试**

```python
# backend/tests/test_session_service.py
import pytest
from app.application.session_service import SessionService

@pytest.mark.asyncio
async def test_create_session(storage):
    service = SessionService(storage)
    session = await service.create_session(agent_id="agent-1", name="My Session")
    assert session.name == "My Session"
    assert session.agent_id.value == "agent-1"
    assert session.message_count == 0

@pytest.mark.asyncio
async def test_update_session_name(storage):
    service = SessionService(storage)
    session = await service.create_session(agent_id="agent-1")
    updated = await service.update_session(session.id, name="New Name")
    assert updated is not None
    assert updated.name == "New Name"

@pytest.mark.asyncio
async def test_increment_message_count(storage):
    service = SessionService(storage)
    session = await service.create_session(agent_id="agent-1")
    await service.increment_message_count(session.id)
    updated = await service.get_session(session.id)
    assert updated is not None
    assert updated.message_count == 1
```

- [ ] **Step 3: 运行测试**

Run: `cd backend && python -m pytest tests/test_session_service.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add backend/app/application/session_service.py backend/tests/test_session_service.py
git commit -m "feat(backend): add SessionService with business logic"
```

---

## Task 4: 后端 - API Routes

**Files:**
- Create: `backend/app/api/sessions.py`
- Modify: `backend/app/api/__init__.py` (注册 router)
- Test: `backend/tests/test_sessions_api.py`

- [ ] **Step 1: 创建 sessions API**

```python
# backend/app/api/sessions.py
"""Session API routes."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import Storage
from app.application.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionResponse(BaseModel):
    id: str
    name: str
    agent_id: str
    created_at: str
    updated_at: str
    message_count: int

    @classmethod
    def from_session(cls, session) -> "SessionResponse":
        return cls(
            id=session.id,
            name=session.name,
            agent_id=session.agent_id,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=session.message_count,
        )


class CreateSessionRequest(BaseModel):
    agent_id: str
    name: Optional[str] = None


class UpdateSessionRequest(BaseModel):
    name: str


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    storage: Storage,
    offset: int = 0,
    limit: int = 100,
) -> List[SessionResponse]:
    """List all sessions, ordered by updated_at desc."""
    service = SessionService(storage)
    sessions = await service.list_sessions(offset=offset, limit=limit)
    return [SessionResponse.from_session(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    storage: Storage,
) -> SessionResponse:
    """Get a single session by ID."""
    service = SessionService(storage)
    session = await service.get_session(session_id)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.from_session(session)


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    storage: Storage,
) -> SessionResponse:
    """Create a new session."""
    service = SessionService(storage)
    session = await service.create_session(agent_id=request.agent_id, name=request.name)
    return SessionResponse.from_session(session)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    storage: Storage,
) -> SessionResponse:
    """Update session name."""
    service = SessionService(storage)
    session = await service.update_session(session_id, name=request.name)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse.from_session(session)


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    storage: Storage,
) -> dict:
    """Delete a session."""
    service = SessionService(storage)
    await service.delete_session(session_id)
    return {"ok": True}
```

- [ ] **Step 2: 在 api/__init__.py 注册 router**

找到 `__init__.py` 中的 router 注册部分，添加：
```python
from app.api.sessions import router as sessions_router
router.include_router(sessions_router)
```

- [ ] **Step 3: 创建 API 测试**

```python
# backend/tests/test_sessions_api.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from main import app
    return TestClient(app)

def test_create_session(client):
    response = client.post("/sessions", json={"agent_id": "agent-1", "name": "Test"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test"
    assert data["agent_id"] == "agent-1"

def test_list_sessions(client):
    response = client.get("/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_session(client):
    # 先创建
    create_resp = client.post("/sessions", json={"agent_id": "agent-1"})
    session_id = create_resp.json()["id"]
    # 再更新
    response = client.patch(f"/sessions/{session_id}", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"

def test_delete_session(client):
    create_resp = client.post("/sessions", json={"agent_id": "agent-1"})
    session_id = create_resp.json()["id"]
    response = client.delete(f"/sessions/{session_id}")
    assert response.status_code == 200
    # 验证删除
    get_resp = client.get(f"/sessions/{session_id}")
    assert get_resp.status_code == 404
```

- [ ] **Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/test_sessions_api.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/sessions.py backend/app/api/__init__.py backend/tests/test_sessions_api.py
git commit -m "feat(backend): add Session API routes"
```

---

## Task 5: 前端 - API Client

**Files:**
- Create: `src/api/sessions.ts`

- [ ] **Step 1: 创建 sessions API client**

```typescript
// src/api/sessions.ts
import client from './client'

export interface Session {
  id: string
  name: string
  agent_id: string
  created_at: string
  updated_at: string
  message_count: number
}

export const sessionsApi = {
  async list(): Promise<Session[]> {
    const { data } = await client.get('/sessions')
    return data
  },

  async get(id: string): Promise<Session> {
    const { data } = await client.get(`/sessions/${id}`)
    return data
  },

  async create(agentId: string, name?: string): Promise<Session> {
    const { data } = await client.post('/sessions', { agent_id: agentId, name })
    return data
  },

  async update(id: string, name: string): Promise<Session> {
    const { data } = await client.patch(`/sessions/${id}`, { name })
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/sessions/${id}`)
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add src/api/sessions.ts
git commit -m "feat(frontend): add sessions API client"
```

---

## Task 6: 前端 - Sessions Store

**Files:**
- Create: `src/stores/sessions.ts`

- [ ] **Step 1: 创建 sessions Pinia store**

参考 `stores/logs.ts` 的模式：

```typescript
// src/stores/sessions.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Session } from '@/api/sessions'
import { sessionsApi } from '@/api/sessions'

export const useSessionsStore = defineStore('sessions', () => {
  const sessions = ref<Session[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSessions(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      sessions.value = await sessionsApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch sessions'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createSession(agentId: string, name?: string): Promise<Session> {
    const session = await sessionsApi.create(agentId, name)
    sessions.value.unshift(session)
    return session
  }

  async function updateSession(id: string, name: string): Promise<void> {
    const updated = await sessionsApi.update(id, name)
    const idx = sessions.value.findIndex(s => s.id === id)
    if (idx !== -1) {
      sessions.value[idx] = updated
    }
  }

  async function deleteSession(id: string): Promise<void> {
    await sessionsApi.delete(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
  }

  return {
    sessions,
    loading,
    error,
    fetchSessions,
    createSession,
    updateSession,
    deleteSession
  }
})
```

- [ ] **Step 2: 提交**

```bash
git add src/stores/sessions.ts
git commit -m "feat(frontend): add sessions Pinia store"
```

---

## Task 7: 前端 - SessionsDrawer 组件

**Files:**
- Create: `src/components/SessionsDrawer.vue`

- [ ] **Step 1: 创建抽屉组件**

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSessionsStore } from '@/stores/sessions'
import IconButton from '@/components/ui/IconButton.vue'
import Input from '@/components/ui/Input.vue'

const props = defineProps<{
  open: boolean
  agentId: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', sessionId: string): void
}>()

const sessionsStore = useSessionsStore()
const editingId = ref<string | null>(null)
const editingName = ref('')

watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    await sessionsStore.fetchSessions()
  }
})

function formatTime(isoString: string): string {
  const d = new Date(isoString)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return d.toLocaleDateString()
}

function getDisplayName(session: { name: string; message_count: number }): string {
  if (session.name) return session.name
  return session.message_count > 0 ? '新会话' : '空会话'
}

async function handleNewSession() {
  const session = await sessionsStore.createSession(props.agentId)
  emit('select', session.id)
  emit('close')
}

function handleSelect(sessionId: string) {
  emit('select', sessionId)
  emit('close')
}

function startEdit(id: string, currentName: string) {
  editingId.value = id
  editingName.value = currentName
}

async function saveEdit(id: string) {
  if (editingName.value.trim()) {
    await sessionsStore.updateSession(id, editingName.value.trim())
  }
  editingId.value = null
}

async function handleDelete(id: string) {
  await sessionsStore.deleteSession(id)
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="drawer-overlay" @click="emit('close')" />
    <div :class="['drawer', { open }]">
      <div class="drawer-header">
        <span class="drawer-title">会话历史</span>
        <IconButton icon="close" @click="emit('close')" />
      </div>

      <div class="drawer-content">
        <button class="new-session-btn" @click="handleNewSession">
          + 新建会话
        </button>

        <div class="sessions-list">
          <div
            v-for="session in sessionsStore.sessions"
            :key="session.id"
            class="session-item"
          >
            <template v-if="editingId === session.id">
              <Input
                v-model="editingName"
                class="edit-input"
                @keyup.enter="saveEdit(session.id)"
                @blur="saveEdit(session.id)"
                @keyup.escape="editingId = null"
                autofocus
              />
            </template>
            <template v-else>
              <div class="session-info" @click="handleSelect(session.id)">
                <span class="session-name">{{ getDisplayName(session) }}</span>
                <span class="session-time">{{ formatTime(session.updated_at) }}</span>
              </div>
              <div class="session-actions">
                <IconButton
                  icon="edit"
                  size="small"
                  @click.stop="startEdit(session.id, session.name)"
                />
                <IconButton
                  icon="delete"
                  size="small"
                  @click.stop="handleDelete(session.id)"
                />
              </div>
            </template>
          </div>

          <div v-if="sessionsStore.sessions.length === 0" class="empty-state">
            暂无会话记录
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 320px;
  height: 100vh;
  background: var(--color-surface);
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.2s ease;
  z-index: 101;
  display: flex;
  flex-direction: column;
}

.drawer.open {
  transform: translateX(0);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
}

.drawer-title {
  font-weight: 600;
}

.drawer-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.new-session-btn {
  width: 100%;
  padding: 10px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 16px;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--color-background);
}

.session-item:hover .session-actions {
  opacity: 1;
}

.session-info {
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.session-name {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.session-time {
  display: block;
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

.session-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.edit-input {
  flex: 1;
}

.empty-state {
  text-align: center;
  color: var(--color-text-muted);
  padding: 24px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/SessionsDrawer.vue
git commit -m "feat(frontend): add SessionsDrawer component"
```

---

## Task 8: 前端 - 集成到 AgentDetailView

**Files:**
- Modify: `src/views/AgentDetailView.vue`

- [ ] **Step 1: 添加抽屉状态和图标按钮**

在 script setup 区域添加：

```typescript
import SessionsDrawer from '@/components/SessionsDrawer.vue'

const drawerOpen = ref(false)

function openSessionsDrawer() {
  drawerOpen.value = true
}

function handleSessionSelect(sessionId: string) {
  currentSessionId.value = sessionId
  setStoredSessionId(agentId.value, sessionId)
  // 清空消息，重新加载该会话的日志
  messages.value = []
  // TODO: 从日志 API 加载该 session 的历史消息
  loadSessionMessages(sessionId)
}
```

- [ ] **Step 2: 在模板中添加抽屉触发按钮**

在顶部操作区域添加一个图标按钮（搜索 `Card header` 或类似结构）：

```html
<IconButton icon="history" @click="openSessionsDrawer" title="会话历史" />
```

- [ ] **Step 3: 在模板底部添加抽屉组件**

```html
<SessionsDrawer
  :open="drawerOpen"
  :agent-id="agentId"
  @close="drawerOpen = false"
  @select="handleSessionSelect"
/>
```

- [ ] **Step 4: 提交**

```bash
git add src/views/AgentDetailView.vue
git commit -m "feat(frontend): integrate SessionsDrawer into AgentDetailView"
```

---

## Task 9: 端到端测试

**Files:**
- 测试：创建会话 → 切换会话 → 编辑名称 → 删除

- [ ] **Step 1: 手动测试流程**

1. 启动后端服务：`cd backend && uvicorn main:app --reload`
2. 启动前端服务：`cd src && npm run dev`
3. 打开浏览器，进入 Agent 详情页
4. 点击"会话历史"图标，抽屉正常展开
5. 点击"新建会话"，确认新会话创建并切换
6. 在会话列表中 hover，编辑/删除按钮出现
7. 编辑会话名称，确认保存成功
8. 删除会话，确认列表更新

- [ ] **Step 2: 提交全部改动**

```bash
git add -A
git commit -m "feat: add session history feature - global session list with drawer UI"
```

---

## 依赖关系

```
Task 1 (Domain Model)
    ↓
Task 2 (SQLAlchemy Model) ← Task 1
    ↓
Task 3 (Service) ← Task 2
    ↓
Task 4 (API) ← Task 3
    ↓
Task 5 (Frontend API) ← Task 4 (API 完成)
    ↓
Task 6 (Store) ← Task 5
    ↓
Task 7 (Drawer) ← Task 6
    ↓
Task 8 (Integration) ← Task 7
    ↓
Task 9 (E2E Test)
```
