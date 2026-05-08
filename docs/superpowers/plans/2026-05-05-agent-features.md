# Agent Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 4 agent features: true streaming, session memory, collapsible config/scheduled sections

**Architecture:**
- Streaming: Backend already emits SSE; frontend needs to switch from XHR polling to true streaming via `ReadableStream` or EventSource
- Session memory: Verify checkpointer properly restores conversation history; frontend needs to persist `session_id` in localStorage
- Collapsible UI: Add Vue collapsible wrappers around config and scheduled tasks sections using existing patterns

**Tech Stack:** Vue 3, FastAPI, SSE (Server-Sent Events), LangGraph MemorySaver

---

## File Structure

```
Files to modify:
- backend/app/api/agents.py                 → SSE streaming endpoint
- backend/app/deepagents/wrapper.py        → Session/checkpointer logic
- src/views/AgentDetailView.vue            → Main UI (streaming, collapsible, session)
- frontend/views/AgentDetailView.vue       → Older version (streaming only)
- src/stores/agents.ts                     → Session ID persistence
- src/types/index.ts                       → Message type definitions
```

---

## Task 1: True Streaming Output

**Files:**
- Modify: `src/views/AgentDetailView.vue:228-241` (streaming handler)
- Modify: `frontend/views/AgentDetailView.vue:222-286` (older version)

**Current Issue:** Frontend uses XHR `.onprogress` which polls the full response text - not true streaming. Events arrive in batches rather than incrementally.

**Steps:**

- [ ] **Step 1: Read current streaming implementation**

Run: Read lines 220-295 in `src/views/AgentDetailView.vue`

- [ ] **Step 2: Change XHR to fetch with ReadableStream**

Replace the XHR-based streaming with `fetch()` + `ReadableStream` for true streaming:

```javascript
// Replace xhr.onprogress block (lines ~228-241) with:
const reader = response.body.getReader()
const decoder = new TextDecoder()
let buffer = ''

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  
  buffer += decoder.decode(value, { stream: true })
  const lines = buffer.split('\n')
  buffer = lines.pop() || ''
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const data = JSON.parse(line.slice(6))
        handleEvent(data, agentMessage)
      } catch {}
    }
  }
}
```

- [ ] **Step 3: Apply same fix to frontend version**

Copy the streaming fix to `frontend/views/AgentDetailView.vue` at the equivalent location.

- [ ] **Step 4: Test streaming**

Start the dev server and run an agent - verify content appears incrementally rather than in batches.

---

## Task 2: Session Memory Persistence

**Files:**
- Modify: `src/stores/agents.ts` → Persist session_id
- Modify: `src/views/AgentDetailView.vue` → Restore session on mount
- Modify: `backend/app/api/agents.py` → Verify checkpointer behavior

**Current Issue:** `session_id` is created fresh each time, causing each turn to have no memory of previous turns.

**Steps:**

- [ ] **Step 1: Read agents store**

Run: `cat src/stores/agents.ts`

- [ ] **Step 2: Add session persistence to agents store**

Add to agents store (after line ~50):
```typescript
function getStoredSessionId(agentId: string): string | null {
  return localStorage.getItem(`agent_session_${agentId}`)
}

function setStoredSessionId(agentId: string, sessionId: string) {
  localStorage.setItem(`agent_session_${agentId}`, sessionId)
}
```

- [ ] **Step 3: Update handleRun to restore stored session**

In `AgentDetailView.vue`, modify `handleRun` (around line 270) to:
```javascript
const storedSessionId = getStoredSessionId(agentId.value)
const sessionId = storedSessionId || crypto.randomUUID()
if (!storedSessionId) {
  setStoredSessionId(agentId.value, sessionId)
}
currentSessionId.value = sessionId
```

- [ ] **Step 4: Clear session on new conversation**

When user clicks "清空对话" (clearOutput), also clear the stored session:
```javascript
function clearOutput() {
  messages.value = []
  currentSessionId.value = null
  localStorage.removeItem(`agent_session_${agentId.value}`)
}
```

- [ ] **Step 5: Verify backend checkpointer**

Read `backend/app/api/agents.py` lines 160-180 to verify MemorySaver checkpointer is properly restoring state.

- [ ] **Step 6: Test multi-turn**

1. Ask agent a question
2. Ask a follow-up that references the first question
3. Verify agent remembers context

---

## Task 3: Collapsible Config and Scheduled Tasks

**Files:**
- Modify: `src/views/AgentDetailView.vue:391-412` (scheduled tasks)
- Modify: `src/views/AgentDetailView.vue:445-458` (config section)

**Steps:**

- [ ] **Step 1: Wrap Scheduled Tasks in collapsible**

Replace lines 391-412 with:
```vue
<Card title="Scheduled Tasks" :padding="false">
  <div class="p-4">
    <button
      @click="scheduledTasksExpanded = !scheduledTasksExpanded"
      class="w-full flex items-center justify-between text-sm text-gray-600 hover:bg-gray-50 -mx-4 -mt-4 px-4 py-2"
    >
      <span>Scheduled Tasks</span>
      <span>{{ scheduledTasksExpanded ? '收起' : '展开' }}</span>
    </button>
    <div v-show="scheduledTasksExpanded">
      <!-- existing content -->
    </div>
  </div>
</Card>
```

- [ ] **Step 2: Add collapsible to Config section**

After line 458 (end of config grid), wrap the content in a collapsible div:
```vue
<div class="pt-4 border-t border-gray-200">
  <button
    @click="configExpanded = !configExpanded"
    class="w-full flex items-center justify-between text-sm text-gray-600 hover:bg-gray-50 -mx-4 -mt-4 px-4 py-2"
  >
    <span>Configuration</span>
    <span>{{ configExpanded ? '收起' : '展开' }}</span>
  </button>
  <div v-show="configExpanded">
    <!-- existing grid content -->
  </div>
</div>
```

- [ ] **Step 3: Add state refs**

Add after line ~50:
```typescript
const scheduledTasksExpanded = ref(true)
const configExpanded = ref(true)
```

- [ ] **Step 4: Test collapsible**

Verify both sections collapse/expand correctly.

---

## Task 4: Thinking Collapsible (Already Done)

The thinking section is already collapsible (lines 515-528). The recent fix removed the "AI 正在思考..." placeholder that was being concatenated with actual thinking content.

**Verification only:**

- [ ] **Step 1: Verify thinking collapsible works**

Open agent detail, run agent, verify thinking section expands/collapses and shows content properly without placeholder text.

---

## Self-Review Checklist

1. **Spec coverage:**
   - Streaming output → Task 1
   - Session memory → Task 2
   - Config/scheduled collapsible → Task 3
   - Thinking collapsible → Task 4 (already done + fix)

2. **Placeholder scan:** No TODOs or placeholders in plan

3. **Type consistency:**
   - `session_id` vs `currentSessionId` - consistent in code
   - `handleEvent` function - unchanged
   - `agentMessage.thinking` - unchanged

---

**Plan saved to:** `docs/superpowers/plans/2026-05-05-agent-features.md`

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
