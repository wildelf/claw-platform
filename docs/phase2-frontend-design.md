# Phase 2 前端设计规范 — Permission Management

## 1. 概述

本文档定义 Phase 2（Permission Management 嵌入员工详情页）的前端设计规范，包括页面结构、组件设计、状态管理、API 集成和交互流程。

**目标**：在现有的 `EmployeeProfileDetailView` 中新增 "Permissions" Tab，提供权限规则管理、审计日志查看、权限覆盖请求三大功能模块。

**范围**：
- 在员工详情页 Tab 栏新增 "Permissions" Tab（与 Files / Constraints / Working Rules 并列）
- Permissions Tab 内含三个子 Tab：Permission Rules / Audit Logs / Override Requests
- 新增 Pinia Store（permissionStore）管理权限相关状态
- 新增 API 客户端模块（permissions.ts）对接后端 Permission API
- 不新增独立路由，所有功能嵌入 `/employee-profiles/:id` 页面内

## 2. 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.x | UI 框架（Composition API） |
| TypeScript | 5.x | 类型安全 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由管理 |
| Tailwind CSS | 3.x | 样式框架 |
| Axios | 1.x | HTTP 客户端 |

## 3. 页面结构

### 3.1 目标页面

修改 `src/views/EmployeeProfileDetailView.vue`，在现有 Tab 栏中追加 "Permissions" Tab。

**现有 Tab 栏结构**：
```
Files | Constraints | Working Rules
```

**新增后**：
```
Files | Constraints | Working Rules | Permissions
```

### 3.2 Permissions Tab 内部结构

Permissions Tab 内部包含三个子 Tab 和统计卡片区：

```
┌─────────────────────────────────────────────────────────────┐
│  Permission Overview Stats (4 stat cards)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Rules     │ │Decisions │ │Blocked   │ │Pending   │       │
│  │6         │ │342 (24h) │ │1 (24h)   │ │Overrides │       │
│  │4G+2C     │ │99.7% ok  │ │1 high    │ │0         │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│  Sub-tabs: [Permission Rules] [Audit Logs] [Override Req]    │
├─────────────────────────────────────────────────────────────┤
│  [Active sub-tab content]                                    │
│  - Rules: Table of rules + Add Rule form                     │
│  - Audit: Table of decisions + Detail panel                  │
│  - Overrides: Table of requests + New Request form + Actions │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 路由变更

**无需新增路由**。所有功能在 `/employee-profiles/:id` 页面内通过 Tab 切换实现。

Permissions Tab 激活时，自动触发数据加载（rules、audit stats、override stats）。子 Tab 切换时按需加载对应数据。

## 4. 新增组件设计

### 4.1 组件清单

| 组件 | 文件路径 | 用途 |
|------|----------|------|
| PermissionStats | `src/components/permissions/PermissionStats.vue` | 顶部 4 个统计卡片 |
| PermissionRulesTable | `src/components/permissions/PermissionRulesTable.vue` | 权限规则列表表格 |
| PermissionRuleForm | `src/components/permissions/PermissionRuleForm.vue` | 新增/编辑规则表单 |
| AuditLogsTable | `src/components/permissions/AuditLogsTable.vue` | 审计日志列表表格 |
| AuditLogDetail | `src/components/permissions/AuditLogDetail.vue` | 审计日志详情面板 |
| OverrideRequestsTable | `src/components/permissions/OverrideRequestsTable.vue` | 覆盖请求列表表格 |
| OverrideRequestForm | `src/components/permissions/OverrideRequestForm.vue` | 新建覆盖请求表单 |
| OverrideRequestDetail | `src/components/permissions/OverrideRequestDetail.vue` | 覆盖请求详情面板 |

### 4.2 组件复用策略

- **表格**：使用现有 `src/components/ui/Table.vue`（slot-based cells）
- **卡片**：使用现有 `src/components/ui/Card.vue`
- **按钮**：使用现有 `src/components/ui/Button.vue`（variant: primary/secondary/danger/ghost）
- **标签**：使用现有 `src/components/ui/Badge.vue`（variant: success/warning/danger/info/default）
- **输入框**：使用现有 `src/components/ui/Input.vue`

### 4.3 组件层级

```
EmployeeProfileDetailView
└── Permissions Tab
    ├── PermissionStats
    ├── Sub-tab Bar (inline, no separate component)
    └── Active Sub-tab Content
        ├── Rules Sub-tab
        │   ├── Card (header + search + Add Rule button)
        │   │   └── PermissionRulesTable (uses ui/Table)
        │   └── Card (PermissionRuleForm, inline toggle)
        │
        ├── Audit Logs Sub-tab
        │   ├── Card (header + filters + Refresh button)
        │   │   └── AuditLogsTable (uses ui/Table)
        │   └── Card (AuditLogDetail, collapsible)
        │
        └── Override Requests Sub-tab
            ├── Card (header + New Request button)
            │   └── OverrideRequestsTable (uses ui/Table)
            ├── Card (OverrideRequestForm, inline toggle)
            └── Card (OverrideRequestDetail, collapsible)
