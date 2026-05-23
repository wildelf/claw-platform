# Phase 1 API Reference

## Overview

Phase 1 exposes two groups of REST endpoints under `/api`:

| Group | Prefix | Purpose |
|-------|--------|---------|
| Employee Profiles | `/api/employee-profiles` | CRUD for digital employee identities + file management |
| Operations | `/api/operations` | Worker monitoring, queue stats, task management |

**Auth**: All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

**Content-Type**: `application/json` for request/response bodies.

---

## 1. Employee Profiles API

Base path: `/api/employee-profiles`

### 1.1 Create Employee Profile

```
POST /api/employee-profiles
```

**Request Body**:
```json
{
  "name": "张三",
  "role": "AI 客服专员",
  "goal": "高效处理客户咨询和投诉，提升客户满意度",
  "backstory": "拥有 5 年客服经验的 AI 员工...",
  "personality": "耐心、友善、专业"
}
```

| Field | Type | Required | Max Length |
|-------|------|----------|------------|
| name | string | Yes | 100 |
| role | string | Yes | 500 |
| goal | string | Yes | 1000 |
| backstory | string | No | 2000 |
| personality | string | No | 1000 |

**Response** `201 Created`:
```json
{
  "id": "ep-abc123",
  "name": "张三",
  "role": "AI 客服专员",
  "goal": "高效处理客户咨询和投诉，提升客户满意度",
  "backstory": "拥有 5 年客服经验的 AI 员工...",
  "personality": "耐心、友善、专业",
  "status": "active",
  "userId": "user-001",
  "organizationId": null,
  "gitPath": "/Users/wilde/.qoder/employees/ep-abc123/",
  "createdAt": "2026-05-24T10:00:00Z",
  "updatedAt": "2026-05-24T10:00:00Z"
}
```

**Errors**:
- `400` — Validation error (missing required fields, length exceeded)
- `401` — Not authenticated

---

### 1.2 List Employee Profiles

```
GET /api/employee-profiles
```

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| status | string | — | Filter by status: active/paused/retired |
| limit | int | 50 | Max results (1-200) |
| offset | int | 0 | Pagination offset |

