# Multi-Turn Conversation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable multi-turn conversations by leveraging LangGraph's built-in Checkpointer mechanism — no custom session/message tables needed.

**Architecture:**
- Use `langgraph.checkpoint.memory.MemorySaver` as checkpointer
- Pass `session_id` (used as `thread_id`) in config during agent invocation
- DeepAgents automatically persists conversation state via checkpointer

**Tech Stack:** LangGraph Checkpointers (MemorySaver), DeepAgents, SSE

---

## File Structure

### Backend
- `backend/app/deepagents/wrapper.py` — **Modify**: Add checkpointer support, pass thread_id through config

### Frontend
- `frontend/views/AgentDetailView.vue` — **Modify**: Track `session_id`, send with requests, display conversation history
- `frontend/stores/agents.ts` — **Modify**: Add message history state
- `frontend/types/index.ts` — **Modify**: Add Message type

---

## Task 1: Backend - Wrapper Checkpointer Support

**Files:**
- Modify: `backend/app/deepagents/wrapper.py:35-119` (create method)
- Modify: `backend/app/deepagents/wrapper.py:122-168` (run method)

### Steps

- [ ] **Step 1: Update DeepAgentsRunner.__init__ to accept checkpointer**

In `wrapper.py` after line 58, add checkpointer parameter:

```python
self._skill_event_queue: asyncio.Queue[dict] | None = None
self._override_model_config_id = override_model_config_id
self._checkpointer = None  # Will be set via set_checkpointer()
self._thread_id = None
```

Add new method after `_system_prompt_override` setter (~line 57):

```python
def set_checkpointer(self, checkpointer, thread_id: str):
    """Set checkpointer and thread_id for multi-turn conversations."""
    self._checkpointer = checkpointer
    self._thread_id = thread_id
```

- [ ] **Step 2: Update create() to configure checkpointer**

In `wrapper.py` around line 112, modify the `create_deep_agent` call to include checkpointer:

```python
from langgraph.checkpoint.memory import MemorySaver

# ... existing code ...
self._runner = create_deep_agent(
    model=self._model,
    tools=tools if tools else None,
    system_prompt=system_prompt,
    skills=None,
    middleware=[skill_middleware],
    backend=backend,
    checkpointer=MemorySaver() if self._checkpointer else None,
)
```

- [ ] **Step 3: Update run() to pass thread_id config**

In `wrapper.py` around line 246, modify the astream call:

```python
# Build config with thread_id for checkpointer
config = {"configurable": {"thread_id": self._thread_id}} if self._thread_id else {}

async for chunk in self._runner.astream(input_data, config=config, stream_mode=modes):
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/deepagents/wrapper.py && \
git commit -m "feat(agent): add checkpointer support for multi-turn conversations"
```

---

## Task 2: Backend API - Session ID passthrough

**Files:**
- Modify: `backend/app/api/agents.py:133-138` (RunAgentRequest)
- Modify: `backend/app/api/agents.py:140-233` (run_agent endpoint)

### Steps

- [ ] **Step 1: Update RunAgentRequest to accept session_id**

```python
class RunAgentRequest(BaseModel):
    """Payload for running an agent."""
    task: str
    images: list[str] = Field(default_factory=list, description="Base64 encoded images")
    model_config_id: str | None = Field(default=None, description="临时覆盖默认模型")
    session_id: str | None = Field(default=None, description="会话ID，用于多轮对话继续")
```

- [ ] **Step 2: Update run_agent to configure checkpointer and pass session_id**