```

## 5. 类型定义

在 `src/types/index.ts` 中新增以下类型：

```typescript
// Permission Rule
export type PermissionCategory = 'READ' | 'WRITE' | 'DELETE' | 'EXECUTE' | 'NETWORK' | 'PRODUCTION'
export type PermissionAction = 'ALLOW' | 'DENY' | 'REQUIRE_APPROVAL'
export type RiskLevel = 'safe' | 'low' | 'medium' | 'high' | 'critical'

export interface PermissionRule {
  id: string
  name: string
  category: PermissionCategory
  riskLevel: RiskLevel
  action: PermissionAction
  pattern: string          // regex pattern
  description: string
  scope: 'global' | 'employee'   // global = all employees, employee = specific
  employeeId?: string
  enabled: boolean
  createdAt?: string
  updatedAt?: string
}

// Audit Log
export interface AuditLog {
  id: string
  employeeId: string
  toolName: string
  toolInput: string
  riskLevel: RiskLevel
  decision: PermissionAction
  matchedRuleId?: string
  matchedRuleName?: string
  reasoning?: string
  evaluator: string        // e.g. "RuleMatcher"
  latencyMs: number
  timestamp: string
}

// Audit Log Stats
export interface AuditLogStats {
  totalDecisions24h: number
  allowedPercentage: number
  blocked24h: number
  highRiskBlocked: number
}

// Override Request
export type OverrideStatus = 'pending' | 'approved' | 'rejected' | 'expired'

export interface OverrideRequest {
  id: string
  employeeId: string
  toolName: string
  toolInput: string
  riskLevel: RiskLevel
  justification: string
  status: OverrideStatus
  requestedBy?: string
  requestedAt: string
  expiresAt?: string
  approvedBy?: string
  approvedAt?: string
  rejectionReason?: string
}

// Permission Stats (for overview cards)
export interface PermissionStats {
  totalRules: number
  globalRules: number
  customRules: number
  decisions24h: number
  allowedPercentage: number
  blocked24h: number
  pendingOverrides: number
}

// Evaluate Request/Response (for testing)
export interface EvaluateRequest {
  employeeId: string
  toolName: string
  toolInput: string
}

export interface EvaluateResponse {
  decision: PermissionAction
  riskLevel: RiskLevel
  matchedRule?: PermissionRule
  reasoning: string
  latencyMs: number
}
```

## 6. API 客户端设计

### 6.1 模块结构

新建 `src/api/permissions.ts`，遵循现有 `src/api/employeeProfiles.ts` 模式。

```typescript
import client from './client'
import type {
  PermissionRule,
  AuditLog,
  AuditLogStats,
  OverrideRequest,
  PermissionStats,
  EvaluateRequest,
  EvaluateResponse,
} from '@/types'

