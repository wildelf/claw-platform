# Phase 2 API Reference

## Overview

Phase 2 introduces the **Dual-Layer Permission Verification** system. It exposes four groups of REST endpoints under `/api`:

| Group | Prefix | Purpose |
|-------|--------|---------|
| Permission Rules | `/api/permissions/rules` | CRUD for permission rules with Git-backed storage |
| Permission Evaluation | `/api/permissions/evaluate` | Evaluate tool actions through the dual-layer engine |
| Audit Logs | `/api/permissions/audit-logs` | Query and analyze permission decision logs |
| Override Requests | `/api/permissions/overrides` | Submit and manage permission override approvals |

**Auth**: All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

**Content-Type**: `application/json` for request/response bodies.

---

## 1. Permission Rules API

Base path: `/api/permissions/rules`

### 1.1 Create Permission Rule

```
POST /api/permissions/rules
```

**Request Body**:
```json
{
  "name": "禁止删除 .git 目录",
  "description": "防止任何操作删除 Git 版本控制目录",
  "category": "DELETE",
  "risk_level": "CRITICAL",
  "pattern": "rm.*\\.git(/|$)",
  "action": "DENY",
  "priority": 8,
  "enabled": true,
  "employee_id": null
}
```

| Field | Type | Required | Max Length | Description |
|-------|------|----------|------------|-------------|
| name | string | Yes | 200 | Rule name |
| description | string | No | 1000 | Human-readable description |
| category | enum | Yes | — | `READ`, `WRITE`, `DELETE`, `EXECUTE`, `NETWORK`, `PRODUCTION` |
| risk_level | enum | Yes | — | `SAFE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| pattern | string | Yes | 500 | Regex pattern for matching tool input |
| action | enum | Yes | — | `ALLOW`, `DENY`, `REQUIRE_APPROVAL` |
| priority | int | No | — | 1-10, higher = checked first (default: 5) |
| enabled | bool | No | — | Whether rule is active (default: true) |
| employee_id | string (UUID) | No | — | Target employee; null = global rule |

**Response** `201 Created`:
```json
{
  "id": "rule-abc123",
  "name": "禁止删除 .git 目录",
  "description": "防止任何操作删除 Git 版本控制目录",
  "category": "DELETE",
  "risk_level": "CRITICAL",
  "pattern": "rm.*\\.git(/|$)",
  "action": "DENY",
  "priority": 8,
  "enabled": true,
  "employee_id": null,
  "git_path": "/Users/wilde/.claw-platform/rules/rule-abc123.yaml",
  "created_at": "2026-05-24T10:00:00Z",
  "updated_at": "2026-05-24T10:00:00Z",
  "created_by": "user-001"
}
```

**Errors**:
- `400` — Validation error (missing required fields, invalid regex pattern, invalid enum value)
- `401` — Not authenticated
- `403` — Not authorized to create rules

---

### 1.2 List Permission Rules

```
GET /api/permissions/rules
```

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| employee_id | string (UUID) | — | Filter by employee (null = global rules) |
| enabled | bool | — | Filter by enabled status |
| category | string | — | Filter by category: READ/WRITE/DELETE/EXECUTE/NETWORK/PRODUCTION |
| limit | int | 50 | Max results (1-200) |
| offset | int | 0 | Pagination offset |

**Response** `200 OK`:
```json
{
  "rules": [
    {
      "id": "rule-abc123",
      "name": "禁止删除 .git 目录",
      "category": "DELETE",
      "risk_level": "CRITICAL",
      "action": "DENY",
      "priority": 8,
      "enabled": true,
      "employee_id": null,
      "created_at": "2026-05-24T10:00:00Z",
      "updated_at": "2026-05-24T10:00:00Z"
    },
    {
      "id": "rule-def456",
      "name": "安全文件读取",
      "category": "READ",
      "risk_level": "SAFE",
      "action": "ALLOW",
      "priority": 5,
      "enabled": true,
      "employee_id": "emp-001",
      "created_at": "2026-05-24T10:05:00Z",
      "updated_at": "2026-05-24T10:05:00Z"
    }
  ],
  "total": 2
}
```

---

### 1.3 Get Permission Rule

```
GET /api/permissions/rules/{rule_id}
```

**Response** `200 OK`: Same as Create response body.

**Errors**:
- `404` — Rule not found

---

### 1.4 Update Permission Rule

```
PUT /api/permissions/rules/{rule_id}
```

**Request Body**: Same fields as Create, all optional. Only provided fields are updated.

```json
{
  "name": "禁止删除 Git 目录（更新）",
  "priority": 9
}
```

**Response** `200 OK`: Same as Create response body.

**Errors**:
- `404` — Rule not found
- `400` — Validation error (invalid regex, invalid enum value)
- `403` — Not authorized to modify this rule

---

### 1.5 Delete Permission Rule

```
DELETE /api/permissions/rules/{rule_id}
```

Soft delete: sets `enabled=false`. Rule remains in storage for audit purposes.

**Response** `200 OK`:
```json
{
  "deleted": true,
  "message": "Permission rule disabled (soft delete)"
}
```

**Errors**:
- `404` — Rule not found
- `403` — Not authorized to delete this rule

---

### 1.6 Toggle Permission Rule

```
PUT /api/permissions/rules/{rule_id}/toggle
```

**Request Body**:
```json
{
  "enabled": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| enabled | bool | Yes | Target enabled state |

**Response** `200 OK`:
```json
{
  "id": "rule-abc123",
  "enabled": false,
  "message": "Rule disabled"
}
```

**Errors**:
- `404` — Rule not found
- `400` — Missing required field `enabled`
- `403` — Not authorized to modify this rule

---

### 1.7 Get Rule Git Log

```
GET /api/permissions/rules/{rule_id}/git-log
```

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| limit | int | 20 | Max commits (1-100) |

**Response** `200 OK`:
```json
{
  "rule_id": "rule-abc123",
  "git_path": "/Users/wilde/.claw-platform/rules/rule-abc123.yaml",
  "commits": [
    {
      "hash": "a1b2c3d",
      "author": "user-001",
      "message": "Update rule priority from 8 to 9",
      "timestamp": "2026-05-24T12:00:00Z"
    },
    {
      "hash": "e5f6g7h",
      "author": "user-002",
      "message": "Initial rule creation",
      "timestamp": "2026-05-24T10:00:00Z"
    }
  ]
}
```

**Errors**:
- `404` — Rule not found
- `500` — Git log retrieval failed

---

## 2. Permission Evaluation API

### 2.1 Evaluate Action

```
POST /api/permissions/evaluate
```

Evaluates a tool action through the dual-layer permission engine (RuleMatcher → ReasoningJudge).

**Request Body**:
```json
{
  "employee_id": "emp-001",
  "agent_id": "agent-xyz",
  "tool_name": "bash",
  "tool_input": {"command": "rm -rf /tmp/production/data"},
  "context": {"working_directory": "/home/user/project"}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| employee_id | string (UUID) | Yes | Employee identifier |
| agent_id | string (UUID) | Yes | Agent identifier |
| tool_name | string | Yes | Tool being invoked |
| tool_input | object | Yes | Tool input parameters (serialized) |
| context | object | No | Additional execution context |

**Response** `200 OK` — Allowed:
```json
{
  "allowed": true,
  "risk_level": "SAFE",
  "decision": "ALLOW",
  "evaluator": "RULE_MATCHER",
  "matched_rule_id": "rule-001",
  "reasoning": "Matched safe-read rule: read_file on non-sensitive path",
  "latency_ms": 8,
  "override_request_id": null
}
```

**Response** `200 OK` — Denied:
```json
{
  "allowed": false,
  "risk_level": "CRITICAL",
  "decision": "DENY",
  "evaluator": "RULE_MATCHER",
  "matched_rule_id": "rule-004",
  "reasoning": "Detected recursive deletion pattern matching dangerous rule #42: rm.*\\.git(/|$)",
  "latency_ms": 12,
  "override_request_id": "override-abc123"
}
```

**Response** `200 OK` — Requires Approval:
```json
{
  "allowed": false,
  "risk_level": "HIGH",
  "decision": "REQUIRE_APPROVAL",
  "evaluator": "REASONING_JUDGE",
  "matched_rule_id": "rule-005",
  "reasoning": "Production directory access requires admin approval per policy",
  "latency_ms": 3200,
  "override_request_id": "override-def456"
}
```

| Field | Type | Description |
|-------|------|-------------|
| allowed | bool | Whether the action can proceed |
| risk_level | enum | `SAFE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| decision | enum | `ALLOW`, `DENY`, `REQUIRE_APPROVAL` |
| evaluator | enum | `RULE_MATCHER`, `REASONING_JUDGE`, `HARDCODED` |
| matched_rule_id | string (UUID) \| null | ID of the rule that matched, or null |
| reasoning | string | Human-readable explanation of the decision |
| latency_ms | int | Total evaluation time in milliseconds |
| override_request_id | string (UUID) \| null | Created override request ID (if DENY or REQUIRE_APPROVAL) |

**Errors**:
- `400` — Validation error (missing required fields)
- `401` — Not authenticated
- `500` — Evaluation engine error

---

## 3. Audit Logs API

Base path: `/api/permissions/audit-logs`

### 3.1 List Audit Logs

```
GET /api/permissions/audit-logs
```

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| employee_id | string (UUID) | — | Filter by employee |
| decision | string | — | Filter by decision: ALLOW/DENY/REQUIRE_APPROVAL |
| risk_level | string | — | Filter by risk level: SAFE/LOW/MEDIUM/HIGH/CRITICAL |
| evaluator | string | — | Filter by evaluator: RULE_MATCHER/REASONING_JUDGE/HARDCODED |
| limit | int | 50 | Max results (1-200) |
| offset | int | 0 | Pagination offset |

**Response** `200 OK`:
```json
{
  "logs": [
    {
      "id": 1024,
      "employee_id": "emp-001",
      "agent_id": "agent-xyz",
      "tool_name": "bash",
      "tool_input": "rm -rf /tmp/production/data",
      "risk_level": "CRITICAL",
      "decision": "DENY",
      "evaluator": "RULE_MATCHER",
      "matched_rule_id": "rule-004",
      "reasoning": "Detected recursive deletion pattern matching dangerous rule #42",
      "latency_ms": 12,
      "timestamp": "2026-05-24T10:30:00Z"
    },
    {
      "id": 1023,
      "employee_id": "emp-002",
      "agent_id": "agent-abc",
      "tool_name": "read_file",
      "tool_input": "docs/readme.md",
      "risk_level": "SAFE",
      "decision": "ALLOW",
      "evaluator": "RULE_MATCHER",
      "matched_rule_id": "rule-001",
      "reasoning": "Matched safe-read rule: read_file on non-sensitive path",
      "latency_ms": 8,
      "timestamp": "2026-05-24T10:28:00Z"
    }
  ],
  "total": 2
}
```

**Errors**:
- `401` — Not authenticated
- `403` — Not authorized to view audit logs

---

### 3.2 Get Audit Statistics

```
GET /api/permissions/audit-logs/stats
```

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| employee_id | string (UUID) | — | Filter by employee |
| period | string | 7d | Time window: 1h / 6h / 24h / 7d / 30d |

**Response** `200 OK`:
```json
{
  "period": "7d",
  "total_evaluations": 15420,
  "by_decision": {
    "ALLOW": 14200,
    "DENY": 980,
    "REQUIRE_APPROVAL": 240
  },
  "by_risk_level": {
    "SAFE": 10500,
    "LOW": 3200,
    "MEDIUM": 820,
    "HIGH": 680,
    "CRITICAL": 220
  },
  "by_evaluator": {
    "RULE_MATCHER": 13800,
    "REASONING_JUDGE": 1500,
    "HARDCODED": 120
  },
  "avg_latency_ms": 45,
  "p95_latency_ms": 120,
  "override_requests": {
    "pending": 12,
    "approved": 180,
    "rejected": 35,
    "expired": 13
  }
}
```

**Errors**:
- `401` — Not authenticated
- `403` — Not authorized to view audit statistics
- `400` — Invalid period value

---

## 4. Override Requests API

Base path: `/api/permissions/overrides`

### 4.1 Create Override Request

```
POST /api/permissions/overrides
```

Creates a permission override request, typically after a DENY or REQUIRE_APPROVAL decision.

**Request Body**:
```json
{
  "employee_id": "emp-001",
  "agent_id": "agent-xyz",
  "tool_name": "bash",
  "tool_input": {"command": "rm -rf /tmp/production/legacy"},
  "risk_level": "HIGH",
  "reason": "需要清理已迁移的旧生产数据目录，已获得业务负责人确认"
}
```

| Field | Type | Required | Max Length | Description |
|-------|------|----------|------------|-------------|
| employee_id | string (UUID) | Yes | — | Employee requesting override |
| agent_id | string (UUID) | Yes | — | Agent that was blocked |
| tool_name | string | Yes | — | Blocked tool name |
| tool_input | object | Yes | — | Blocked tool input (truncated to 2000 chars) |
| risk_level | enum | Yes | — | `HIGH` or `CRITICAL` |
| reason | string | Yes | 2000 | Justification for the override |

**Response** `201 Created`:
```json
{
  "id": "override-abc123",
  "employee_id": "emp-001",
  "agent_id": "agent-xyz",
  "tool_name": "bash",
  "tool_input": "rm -rf /tmp/production/legacy",
  "risk_level": "HIGH",
  "reason": "需要清理已迁移的旧生产数据目录，已获得业务负责人确认",
  "requested_by": "user-001",
  "requested_at": "2026-05-24T11:00:00Z",
  "status": "PENDING",
  "approved_by": null,
  "approved_at": null,
  "rejection_reason": null,
  "expires_at": null
}
```

**Errors**:
- `400` — Validation error (missing required fields, invalid risk_level)
- `401` — Not authenticated

---

### 4.2 List Override Requests

```
GET /api/permissions/overrides
```

**Query Parameters**:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| status | string | — | Filter by status: PENDING/APPROVED/REJECTED/EXPIRED |
| employee_id | string (UUID) | — | Filter by employee |
| limit | int | 50 | Max results (1-200) |
| offset | int | 0 | Pagination offset |

**Response** `200 OK`:
```json
{
  "overrides": [
    {
      "id": "override-abc123",
      "employee_id": "emp-001",
      "agent_id": "agent-xyz",
      "tool_name": "bash",
      "risk_level": "HIGH",
      "reason": "需要清理已迁移的旧生产数据目录",
      "status": "PENDING",
      "requested_by": "user-001",
      "requested_at": "2026-05-24T11:00:00Z",
      "expires_at": null
    },
    {
      "id": "override-def456",
      "employee_id": "emp-002",
      "agent_id": "agent-abc",
      "tool_name": "execute_script",
      "risk_level": "CRITICAL",
      "reason": "紧急修复生产环境数据库连接",
      "status": "APPROVED",
      "requested_by": "user-002",
      "requested_at": "2026-05-24T09:00:00Z",
      "approved_by": "admin-001",
      "approved_at": "2026-05-24T09:15:00Z",
      "expires_at": "2026-05-25T09:15:00Z"
    }
  ],
  "total": 2
}
```

---

### 4.3 Get Override Request

```
GET /api/permissions/overrides/{override_id}
```

**Response** `200 OK`: Same as Create response body.

**Errors**:
- `404` — Override request not found
- `403` — Not authorized to view this request

---

### 4.4 Approve Override Request

```
POST /api/permissions/overrides/{override_id}/approve
```

**Request Body**:
```json
{
  "comment": "确认可以执行，该目录已完成数据迁移"
}
```

| Field | Type | Required | Max Length | Description |
|-------|------|----------|------------|-------------|
| comment | string | No | 1000 | Approval comment (recorded in audit log) |

**Response** `200 OK`:
```json
{
  "id": "override-abc123",
  "status": "APPROVED",
  "approved_by": "admin-001",
  "approved_at": "2026-05-24T11:30:00Z",
  "expires_at": "2026-05-25T11:30:00Z",
  "message": "Override approved. Temporary authorization valid for 24 hours."
}
```

**Errors**:
- `404` — Override request not found
- `400` — Request already resolved (APPROVED/REJECTED/EXPIRED)
- `403` — Not authorized to approve overrides

---

### 4.5 Reject Override Request

```
POST /api/permissions/overrides/{override_id}/reject
```

**Request Body**:
```json
{
  "reason": "该操作涉及生产数据删除，需先完成变更审批流程"
}
```

| Field | Type | Required | Max Length | Description |
|-------|------|----------|------------|-------------|
| reason | string | Yes | 1000 | Reason for rejection |

**Response** `200 OK`:
```json
{
  "id": "override-abc123",
  "status": "REJECTED",
  "rejection_reason": "该操作涉及生产数据删除，需先完成变更审批流程",
  "approved_by": "admin-001",
  "approved_at": "2026-05-24T11:35:00Z",
  "expires_at": null,
  "message": "Override request rejected"
}
```

**Errors**:
- `404` — Override request not found
- `400` — Missing required field `reason`, or request already resolved
- `403` — Not authorized to reject overrides

---

## 5. Error Response Format

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Status | Meaning |
|-------------|---------|
| 400 | Bad Request — Validation error (missing fields, invalid values, length exceeded) |
| 401 | Unauthorized — Missing or invalid JWT |
| 403 | Forbidden — Not authorized for this action |
| 404 | Not Found — Resource does not exist |
| 500 | Internal Server Error |

---

## 6. Data Types Reference

### PermissionCategory
`"READ"` | `"WRITE"` | `"DELETE"` | `"EXECUTE"` | `"NETWORK"` | `"PRODUCTION"`

### RiskLevel
`"SAFE"` | `"LOW"` | `"MEDIUM"` | `"HIGH"` | `"CRITICAL"`

### PermissionAction
`"ALLOW"` | `"DENY"` | `"REQUIRE_APPROVAL"`

### PermissionDecision
`"ALLOW"` | `"DENY"` | `"REQUIRE_APPROVAL"`

### PermissionEvaluator
`"RULE_MATCHER"` | `"REASONING_JUDGE"` | `"HARDCODED"`

### OverrideStatus
`"PENDING"` | `"APPROVED"` | `"REJECTED"` | `"EXPIRED"`

### PermissionRule (full model)
```
id: UUID
name: string (max 200)
description: string (max 1000)
category: PermissionCategory
risk_level: RiskLevel
pattern: string (regex, max 500)
action: PermissionAction
priority: int (1-10)
enabled: bool
employee_id: UUID | null
git_path: string
created_at: datetime (ISO 8601)
updated_at: datetime (ISO 8601)
created_by: UUID
```

### PermissionAuditLog (full model)
```
id: int (auto-increment)
employee_id: UUID
agent_id: UUID
tool_name: string
tool_input: string (truncated to 2000 chars)
risk_level: RiskLevel
decision: PermissionDecision
evaluator: PermissionEvaluator
matched_rule_id: UUID | null
reasoning: string (max 2000)
latency_ms: int
timestamp: datetime (ISO 8601)
```

### PermissionOverrideRequest (full model)
```
id: UUID
employee_id: UUID
agent_id: UUID
tool_name: string
tool_input: string (truncated to 2000 chars)
risk_level: RiskLevel (HIGH or CRITICAL)
reason: string (max 2000)
requested_by: UUID
requested_at: datetime (ISO 8601)
status: OverrideStatus
approved_by: UUID | null
approved_at: datetime | null
rejection_reason: string (max 1000) | null
expires_at: datetime | null (24h after approval)
```
