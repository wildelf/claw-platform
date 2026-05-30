# Conversation Interface Design

**Date:** 2026-05-31
**Author:** Claude
**Status:** Approved

## Context

The user (claw-platform project) wants to build a conversation UI similar to QoderWake (http://127.0.0.1:19820/) for semiconductor factory operators. The primary goal is to enable operators to interact with AI Agents through a conversational interface.

**Key Constraints:**
- Target users: Production operators (YE, EE, IT roles)
- Platform: Vue 3 + TypeScript frontend, FastAPI Python backend
- Backend: DeepAgents framework (already supports streaming)
- Deployment: Independent page (`/conversation`)

---

## Design Summary

This design covers the conversation interface for claw-platform, enabling factory operators to chat with specialized AI Agents to query MES/YMS/DMS/FDC systems and perform production tasks.

---

## 1. Page Layout

```
┌─────────────────────────────────────────────────────────┐
│  Header: Logo + 当前用户信息                              │
├──────────────┬──────────────────────────────────────────┤
│              │  Header: Wilde >  + Task/Automation      │
│   侧边栏      ├──────────────────────────────────────────┤
│   (260px)    │                                          │
│              │          欢迎区 / 对话区                  │
│  My Agents   │                                          │
│   (N)        │                                          │
│              ├──────────────────────────────────────────┤
│  + Create    │          输入区                           │
│              │  Select Workspace | 输入框 | 发送         │
└──────────────┴──────────────────────────────────────────┘
```

### 1.1 Left Sidebar (260px)

- **Top:** Logo "claw-platform" + "Beta"
- **Section:** "My Agents (N)" with count
- **Button:** "+ Create Agent" (dashed border, for future use)
- **List:** Agent cards with avatar, name, description, date
- **Bottom:** User info (avatar, name, org, settings icon)

### 1.2 Main Content Area

**Header Bar:**
- Left: Current Agent name + avatar
- Right: "+ Task", "+ Automation", "Task List" buttons

**Content Zone (switchable):**
- Welcome view (when no conversation)
- Conversation view (when in chat)

**Input Area:**
- Left: "Select Workspace" dropdown
- Center: Text input with placeholder
- Right: "auto" mode selector + Send button

---

## 2. Core Interactions

### 2.1 Agent Switching
- Click sidebar Agent → Load welcome view for that agent
- If has history → Show recent conversation
- If new → Show welcome message + shortcuts

### 2.2 Message Sending
- Type in input → Press Enter or Send → Message appears in chat
- AI response → Stream via SSE, display in real-time
- Workspace selection → Affects AI context

### 2.3 Shortcuts / Suggested Actions
- Preset buttons for common operations (e.g., "Query lot status", "Check equipment")
- Click → Fill input, user can modify → Send
- Shortcuts are per-Agent-type (configurable later)

### 2.4 Task / Automation
- "+ Task" → Create task (future feature)
- "+ Automation" → Create automation (future feature)

---

## 3. Data Models

### 3.1 Session

```typescript
interface Session {
  id: string
  agent_id: string        // Associated Agent
  user_id: string
  workspace_id: string     // Context workspace
  title: string            // Conversation title (for list)
  created_at: string
  updated_at: string
  last_message_at: string | null
}
```

### 3.2 Message

```typescript
interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  metadata: {
    agent_id?: string
    tools_used?: string[]
  } | null
}
```

### 3.3 Workspace (Auto-created)

```typescript
interface Workspace {
  id: string
  name: string              // e.g., "YE-Workspace"
  type: 'private' | 'public'
  owner_agent_id: string     // For private type only
  created_at: string
}
```

**Lifecycle:**
- Create Agent → Auto-create private Workspace (name = Agent name + "-Workspace")
- Delete Agent → Auto-delete Workspace
- Public Workspace → Admin creates manually

---

## 4. API Design

### 4.1 Session Endpoints

```
GET    /api/agents/:id/sessions        # List sessions for agent
POST   /api/agents/:id/sessions        # Create new session
GET    /api/sessions/:id               # Get session details
DELETE /api/sessions/:id               # Delete session
```

### 4.2 Message Endpoints

```
GET    /api/sessions/:id/messages      # List messages (history)
POST   /api/sessions/:id/messages      # Send message (SSE stream)
```

### 4.3 Workspace Endpoints

```
GET    /api/workspaces                 # List all workspaces (for current user)
GET    /api/workspaces/:id             # Get workspace details
POST   /api/workspaces                 # Create workspace (admin)
PUT    /api/workspaces/:id             # Update workspace (admin)
DELETE /api/workspaces/:id             # Delete workspace (admin)
```

### 4.4 SSE Message Streaming

**POST /api/sessions/:id/messages**

Request:
```json
{
  "content": "Query WIP data for lot ABC",
  "workspace_id": "optional-workspace-id"
}
```

Response: SSE stream
```
event: message_start
data: {"message_id": "xxx"}

event: token
data: {"content": "好的"}

event: tool_call
data: {"tool": "mes_wip_query", "args": {"lot_id": "ABC"}}

event: tool_result
data: {"tool": "mes_wip_query", "result": {...}}

event: content
data: {"content": "查询完成"}

event: message_end
data: {"message_id": "xxx", "final_content": "查询完成"}
```

---

## 5. Backend Integration

### 5.1 DeepAgentsRunner Streaming

The `DeepAgentsRunner.run()` method is already an `AsyncGenerator` that yields events:

- `type: "preparing"` - Preparation phase
- `type: "content"` - Token content
- `type: "tool_call"` - Tool invocation
- `type: "tool_result"` - Tool result
- `type: "image"` - Generated image
- `type: "update"` - Node/task updates

### 5.2 SSE Adapter Layer

The API layer needs to:
1. Receive events from `DeepAgentsRunner.run()`
2. Transform to SSE format for frontend
3. Store final message to database on completion

```
User → API → DeepAgentsRunner.run() → SSE Adapter → Frontend SSE
                                    → Database (on complete)
```

---

## 6. Frontend Views

### 6.1 ConversationView

Main view component at `/conversation` route:
- Sidebar with AgentList
- Welcome area (when no active session)
- Chat area (when in conversation)
- Input area with Workspace selector

### 6.2 Components

| Component | Description |
|-----------|-------------|
| `AgentSidebar` | Left sidebar with Agent list |
| `AgentCard` | Individual Agent in sidebar |
| `ConversationHeader` | Agent name + action buttons |
| `WelcomeView` | Avatar, greeting, shortcuts |
| `ChatView` | Message list + input |
| `MessageBubble` | User/Assistant message display |
| `WorkspaceSelector` | Dropdown for Workspace selection |
| `MessageInput` | Text input + send button |

---

## 7. Workspace Policy

### 7.1 Workspace Types

| Type | Created By | Visible To |
|------|-----------|------------|
| Private | Auto (on Agent create) | Owner Agent only |
| Public | Admin manual | All Agents |

### 7.2 Lifecycle Rules

- **Create Agent:** Auto-create `"{AgentName}-Workspace"` (private)
- **Delete Agent:** Auto-delete its Workspace
- **Public Workspace:** Admin creates via API (no UI needed for v1)

### 7.3 Context Behavior

- Workspace selected → Passed to API as context
- AI receives Workspace info → Included in prompt
- Content loaded on-demand (user decides whether to bring into conversation)

---

## 8. Future Extensions (Out of Scope)

- Task management UI ("+ Task" button)
- Automation management UI ("+ Automation" button)
- Agent creation UI (currently admin-only)
- Workspace management UI (not needed, indirect via Agent)
- Per-Agent shortcuts/suggested actions

---

## 9. Implementation Order

1. **Backend:** Session + Message models + CRUD API
2. **Backend:** SSE streaming endpoint for chat
3. **Backend:** Workspace auto-creation on Agent create
4. **Frontend:** ConversationView page layout
5. **Frontend:** AgentSidebar component
6. **Frontend:** WelcomeView component
7. **Frontend:** ChatView + MessageBubble
8. **Frontend:** MessageInput + WorkspaceSelector
9. **Integration:** SSE connection + real-time display

---

## 10. Verification Checklist

- [ ] Session CRUD API works
- [ ] Message creation triggers DeepAgentsRunner
- [ ] SSE stream delivers tokens to frontend
- [ ] Agent switch shows correct welcome/history
- [ ] Workspace selection persists in session
- [ ] Tool calls display correctly during streaming
- [ ] Message history loads on page refresh