export const permissionsApi = {
  // --- Rules ---

  async listRules(params?: {
    employeeId?: string
    enabled?: boolean
  }): Promise<PermissionRule[]> {
    const { data } = await client.get('/permissions/rules', { params })
    return data
  },

  async createRule(rule: Partial<PermissionRule>): Promise<PermissionRule> {
    const { data } = await client.post('/permissions/rules', rule)
    return data
  },

  async updateRule(id: string, rule: Partial<PermissionRule>): Promise<PermissionRule> {
    const { data } = await client.put(`/permissions/rules/${id}`, rule)
    return data
  },

  async deleteRule(id: string): Promise<{ deleted: boolean }> {
    const { data } = await client.delete(`/permissions/rules/${id}`)
    return data
  },

  async toggleRule(id: string): Promise<PermissionRule> {
    const { data } = await client.put(`/permissions/rules/${id}/toggle`)
    return data
  },

  async evaluate(request: EvaluateRequest): Promise<EvaluateResponse> {
    const { data } = await client.post('/permissions/evaluate', request)
    return data
  },

  // --- Audit Logs ---

  async listAuditLogs(params?: {
    employeeId?: string
    decision?: string
    riskLevel?: string
    limit?: number
  }): Promise<AuditLog[]> {
    const { data } = await client.get('/permissions/audit-logs', { params })
    return data
  },

  async getAuditLogStats(params?: {
    employeeId?: string
  }): Promise<AuditLogStats> {
    const { data } = await client.get('/permissions/audit-logs/stats', { params })
    return data
  },

  // --- Override Requests ---

  async createOverride(request: Partial<OverrideRequest>): Promise<OverrideRequest> {
    const { data } = await client.post('/permissions/overrides', request)
    return data
  },

  async listOverrides(params?: {
    status?: string
    employeeId?: string
  }): Promise<OverrideRequest[]> {
    const { data } = await client.get('/permissions/overrides', { params })
    return data
  },

  async getOverride(id: string): Promise<OverrideRequest> {
    const { data } = await client.get(`/permissions/overrides/${id}`)
    return data
  },

  async approveOverride(id: string): Promise<OverrideRequest> {
    const { data } = await client.post(`/permissions/overrides/${id}/approve`)
    return data
  },

  async rejectOverride(id: string, reason?: string): Promise<OverrideRequest> {
    const { data } = await client.post(`/permissions/overrides/${id}/reject`, { reason })
    return data
  },

  // --- Stats ---

  async getPermissionStats(employeeId: string): Promise<PermissionStats> {
    const { data } = await client.get('/permissions/stats', { params: { employeeId } })
    return data
  },
}
```

## 7. Pinia Store 设计

新建 `src/stores/permissions.ts`，遵循现有 `src/stores/employeeProfiles.ts` 模式。

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  PermissionRule,
  AuditLog,
  AuditLogStats,
  OverrideRequest,
  PermissionStats,
  EvaluateResponse,
} from '@/types'
import { permissionsApi } from '@/api/permissions'

export const usePermissionsStore = defineStore('permissions', () => {
  // --- State ---
  const rules = ref<PermissionRule[]>([])
  const auditLogs = ref<AuditLog[]>([])
  const auditLogStats = ref<AuditLogStats | null>(null)
  const overrides = ref<OverrideRequest[]>([])
  const currentOverride = ref<OverrideRequest | null>(null)
  const currentAuditLog = ref<AuditLog | null>(null)
  const permissionStats = ref<PermissionStats | null>(null)
  const evaluateResult = ref<EvaluateResponse | null>(null)

  const loading = ref(false)
  const loadingRules = ref(false)
  const loadingAuditLogs = ref(false)
  const loadingOverrides = ref(false)
  const error = ref<string | null>(null)

  // --- Rules Actions ---
  async function fetchRules(employeeId: string, enabled?: boolean) {
    loadingRules.value = true
    error.value = null
    try {
      rules.value = await permissionsApi.listRules({ employeeId, enabled })
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch rules'
    } finally {
      loadingRules.value = false
    }
  }

  async function createRule(rule: Partial<PermissionRule>): Promise<PermissionRule> {
    const result = await permissionsApi.createRule(rule)
    return result
  }

  async function updateRule(id: string, rule: Partial<PermissionRule>): Promise<PermissionRule> {
    const result = await permissionsApi.updateRule(id, rule)
    return result
  }

  async function deleteRule(id: string): Promise<void> {
    await permissionsApi.deleteRule(id)
  }

  async function toggleRule(id: string): Promise<PermissionRule> {
    const result = await permissionsApi.toggleRule(id)
    // Update in local list
    const index = rules.value.findIndex(r => r.id === id)
    if (index !== -1) {
      rules.value[index] = result
    }
    return result
  }

  // --- Audit Logs Actions ---
  async function fetchAuditLogs(employeeId: string, params?: {
    decision?: string
    riskLevel?: string
    limit?: number
  }) {
    loadingAuditLogs.value = true
    error.value = null
    try {
      auditLogs.value = await permissionsApi.listAuditLogs({ employeeId, ...params })
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch audit logs'
    } finally {
      loadingAuditLogs.value = false
    }
  }

  async function fetchAuditLogStats(employeeId: string) {
    error.value = null
    try {
      auditLogStats.value = await permissionsApi.getAuditLogStats({ employeeId })
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch audit log stats'
    }
  }

  function selectAuditLog(log: AuditLog) {
    currentAuditLog.value = log
  }

  function clearAuditLogSelection() {
    currentAuditLog.value = null
  }

  // --- Override Requests Actions ---
  async function fetchOverrides(employeeId: string, status?: string) {
    loadingOverrides.value = true
    error.value = null
    try {
      overrides.value = await permissionsApi.listOverrides({ employeeId, status })
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch overrides'
    } finally {
      loadingOverrides.value = false
    }
  }

  async function createOverride(request: Partial<OverrideRequest>): Promise<OverrideRequest> {
    const result = await permissionsApi.createOverride(request)
    return result
  }

  async function fetchOverrideDetail(id: string) {
    loading.value = true
    error.value = null
    try {
      currentOverride.value = await permissionsApi.getOverride(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch override detail'
    } finally {
      loading.value = false
    }
  }

  async function approveOverride(id: string): Promise<OverrideRequest> {
    const result = await permissionsApi.approveOverride(id)
    // Update in local list
    const index = overrides.value.findIndex(o => o.id === id)
    if (index !== -1) {
      overrides.value[index] = result
    }
    currentOverride.value = result
    return result
  }

  async function rejectOverride(id: string, reason?: string): Promise<OverrideRequest> {
    const result = await permissionsApi.rejectOverride(id, reason)
    const index = overrides.value.findIndex(o => o.id === id)
    if (index !== -1) {
      overrides.value[index] = result
    }
    currentOverride.value = result
    return result
  }

  function selectOverride(request: OverrideRequest) {
    currentOverride.value = request
  }

  function clearOverrideSelection() {
    currentOverride.value = null
  }

  // --- Stats ---
  async function fetchPermissionStats(employeeId: string) {
    error.value = null
    try {
      permissionStats.value = await permissionsApi.getPermissionStats(employeeId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch permission stats'
    }
  }

  // --- Evaluate ---
  async function evaluate(request: { employeeId: string; toolName: string; toolInput: string }) {
    error.value = null
    try {
      evaluateResult.value = await permissionsApi.evaluate(request)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to evaluate permission'
    }
  }

  return {
    // State
    rules,
    auditLogs,
    auditLogStats,
    overrides,
    currentOverride,
    currentAuditLog,
    permissionStats,
    evaluateResult,
    loading,
    loadingRules,
    loadingAuditLogs,
    loadingOverrides,
    error,
    // Rules
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    toggleRule,
    // Audit Logs
    fetchAuditLogs,
    fetchAuditLogStats,
    selectAuditLog,
    clearAuditLogSelection,
    // Overrides
    fetchOverrides,
    createOverride,
    fetchOverrideDetail,
    approveOverride,
    rejectOverride,
    selectOverride,
    clearOverrideSelection,
    // Stats
    fetchPermissionStats,
    // Evaluate
    evaluate,
  }
})
```