**Response** `200 OK`:
```json
{
  "profiles": [
    {
      "id": "ep-abc123",
      "name": "张三",
      "role": "AI 客服专员",
      "status": "active",
      "createdAt": "2026-05-24T10:00:00Z",
      "updatedAt": "2026-05-24T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 1.3 Get Employee Profile

```
GET /api/employee-profiles/{profile_id}
```

**Response** `200 OK`: Same as Create response body.

**Errors**:
- `404` — Profile not found
- `403` — Not the owner

---

### 1.4 Update Employee Profile

```
PUT /api/employee-profiles/{profile_id}
```

**Request Body**: Same fields as Create, all optional.

**Response** `200 OK`: Same as Create response body.

**Errors**:
- `404` — Profile not found
- `403` — Not the owner
- `400` — Validation error

---

### 1.5 Delete Employee Profile

```
DELETE /api/employee-profiles/{profile_id}
```

**Response** `200 OK`:
```json
{
  "deleted": true,
  "message": "Employee profile deleted"
}
```

**Errors**:
- `404` — Profile not found
- `403` — Not the owner

---

### 1.6 Get Profile Files

```
GET /api/employee-profiles/{profile_id}/files
```

**Response** `200 OK`:
```json
{
  "files": [
    {"filename": "profile.md", "size": 512, "updatedAt": "2026-05-24T10:00:00Z"},
    {"filename": "constraints.md", "size": 256, "updatedAt": "2026-05-24T10:00:00Z"},
    {"filename": "working_rules.md", "size": 384, "updatedAt": "2026-05-24T10:00:00Z"}
  ]
}
```

**Errors**:
- `404` — Profile not found
- `403` — Not the owner

---

### 1.7 Get Profile File Content

```
GET /api/employee-profiles/{profile_id}/files/{filename}
```

**Response** `200 OK`:
```json
{
  "filename": "constraints.md",
  "content": "# Constraints\n\n- Do not share customer data...",
  "size": 256,
  "updatedAt": "2026-05-24T10:00:00Z"
}
```

**Errors**:
- `404` — Profile or file not found
- `403` — Not the owner

---

### 1.8 Update Profile File Content

```
PUT /api/employee-profiles/{profile_id}/files/{filename}
```

**Request Body**:
```json
{
  "content": "# Working Rules\n\n1. Always respond within 30 seconds..."
}
```

**Response** `200 OK`:
```json
{
  "filename": "working_rules.md",
  "content": "# Working Rules\n\n1. Always respond within 30 seconds...",
  "size": 384,
  "updatedAt": "2026-05-24T10:05:00Z"
}
```

**Errors**:
- `404` — Profile not found
- `403` — Not the owner
- `400` — Invalid filename (only profile.md, constraints.md, working_rules.md)

---

## 2. Operations API

Base path: `/api/operations`

### 2.1 Get Worker Status

```
GET /api/operations/worker/status
```

**Response** `200 OK`:
```json
{
  "worker_id": "worker:myhost:12345",
  "status": "online",
  "last_heartbeat": "2026-05-24T10:30:15Z",
  "last_heartbeat_seconds_ago": 3,
  "started_at": "2026-05-24T08:00:00Z",
  "uptime_seconds": 9015,
  "redis_connection": "localhost:6379"
}
```

Offline response:
```json
{
  "worker_id": null,
  "status": "offline",
  "last_heartbeat": null,
  "last_heartbeat_seconds_ago": null,
  "started_at": null,
  "uptime_seconds": null,
  "redis_connection": "localhost:6379"
}
```

---

### 2.2 Restart Worker

```
POST /api/operations/worker/restart
```

**Response** `200 OK`:
```json
{
  "restarting": true,
  "message": "Worker restart signal sent"
}
```

**Errors**:
- `404` — No worker registered

---

### 2.3 Stop Worker

```
POST /api/operations/worker/stop
```

**Response** `200 OK`:
```json
{
  "stopping": true,
  "message": "Worker stop signal sent"
}
```

**Errors**:
- `404` — No worker registered

---

### 2.4 Get Queue Stats

```
GET /api/operations/queue/stats
```

**Response** `200 OK`:
```json
{
  "queued": 12,
  "processing": 3,
  "completed": 156,
  "failed": 2
}
```

---

### 2.5 Clear Queue

```
POST /api/operations/queue/clear
```

**Response** `200 OK`:
```json
{
  "cleared_count": 12,
  "message": "Cleared 12 tasks"
}
```

---

### 2.6 List Tasks

```
GET /api/operations/tasks
```

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| status | string | — | Filter: queued/processing/completed/failed |
| limit | int | 50 | Max results (1-200) |

**Response** `200 OK`:
```json
{
  "tasks": [
    {
      "task_id": "t-001",
      "agent_id": "agent-xyz",
      "agent_name": "张三",
      "status": "processing",
      "created_at": "2026-05-24T10:25:00Z",
      "completed_at": null,
      "error": null
    }
  ],
  "total": 1
}
```

---

### 2.7 Cancel Task

```
POST /api/operations/tasks/{task_id}/cancel
```

**Response** `200 OK`:
```json
{
  "task_id": "t-001",
  "cancelled": true,
  "message": "Task cancelled"
}
```

**Errors**:
- `404` — Task not found or cannot be cancelled (already completed/failed)

---

## 3. Error Response Format

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Status | Meaning |
|-------------|---------|
| 400 | Bad Request — Validation error |
| 401 | Unauthorized — Missing or invalid JWT |
| 403 | Forbidden — Not the resource owner |
| 404 | Not Found — Resource does not exist |
| 500 | Internal Server Error |

---

## 4. Data Types Reference

### EmployeeProfileStatus
`"active"` | `"paused"` | `"retired"`

### TaskStatus
`"queued"` | `"processing"` | `"completed"` | `"failed"` | `"cancelled"`

### WorkerStatus
`"online"` | `"offline"`

### Valid Filenames
`"profile.md"` | `"constraints.md"` | `"working_rules.md"`
