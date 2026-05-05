# MCP Gateway Microservice — Architecture Plan

## Context

claw-platform's MCP integration currently runs as an in-process adapter (`client.py`) communicating over stdio with an MCP server spawned as a subprocess. This works for single-node deployment but blocks the multi-service OCAP architecture.

**Why redesign:**
- Gateway should be a standalone microservice (FastMCP) so OCAP agents can use it without claw-platform process coupling
- IT needs a config UI where they input HTTP API endpoints → gateway dynamically generates MCP routes
- Gateway polls claw-platform REST API for tool registration updates (decoupled sync)

**Reference:** Studied [Unla](https://github.com/AmoyLab/Unla) — a production Go-based MCP gateway with YAML-driven HTTP→MCP translation, template-based request/response transformation, hot-reload, and multi-transport support (stdio/SSE/streamable HTTP).

---

## Decision Summary

| Decision | Choice | Rationale |
|---|---|---|
| D1 — Gateway sync | B) claw-platform pushes OR gateway polls | Decoupled microservices; no tight coupling |
| D2 — Sync protocol | B) claw-platform exposes internal REST API | Reuse existing `/api/tools`; no new wire protocol |
| D3 — Gateway MCP interface | A) HTTP-based MCP adapter + FastMCP | One fewer hop; runner speaks HTTP like OpenAI calls |

---

## Target Architecture

```
OCAP Agent (runner)
    │ MCP over SSE / Streamable HTTP
    ▼
┌─────────────────────────┐
│   MCP Gateway           │  FastMCP
│   ─────────────────     │
│   HTTP→MCP adapter      │  Dynamic route generation
│   Tool registry cache   │  from IT-provided configs
│   /mcp/{tenant}/sse     │  (inspired by Unla)
│   /mcp/{tenant}/message │
│   /mcp/{tenant}/mcp     │
└────────┬────────────────┘
         │ polls REST (every 30s)
         ▼
┌─────────────────────────┐
│   claw-platform         │  FastAPI
│   ─────────────────     │
│   GET /api/tools        │  returns MCP tool registrations
│   POST /api/tools       │  IT creates via UI
│   Tool config UI (IT)   │  persist to DB
└─────────────────────────┘

MCP Gateway also connects to fab systems directly:
  MESAdapter → MES HTTP API
  YMSAdapter → YMS HTTP API
  DMSAdapter → DMS HTTP API
  FDCAdapter → FDC HTTP API
```

---

## MCP Tool Config Schema (from Unla-inspired design)

Based on Unla's YAML-driven approach, the tool registration payload stored in claw-platform:

```json
{
  "name": "mes_wip_query",
  "description": "Query WIP data from MES",
  "type": "MCP",
  "server_name": "mes-server",
  "allowed_tools": ["mes_wip_query"],
  "config": {
    "endpoint": "http://mes-fab01:8080/api/v1/wip",
    "method": "POST",
    "auth": { "type": "bearer", "token": "..." },
    "headers": { "X-Fab-Id": "{{ config.fab_id }}" }
  },
  "args": [
    { "name": "lot_id", "position": "body", "required": true, "type": "string" },
    { "name": "stage", "position": "query", "required": false, "type": "string" }
  ],
  "request_template": "{\"lot_id\": \"{{.Args.lot_id}}\", \"stage\": \"{{.Args.stage}}\"}",
  "response_template": "{\"wip_data\": {{.Response.data}}, \"lot\": \"{{.Response.lot}}\"}"
}
```

Key template expressions (from Unla):
- `{{.Args.argName}}` — tool argument value
- `{{.Config.key}}` — server config value
- `{{.Request.Headers.header}}` — incoming request headers
- `{{ env "VAR_NAME" }}` — environment variables
- `{{.Response.data.field}}` — backend response field
- `{{ toJSON .Args.settings }}` — JSON serialization

---

## Components

### 1. MCP Gateway Microservice (`gateway/`)

```
gateway/
├── main.py                    # FastMCP entry point, SSE/streamable attachment
├── adapters/
│   ├── fab_adapters.py       # MES/YMS/DMS/FDC (moved from backend/app)
│   └── http_template.py      # HTTP→MCP with template rendering
├── core/
│   ├── tool_registry.py      # In-memory cache of tool registrations
│   ├── route_generator.py    # Dynamic FastMCP route from tool config
│   └── transport.py          # SSE / streamable HTTP transport handlers
├── sync/
│   └── claw_poller.py        # Poll claw-platform /api/tools for updates
└── requirements.txt
```

**Key design points (from Unla):**
- `HTTPAdapter`: receives MCP JSON-RPC over SSE or streamable HTTP, translates to HTTP calls with template rendering
- `ToolRegistry`: caches tool metadata from claw-platform; refreshed every 30s via poller
- `RouteGenerator`: given tool config (name, endpoint, method, auth, args, templates), dynamically creates FastMCP tool handler
- Template engine: Jinja2-like expressions for URL/header/body transformation
- Hot-reload: on config change, poller detects via ETag/Last-Modified or polls every 30s