### 7.1 Loading 状态拆分

Store 使用 granular loading 状态（`loadingRules`、`loadingAuditLogs`、`loadingOverrides`），使各子 Tab 可以独立显示加载状态而不互相阻塞。

## 8. Tab 结构和子 Tab 行为

### 8.1 外层 Tab（EmployeeProfileDetailView）

在 `EmployeeProfileDetailView.vue` 中扩展 `activeTab` 类型和 UI：

```typescript
// Before:
const activeTab = ref<'files' | 'constraints' | 'rules'>('files')

// After:
const activeTab = ref<'files' | 'constraints' | 'rules' | 'permissions'>('files')
```

新增 Tab 按钮：
```vue
<button
  :class="[
    'px-4 py-2 rounded-lg text-sm font-medium transition',
    activeTab === 'permissions' ? 'tab-active' : 'text-text-muted hover:text-text-primary hover:bg-bg-tertiary'
  ]"
  @click="activeTab = 'permissions'"
>
  Permissions
</button>
```

### 8.2 内层子 Tab（Permissions Tab 内部）

在 Permissions Tab 内容区内定义子 Tab 状态：

```typescript
const permissionSubTab = ref<'rules' | 'audit' | 'overrides'>('rules')
```

子 Tab 栏样式（对齐原型中的样式，使用底部边框指示激活状态）：

```vue
<div class="flex gap-0 border-b border-border-primary mb-6">
  <button
    :class="[
      'px-4 py-2.5 text-sm font-medium transition-colors',
      permissionSubTab === 'rules'
        ? 'text-accent-primary border-b-2 border-accent-primary'
        : 'text-text-secondary hover:text-text-primary'
    ]"
    @click="permissionSubTab = 'rules'"
  >Permission Rules</button>
  <button
    :class="[
      'px-4 py-2.5 text-sm font-medium transition-colors',
      permissionSubTab === 'audit'
        ? 'text-accent-primary border-b-2 border-accent-primary'
        : 'text-text-secondary hover:text-text-primary'
    ]"
    @click="permissionSubTab = 'audit'"
  >Audit Logs</button>
  <button
    :class="[
      'px-4 py-2.5 text-sm font-medium transition-colors',
      permissionSubTab === 'overrides'
        ? 'text-accent-primary border-b-2 border-accent-primary'
        : 'text-text-secondary hover:text-text-primary'
    ]"
    @click="permissionSubTab = 'overrides'"
  >Override Requests</button>
</div>
```

### 8.3 子 Tab 数据加载策略

