# 多轮对话记忆功能设计

## 概述

为 Agent 添加持久化记忆功能：每轮对话后异步生成摘要并存储，后续对话自动携带最近 10 轮记忆作为上下文。

## 核心流程

```
用户输入 → 取最近10轮记忆 → 拼接到输入前 → Agent生成 → 异步LLM摘要 → 存入数据库
```

## 数据模型

### ConversationMemory 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 主键 |
| agent_id | string | 关联的 Agent ID |
| user_input | text | 用户原始输入 |
| agent_output | text | Agent 输出（未经压缩） |
| summary | text | LLM 生成的摘要（500字内） |
| created_at | datetime | 创建时间 |

**索引**：`idx_agent_created` (agent_id, created_at DESC) —— 用于快速查询某 Agent 的最近 N 轮对话

## 实现步骤

### 1. 后端 - 数据模型

**文件**：`backend/app/domain/conversation_memory.py`

```python
class ConversationMemory(BaseModel):
    id: EntityId
    agent_id: EntityId
    user_input: str          # 原始用户输入
    agent_output: str        # Agent 完整输出
    summary: str              # LLM 摘要（500字内）
    created_at: datetime
```

**表结构**：创建 `conversation_memories` 表，迁移文件 `backend/migrations/xxxx_add_conversation_memories.py`

### 2. 后端 - API 接口

**文件**：`backend/app/api/conversation_memories.py`

| Method | Path | 说明 |
|--------|------|------|
| GET | /api/conversation-memories?agent_id=xxx | 获取某 Agent 的记忆（按 created_at DESC，limit 10） |
| POST | /api/conversation-memories | 存储一条记忆 |
| DELETE | /api/conversation-memories/{id} | 删除单条记忆 |
| DELETE | /api/conversation-memories?agent_id=xxx | 清空某 Agent 所有记忆 |

### 3. 后端 - 摘要生成（异步）

**文件**：`backend/app/application/conversation_memory_service.py`

新增 `summarize_and_store()` 方法：
1. 调用 LLM 生成摘要（prompt: "用500字以内总结以下对话的核心内容..."）
2. 存入数据库
3. 后端返回时触发，不阻塞主流程

**注意**：摘要生成失败时，记录 error log，不影响主流程，记忆仍可正常存储（summary 为空或降级处理）

### 4. 前端 - 调用时机

**文件**：`src/views/AgentDetailView.vue`

在 `handleRun()` 函数中，当收到 `done` 事件后：
```typescript
// 对话结束后，异步存储记忆
if (agentMessage.isComplete && currentSessionId.value) {
  storeConversationMemory({
    agent_id: agentId.value,
    user_input: taskInput.value,
    agent_output: agentMessage.content,
    session_id: currentSessionId.value
  })
}
```

### 5. 前端 - 上下文拼接

**文件**：`src/stores/agents.ts` 或 `AgentDetailView.vue`

在发起请求前，从 API 获取最近 10 轮记忆并拼接：
```typescript
const memories = await fetchMemories(agentId.value)
const historyContext = memories.map(m => `用户: ${m.user_input}\n助手: ${m.summary}`).join('\n\n')
const fullTask = historyContext ? `${historyContext}\n\n当前问题: ${taskInput.value}` : taskInput.value
```

### 6. 前端 - UI 可选改进

**文件**：`src/views/AgentDetailView.vue`

- 在输入框上方或折叠区域显示"记忆"图标，点击可查看/管理该 Agent 的历史记忆
- 提供"清空记忆"按钮

## 变更文件清单

```
backend/app/domain/conversation_memory.py     [新建]
backend/app/application/conversation_memory_service.py [新建]
backend/app/api/conversation_memories.py     [新建]
backend/migrations/xxxx_add_conversation_memories.py [新建]
backend/app/models/__init__.py               [修改 - 注册 model]
backend/app/api/main.py                      [修改 - 注册 router]

src/api/conversation_memories.ts             [新建]
src/stores/agents.ts                        [修改 - 添加记忆相关逻辑]
src/views/AgentDetailView.vue               [修改 - 存储记忆 & 拼接上下文]
```

## 错误处理

1. **摘要生成失败**：记录 log，不阻塞主流程，记忆仍存储（summary 为空）
2. **记忆获取失败**：降级为无记忆状态，正常发起对话
3. **记忆存储失败**：静默失败，不影响当前对话

## 测试场景

1. 连续 3 轮对话后，第 4 轮能正确获取前 3 轮记忆
2. 超过 10 轮后，只获取最近 10 轮
3. 页面刷新后记忆仍然存在
4. 异步摘要生成无感（用户无需等待）