### 2. claw-platform REST API (Internal)

```
GET    /api/tools             → list all MCP tool registrations
GET    /api/tools/:id         → single tool config
POST   /api/tools             → IT creates tool registration
PUT    /api/tools/:id         → IT updates
DELETE /api/tools/:id         → IT deletes

Response shape:
{
  "id": "uuid",
  "name": "mes_wip_query",
  "description": "...",
  "type": "MCP",
  "server_name": "mes-server",
  "config": { ... },
  "args": [ ... ],
  "request_template": "...",
  "response_template": "...",
  "updated_at": "ISO8601"
}
```

- `ToolsController` in `backend/app/api/tools.py`
- `ToolService` persists to SQLite `tools` table
- Internal API authenticated via `X-Gateway-Token` header (gateway → claw-platform)

### 3. IT Config UI (Frontend)

**Route**: `GET /tools/create` → `ToolCreateView`

**Form fields:**
- Tool name (string, required)
- Description (string)
- Server name (string, groups tools under same backend)
- Type: `MCP` (select, default)
- HTTP Endpoint URL (string, required)
- HTTP Method (select: GET / POST / PUT / DELETE)
- Auth type (`none` | `bearer` | `apikey`)
- Auth token/header value
- Args: dynamic list — name, position (body/query/path/header), required, type
- Request template (textarea with template syntax help)
- Response template (textarea)

**List view**: existing `/tools` — add `MCP` / `Builtin` badge

### 4. Frontend Changes

| File | Change |
|---|---|
| `src/stores/tools.ts` | Add `createTool()`, `updateTool()`, `deleteTool()` |
| `src/views/ToolCreateView.vue` | New — MCP tool registration form with template fields |
| `src/views/ToolsView.vue` | Show type badge (`Builtin` / `MCP`) |
| `src/router/index.ts` | Add `/tools/create` route |
| `src/api/tools.ts` | Add POST/PUT/DELETE methods |

### 5. Backend Changes

| File | Change |
|---|---|
| `backend/app/api/tools.py` | Add POST/PUT/DELETE `/api/tools` endpoints |
| `backend/app/services/tool_service.py` | New — CRUD operations on tool DB records |
| `backend/app/models/tool.py` | Add `ToolModel` with full MCP config schema (type, server_name, config JSON, args, templates) |
| `backend/app/infrastructure/storage/sqlite.py` | Add `save_tool()`, `get_tool()`, `list_tools()`, `delete_tool()` |

---

## Implementation Order

```
Step 1 — Backend tool CRUD
  └── backend/app/models/tool.py, tool_service.py, tools.py
  └── Test: curl CRUD via API

Step 2 — Frontend ToolCreateView + store methods
  └── src/stores/tools.ts, src/views/ToolCreateView.vue, src/api/tools.ts
  └── Test: IT fills form → tool in DB → appears in Tools list

Step 3 — MCP Gateway scaffold
  └── gateway/main.py, requirements.txt, core/route_generator.py
  └── Test: gateway starts, FastMCP serves on :8081, /health OK

Step 4 — HTTPAdapter with template rendering
  └── gateway/adapters/http_template.py (inspired by Unla's tool.go)
  └── Test: tool call with {{.Args.xxx}} → correct HTTP request to backend

Step 5 — Claw poller + hot-reload
  └── gateway/sync/claw_poller.py, tool_registry.py
  └── Test: gateway polls claw-platform, registers new tools dynamically

Step 6 — End-to-end: IT registers MES tool → OCAP agent uses it
  └── Full integration test
```

---

## Verification

- [ ] `curl -X POST http://localhost:8080/api/tools -d '{"name":"mes_test"...}'` creates tool in DB
- [ ] Frontend: IT fills form → tool appears in Tools list with `MCP` badge
- [ ] Gateway starts: `python gateway/main.py` → FastMCP serves on `:8081`
- [ ] OCAP agent calls `mes_wip_query` via gateway → response from MES adapter
- [ ] Gateway logs: poll → route registration → MCP call → response

---

## Open Questions / TBD

1. **Auth**: `X-Gateway-Token` header for gateway↔claw-platform for now; upgrade to mTLS in prod
2. **Hot-reload trigger**: poll every 30s (simple); add webhook endpoint on claw-platform for push-based invalidation later
3. **FDC real-time**: may need WebSocket → defer to v2; current FDCAdapter uses REST
4. **Response streaming**: for long-running fab queries, support streaming JSON-RPC responses
5. **Multi-tenant**: Unla uses `{tenant}/mcp/sse` paths; for v1 single tenant is fine