| 事件 | 行为 |
|------|------|
| 外层 Tab 切换到 "permissions" | 加载 `fetchPermissionStats(employeeId)`、`fetchRules(employeeId)`、`fetchAuditLogStats(employeeId)`、`fetchOverrides(employeeId)` |
| 子 Tab 切换到 "rules" | 如果 rules 为空则 `fetchRules(employeeId)` |
| 子 Tab 切换到 "audit" | 如果 auditLogs 为空则 `fetchAuditLogs(employeeId, { limit: 50 })` |
| 子 Tab 切换到 "overrides" | 如果 overrides 为空则 `fetchOverrides(employeeId)` |
| 表单提交成功 | 刷新对应列表（rules / overrides） |
| 规则 toggle / delete | 刷新 rules 列表或在本地更新 |

## 9. 表单模式

### 9.1 Create Rule 表单

**触发方式**：点击 "Add Rule" 按钮，在表格下方内联展开表单 Card（原型中的 `create-rule-inline` 模式）。

**表单字段**：

| 字段 | 类型 | 必填 | 验证 |
|------|------|------|------|
| Rule Name | Input (text) | 是 | max 100 |
| Category | Select | 是 | READ/WRITE/DELETE/EXECUTE/NETWORK/PRODUCTION |
| Risk Level | Select | 是 | safe/low/medium/high/critical |
| Action | Select | 是 | ALLOW/DENY/REQUIRE_APPROVAL |
| Regex Pattern | Input (mono font) | 是 | 有效的正则表达式 |
| Description | Textarea | 否 | max 500 |

**表单布局**：
- 第一行：Rule Name + Category（2 列 grid）
- 第二行：Risk Level + Action（2 列 grid）
- 第三行：Regex Pattern（全宽，使用 mono 字体）
- 第四行：Description（全宽 textarea）
- 底部：Cancel + Add Rule（右对齐）

**正则验证**：
- 提交前使用 `new RegExp(pattern)` 测试正则有效性
- 无效时显示红色错误提示

**提交行为**：
- `scope` 字段自动设为 `'employee'`
- `employeeId` 从路由参数获取
- 提交成功后：关闭表单、刷新规则列表、显示成功 Toast

### 9.2 Create Override 表单

**触发方式**：点击 "New Request" 按钮，在表格下方内联展开表单 Card。

**表单字段**：

| 字段 | 类型 | 必填 | 验证 |
|------|------|------|------|
| Tool Name | Input (text, mono) | 是 | max 100 |
| Risk Level | Select | 是 | high/critical（覆盖请求仅针对高风险操作） |
| Tool Input | Textarea (mono) | 是 | max 1000 |
| Business Justification | Textarea | 是 | min 20, max 500 |

**表单布局**：
- 第一行：Tool Name + Risk Level（2 列 grid）
- 第二行：Tool Input（全宽 textarea，2 行）
- 第三行：Business Justification（全宽 textarea，3 行）
- 底部：Cancel + Submit Request（右对齐）

**提交行为**：
- `employeeId` 从路由参数获取
- 提交成功后：关闭表单、刷新覆盖请求列表、显示成功 Toast

### 9.3 表单状态管理

每个表单使用本地 `ref` 管理状态：

```typescript
const showCreateRuleForm = ref(false)
const ruleForm = ref({
  name: '',
  category: 'READ' as PermissionCategory,
  riskLevel: 'safe' as RiskLevel,
  action: 'ALLOW' as PermissionAction,
  pattern: '',
  description: '',
})
const ruleFormErrors = ref<Record<string, string>>({})
const submitting = ref(false)
```

## 10. 表格模式（使用 ui/Table）

### 10.1 Permission Rules 表格

**列定义**：
```typescript
const ruleColumns = [
  { key: 'name', label: 'Name' },
  { key: 'category', label: 'Category', width: '110px' },
  { key: 'riskLevel', label: 'Risk', width: '90px' },
  { key: 'action', label: 'Action', width: '120px' },
  { key: 'pattern', label: 'Pattern' },
  { key: 'scope', label: 'Scope', width: '110px' },
  { key: 'actions', label: 'Actions', width: '160px' }
]
```

**Slot 自定义**：
- `#cell-name`：显示规则名称，custom 规则（scope=employee）使用 `text-accent-light` 高亮
- `#cell-category`：使用 `<Badge>` 显示 category（info variant）
- `#cell-riskLevel`：根据 risk level 显示颜色（safe=绿色, low=绿色, medium=黄色, high=红色, critical=红色加粗）
- `#cell-action`：使用 `<Badge>` 显示 action（ALLOW=success, DENY=danger, REQUIRE_APPROVAL=warning）
- `#cell-pattern`：mono 字体 + `truncate-cell` 类（`overflow-hidden text-ellipsis whitespace-nowrap max-w-[240px]`）
- `#cell-scope`：Global 显示普通文本，employee 显示 `<Badge variant="default">This employee</Badge>`
- `#cell-actions`：Edit（ghost）+ Disable/Enable（ghost）+ Remove（danger，仅 employee scope）