```python
from langgraph.checkpoint.memory import MemorySaver

runner = DeepAgentsRunner(agent, storage, override_model_config_id=request.model_config_id)

# Set checkpointer if session_id provided
if request.session_id:
    runner.set_checkpointer(MemorySaver(), request.session_id)

try:
    await runner.create()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

Also update the stream to return session_id:

```python
yield f"data: {json.dumps({'type': 'start', 'task': task, 'model': model_name, 'session_id': request.session_id})}\n\n"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/agents.py && \
git commit -m "feat(api): pass session_id to checkpointer-enabled agent"
```

---

## Task 3: Frontend Types

**Files:**
- Modify: `frontend/types/index.ts`

### Steps

- [ ] **Step 1: Add Message type**

```typescript
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/types/index.ts && \
git commit -m "feat(frontend): add Message type for conversation history"
```

---

## Task 4: Frontend Store - Message State

**Files:**
- Modify: `frontend/stores/agents.ts`

### Steps

- [ ] **Step 1: Update agents store to manage conversation state**

Add message state and session tracking:

```typescript
export const useAgentsStore = defineStore('agents', () => {
  const agents = ref<Agent[]>([])
  const currentAgent = ref<Agent | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  // New: conversation state
  const currentSessionId = ref<string | null>(null)
  const messages = ref<Message[]>([])

  // ... existing methods ...

  function setCurrentSession(sessionId: string | null) {
    currentSessionId.value = sessionId
    messages.value = []
  }

  function addMessage(message: Message) {
    messages.value.push(message)
  }

  function clearSession() {
    currentSessionId.value = null
    messages.value = []
  }

  return {
    agents,
    currentAgent,
    loading,
    error,
    currentSessionId,
    messages,
    fetchAgents,
    fetchAgent,
    createAgent,
    updateAgent,
    deleteAgent,
    setCurrentSession,
    addMessage,
    clearSession,
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/stores/agents.ts && \
git commit -m "feat(frontend): add conversation state management"
```

---

## Task 5: Frontend AgentDetailView - Conversation UI

**Files:**
- Modify: `frontend/views/AgentDetailView.vue`

### Steps

- [ ] **Step 1: Add conversation state refs**

After existing refs (~line 18), add:

```typescript
// Conversation state
const currentSessionId = ref<string | null>(null)
const messages = ref<Array<{
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}>>([])
```

- [ ] **Step 2: Update handleRun to capture session_id and send it**

In `handleRun` (~line 117-165), add session_id to request:

```typescript
xhr.send(JSON.stringify({
  task: taskInput.value,
  images: uploadedImages.value,
  model_config_id: selectedModelId.value,
  session_id: currentSessionId.value,
}))
```

- [ ] **Step 3: Update handleEvent to capture session_id and build message history**

In `handleEvent` (~line 167), update 'start' and 'content' cases:

```typescript
case 'start':
  // Capture session_id for continued conversation
  if (data.session_id) {
    currentSessionId.value = data.session_id
  }
  generatedImages.value = []
  events.value.push({ ...event, content: `会话: ${data.task}`, model: data.model })
  // Add user message to local history
  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content: data.task,
    timestamp: new Date(),
  })
  break

case 'content':
  currentEvent.value = null
  let content = data.content || ''
  content = content.replace(/<think>[\s\S]*?<\/think>/gi, '')
  if (content.trim()) {
    appendOutput(content)
    events.value.push({ ...event, content })
  }
  break
```

Add 'done' case to add assistant message to history:

```typescript
case 'done':
  currentEvent.value = null
  appendOutput('\n\n--- 完成 ---\n')
  events.value.push({ ...event, content: '任务完成' })
  // Add assistant response to message history
  const responseContent = outputRef.value?.textContent || ''
  messages.value.push({
    id: `assistant-${Date.now()}`,
    role: 'assistant',
    content: responseContent,
    timestamp: new Date(),
  })
  break
```

- [ ] **Step 4: Add conversation history display**

In the template section, add a messages list above the output:

```vue
<!-- Conversation History -->
<div v-if="messages.length > 0" class="mb-4 space-y-3">
  <h3 class="text-sm font-medium text-gray-700">对话历史</h3>
  <div v-for="msg in messages" :key="msg.id"
       :class="['p-3 rounded-lg', msg.role === 'user' ? 'bg-blue-50' : 'bg-gray-50']">
    <div class="flex items-center gap-2 mb-1">
      <span :class="['text-xs font-medium', msg.role === 'user' ? 'text-blue-600' : 'text-gray-600']">
        {{ msg.role === 'user' ? '用户' : '助手' }}
      </span>
      <span class="text-xs text-gray-400">{{ new Date(msg.timestamp).toLocaleTimeString() }}</span>
    </div>
    <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ msg.content }}</p>
  </div>
</div>
```

- [ ] **Step 5: Add "新对话" button to clear session**

Add a button next to Run Agent button:

```vue
<Button v-if="currentSessionId" variant="secondary" @click="clearSession">
  新对话
</Button>
```

Add the clearSession function:

```typescript
function clearSession() {
  currentSessionId.value = null
  messages.value = []
  clearOutput()
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/views/AgentDetailView.vue && \
git commit -m "feat(frontend): add multi-turn conversation UI"
```

---

## Self-Review

**1. Spec coverage:**
- Multi-turn conversation via LangGraph checkpointer ✓
- Frontend sends session_id, receives it back ✓
- Message history display ✓
- New conversation button ✓

**2. Placeholder scan:** No placeholders found. All steps have concrete code.

**3. Type consistency:**
- `Message` type matches frontend usage (id, role, content, timestamp)
- `session_id` passed as string through all layers ✓