**行样式**：
- Custom rules（scope=employee）行添加 `bg-accent-primary/5` 背景色以区分
- hover 时 `bg-bg-hover transition-colors`

### 10.2 Audit Logs 表格

**列定义**：
```typescript
const auditColumns = [
  { key: 'timestamp', label: 'Time', width: '120px' },
  { key: 'toolName', label: 'Tool', width: '120px' },
  { key: 'toolInput', label: 'Input' },
  { key: 'riskLevel', label: 'Risk', width: '90px' },
  { key: 'decision', label: 'Decision', width: '100px' },
  { key: 'evaluator', label: 'Evaluator', width: '110px' },
  { key: 'latencyMs', label: 'Latency', width: '80px' },
  { key: 'actions', label: 'Actions', width: '80px' }
]
```

**Slot 自定义**：
- `#cell-timestamp`：mono 字体，显示相对时间（如 `14:32:01`）或 timeAgo
- `#cell-toolName`：mono 字体
- `#cell-toolInput`：mono 字体 + truncate，高风险 input 使用 `text-status-error`
- `#cell-riskLevel`：文字颜色（safe/low=绿色, medium=黄色, high/critical=红色）
- `#cell-decision`：`<Badge>`（ALLOW=success, DENY=danger）
- `#cell-evaluator`：`<Badge variant="default">` 显示 evaluator 名称
- `#cell-latencyMs`：mono 字体，显示如 `8ms`
- `#cell-actions`：Detail 按钮（ghost, sm），点击后展开详情面板

### 10.3 Override Requests 表格

**列定义**：
```typescript
const overrideColumns = [
  { key: 'id', label: 'ID', width: '90px' },
  { key: 'toolName', label: 'Tool', width: '120px' },
  { key: 'justification', label: 'Reason' },
  { key: 'riskLevel', label: 'Risk', width: '90px' },
  { key: 'status', label: 'Status', width: '110px' },
  { key: 'requestedAt', label: 'Requested', width: '110px' },
  { key: 'actions', label: 'Actions', width: '80px' }
]
```

**Slot 自定义**：
- `#cell-id`：mono 字体，`text-accent-primary`
- `#cell-toolName`：mono 字体
- `#cell-justification`：truncate 文本
- `#cell-riskLevel`：文字颜色（high/critical=红色）
- `#cell-status`：`<Badge>`（pending=warning, approved=success, rejected=danger, expired=default）
- `#cell-requestedAt`：timeAgo 格式（如 `3h ago`）
- `#cell-actions`：View 按钮（ghost, sm），点击后展开详情面板

## 11. 状态管理（Loading / Error / Empty）

### 11.1 Loading 状态

**列表加载**：使用 skeleton 骨架屏（与现有 `employeeProfilesStore.loading` 模式一致）

```vue
<div v-if="permissionsStore.loadingRules" class="text-center py-12">
  <p class="text-text-muted text-sm">Loading rules...</p>
</div>
```

**按钮操作**：使用 `Button` 组件的 `loading` prop

```vue
<Button variant="primary" :loading="submitting" @click="handleSubmit">
  Add Rule
</Button>
```

### 11.2 Error 状态

**列表错误**：
```vue
<div v-else-if="permissionsStore.error" class="text-center py-12">
  <p class="text-red-400 mb-4">{{ permissionsStore.error }}</p>
  <Button variant="primary" @click="handleRetry">Retry</Button>
</div>
```

**表单错误**：字段级错误使用 `<Input>` 的 `error` prop 显示

### 11.3 Empty 状态

**规则为空**：
```vue
<div v-else-if="permissionsStore.rules.length === 0" class="text-center py-16 border border-border-primary border-dashed rounded-xl">
  <svg class="w-10 h-10 text-text-muted mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
  </svg>
  <p class="text-text-muted text-sm mb-4">No permission rules configured</p>
  <Button variant="primary" @click="showCreateRuleForm = true">Add First Rule</Button>
</div>
```

**审计日志为空**：
```vue
<div class="text-center py-12">
  <p class="text-text-muted text-sm">No audit log entries found for this employee</p>
</div>
```

**覆盖请求为空**：
```vue
<div class="text-center py-12">
  <p class="text-text-muted text-sm mb-4">No override requests</p>
  <Button variant="secondary" size="sm" @click="showOverrideForm = true">New Request</Button>
</div>
```

### 11.4 成功反馈

操作成功后使用 Toast 通知（项目现有的 toast/notification 机制）：

| 操作 | 消息 |
|------|------|
| 创建规则成功 | "Permission rule created successfully" |
| 更新规则成功 | "Permission rule updated successfully" |
| 删除规则成功 | "Permission rule removed" |
| 切换规则成功 | "Rule enabled/disabled" |
| 创建覆盖请求成功 | "Override request submitted" |
| 批准覆盖请求成功 | "Override request approved" |
| 拒绝覆盖请求成功 | "Override request rejected" |
| 刷新审计日志成功 | "Audit logs refreshed" |

## 12. 样式规范

### 12.1 颜色映射

| 元素 | 色值 | Tailwind 类 |
|------|------|-------------|
| 背景色 | `#0d1117` | `bg-bg-primary` |
| 卡片背景 | `#161b22` | `bg-bg-card` |
| 侧栏背景 | `#161b22` | `bg-bg-secondary` |
| 边框色 | `#30363d` | `border-border-primary` |
| 主文字 | `#e6edf3` | `text-text-primary` |
| 次要文字 | `#8b949e` | `text-text-secondary` |
| 辅助文字 | `#6e7681` | `text-text-muted` |
| 主题色 | `#58a6ff` | `text-accent-primary` |
| 主题浅色 | `#79c0ff` | `text-accent-light` |
| 成功色 | `#3fb950` | `text-status-active` |
| 警告色 | `#d29922` | `text-status-paused` |
| 错误色 | `#f85149` | `text-status-error` |

### 12.2 特殊样式

**Custom Rule 行高亮**：`bg-accent-primary/5`（5% 透明度主题色背景）

**Pattern 列截断**：
```css
.truncate-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 240px;
}
```

**Mono 字体**：继承项目中已有的 `code-editor` 类（`'SF Mono', 'Fira Code', monospace`）

### 12.3 统计卡片布局

```vue
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
  <div class="bg-bg-card border border-border-primary rounded-xl p-4">
    <div class="text-sm text-text-muted mb-2">Applied Rules</div>
    <div class="text-2xl font-bold text-accent-primary">6</div>
    <div class="text-xs text-text-muted mt-1">4 global + 2 custom</div>
  </div>
  <!-- 3 more cards -->
</div>
```

## 13. 交互规范

### 13.1 规则操作

| 操作 | 交互 | 确认 |
|------|------|------|
| Add Rule | 展开内联表单 | 无 |
| Edit Rule | TODO：展开内联表单（与 Add 复用） | 无 |
| Delete Rule | 仅 employee scope 可删除 | 弹出确认对话框 |
| Enable/Disable | 直接调用 toggle API | 无，按钮文字即时切换 |
| View Global Rules | 跳转到全局规则管理页（后续 Phase） | - |

### 13.2 审计日志操作

| 操作 | 交互 |
|------|------|
| View Detail | 点击 Detail 按钮，下方展开详情面板 |
| Close Detail | 点击 Close 按钮或点击其他行 |
| Request Override | 从详情页点击 "Request Override"，跳转到 Override 表单并预填 tool/input |
| Refresh | 点击 Refresh 按钮，重新拉取列表 |
| Filter by Decision | Select 下拉框（All / ALLOW / DENY） |

### 13.3 覆盖请求操作

| 操作 | 交互 | 确认 |
|------|------|------|
| New Request | 展开内联表单 | 无 |
| View Detail | 点击 View 按钮，下方展开详情面板 | 无 |
| Approve | 在详情面板点击 Approve 按钮 | 弹出确认对话框 |
| Reject | 在详情面板点击 Reject 按钮 | 弹出确认对话框 + 输入拒绝理由 |

### 13.4 确认对话框

使用项目现有的 `confirm()` 模式或封装 `ConfirmDialog` 组件：

```typescript
// 删除规则
async function handleDeleteRule(ruleId: string, ruleName: string) {
  if (!confirm(`Remove permission rule "${ruleName}"?`)) return
  try {
    await permissionsStore.deleteRule(ruleId)
    await permissionsStore.fetchRules(profileId)
    showToast('Permission rule removed', 'success')
  } catch (e) {
    showToast('Failed to remove rule', 'error')
  }
}

// 批准覆盖
async function handleApprove(overrideId: string) {
  if (!confirm('Approve this override request? This will allow the requested operation for 24 hours.')) return
  try {
    await permissionsStore.approveOverride(overrideId)
    showToast('Override request approved', 'success')
  } catch (e) {
    showToast('Failed to approve override', 'error')
  }
}
```

## 14. 开发排期

| 任务 | 负责人 | 工时 | 依赖 |
|------|--------|------|------|
| 类型定义（types/index.ts） | Flora | 0.25d | API 契约确认 |
| API 客户端模块（api/permissions.ts） | Flora | 0.5d | 后端 API 可用 |
| Pinia Store（stores/permissions.ts） | Flora | 0.5d | API 模块完成 |
| PermissionStats 组件 | Flora | 0.25d | Store 完成 |
| PermissionRulesTable + Form | Flora | 1d | Store + Table 组件 |
| AuditLogsTable + Detail | Flora | 0.75d | Store + Table 组件 |
| OverrideRequestsTable + Form + Detail | Flora | 1d | Store + Table 组件 |
| EmployeeProfileDetailView 集成 | Flora | 0.5d | 所有子组件完成 |
| 联调 + 修复 | Flora + Wilde | 1d | 全部 API 可用 |
| UI 优化 + 响应式 | Flora | 0.5d | 联调完成 |

**总工时**：约 5.25 人天

## 15. 开发清单

### 15.1 基础设施

- [ ] 在 `src/types/index.ts` 中添加所有权限相关类型
- [ ] 创建 `src/api/permissions.ts` 并实现所有 API 方法
- [ ] 创建 `src/stores/permissions.ts` 并实现状态管理
- [ ] 确保 `src/api/client.ts` 的 error interceptor 正确处理 403/404

### 15.2 组件开发

- [ ] 创建 `src/components/permissions/` 目录
- [ ] 实现 `PermissionStats.vue`（4 个统计卡片）
- [ ] 实现 `PermissionRulesTable.vue`（规则表格，含 slot 自定义）
- [ ] 实现 `PermissionRuleForm.vue`（内联表单，含正则验证）
- [ ] 实现 `AuditLogsTable.vue`（审计日志表格）
- [ ] 实现 `AuditLogDetail.vue`（详情面板）
- [ ] 实现 `OverrideRequestsTable.vue`（覆盖请求表格）
- [ ] 实现 `OverrideRequestForm.vue`（内联表单）
- [ ] 实现 `OverrideRequestDetail.vue`（详情面板 + 审批操作）

### 15.3 视图集成

- [ ] 修改 `EmployeeProfileDetailView.vue`：
  - [ ] 扩展 `activeTab` 类型加入 `'permissions'`
  - [ ] 添加 "Permissions" Tab 按钮
  - [ ] 添加 Permissions Tab 内容区（stats + 子 Tab 栏 + 3 个子 Tab 内容）
  - [ ] 实现子 Tab 切换逻辑
  - [ ] 实现进入 Permissions Tab 时自动加载数据
- [ ] 确保左侧边栏布局不受影响

### 15.4 交互与状态

- [ ] 实现所有表单提交逻辑（Create Rule, Create Override）
- [ ] 实现规则 toggle（Enable/Disable）
- [ ] 实现规则删除（含确认对话框）
- [ ] 实现审计日志详情展开/收起
- [ ] 实现覆盖请求详情展开/收起
- [ ] 实现审批/拒绝操作（含确认对话框）
- [ ] 实现所有 loading 状态
- [ ] 实现所有 error 状态和 retry
- [ ] 实现所有 empty 状态
- [ ] 实现成功 Toast 通知

### 15.5 样式与体验

- [ ] 验证深色主题一致性（对比原型）
- [ ] 验证 custom rule 行高亮样式
- [ ] 验证所有 Badge 颜色映射
- [ ] 验证 mono 字体在 pattern/input 列的应用
- [ ] 验证 truncate 效果
- [ ] 验证响应式布局（md 网格切换）
- [ ] 验证 Tab 切换动画流畅

### 15.6 验收标准

| 编号 | 标准 | 验证方式 |
|------|------|---------|
| AC-P1 | Permissions Tab 正确显示在 Tab 栏 | 视觉检查 |
| AC-P2 | 统计卡片数据与 API 返回一致 | 对比 API |
| AC-P3 | Rules 子 Tab 正确显示所有规则 | 对比 API |
| AC-P4 | 新增规则后列表自动刷新 | 操作后验证 |
| AC-P5 | 规则 toggle 即时生效 | 操作后验证 |
| AC-P6 | 删除规则有确认对话框 | 手动测试 |
| AC-P7 | Audit Logs 正确显示决策记录 | 对比 API |
| AC-P8 | 审计日志详情面板可展开/收起 | 手动测试 |
| AC-P9 | Override Requests 列表正确 | 对比 API |
| AC-P10 | 新建覆盖请求后列表刷新 | 操作后验证 |
| AC-P11 | 审批/拒绝操作有确认对话框 | 手动测试 |
| AC-P12 | Loading/Error/Empty 状态正确 | 手动触发 |
| AC-P13 | 深色主题样式一致 | 视觉检查 |
| AC-P14 | 表单验证正确（正则、必填） | 手动测试 |
| AC-P15 | 子 Tab 切换数据按需加载 | 网络面板验证 |
