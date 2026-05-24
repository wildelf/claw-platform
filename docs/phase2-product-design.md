# Phase 2: Dual-Layer Permission Verification (Permission Red Lines)

## 1. Background

Claw Platform Phase 1 实现了数字员工身份管理和常驻 Worker 执行能力，但权限系统存在以下核心缺陷：

### 1.1 Current Permission System (Phase 1)

当前 `PermissionController`（`backend/app/deepagents/permission.py`）采用 **二元 allow/deny** 模型：

```python
# PermissionController.is_tool_allowed()
# 1. 内置工具（read_file, write_file, bash 等）始终允许 — 无风险区分
# 2. MCP 工具检查 agent.tool_ids — 仅匹配 ID，不评估操作内容
# 3. 无人工审批流程，无审计日志
```

`SkillEventMiddleware.awrap_tool_call()` 在工具执行前拦截，但：
- 内置工具 **完全绕过** 权限检查（`_is_builtin_tool()` 硬编码白名单）
- 只判断"能否使用工具"，不判断"工具的具体操作是否安全"
- 例如：`bash` 工具始终允许，无论执行 `ls` 还是 `rm -rf /`

### 1.2 Gap Analysis

| Aspect | Phase 1 (Current) | Phase 2 (Target) |
|--------|-------------------|------------------|
| 风险评估 | 无 | 5 级风险分类 |
| 决策引擎 | 二元 allow/deny | 双层（规则 + LLM） |
| 审计 | 无 | 全量审计日志 |
| 人工审批 | 无 | 越权申请 + 审批流 |
| 内置工具 | 始终允许 | 纳入风险评估 |
| 员工约束 | 自由文本，不执行 | 结构化权限策略 |

### 1.3 Existing Dual-Layer Pattern

Nudge 系统已有 `RuleMatcher`（正则快速匹配）+ `ReasoningJudge`（LLM 推理判断）的双层模式，可直接适配为权限验证引擎。

## 2. Goals

| Goal | Metric | Target |
|------|--------|--------|
| 危险操作 100% 拦截 | 拦截率 | 100% |
| 安全操作直通延迟 | RuleMatcher 耗时 | < 50ms (P95) |
| 复杂场景判断准确率 | ReasoningJudge 准确率 | > 90% |
| 审计覆盖率 | 决策记录覆盖率 | 100% |
| 越权审批响应时间 | 管理员审批平均时间 | < 5 min |

## 3. Target Users

- **平台管理员**：配置权限规则、审批越权申请、查看审计日志
- **业务负责人**：为团队数字员工定制权限策略
- **数字员工（AI Agent）**：执行任务时接受权限验证
- **运维人员**：监控权限拦截事件、调优规则

## 4. Scenarios

### Scenario 1: 安全操作直通（Fast Path）
1. 数字员工执行 `read_file` 读取项目文档
2. `RuleMatcher` 匹配 "安全读取" 规则 → ALLOW
3. 操作执行，审计日志记录（耗时 < 50ms）

### Scenario 2: 危险操作拦截（Dual-Layer）
1. 数字员工尝试 `bash: rm -rf /tmp/production/`
2. `RuleMatcher` 未匹配明确规则 → 转入慢路径
3. `ReasoningJudge` LLM 分析：删除生产目录 → DENY
4. 操作被拦截，返回 `PermissionDeniedError`
5. 审计日志记录完整决策链

### Scenario 3: 越权申请与审批
1. 数字员工需要访问受限 API（如支付系统）
2. 权限评估 → DENY
3. 系统自动生成 `PermissionOverrideRequest`
4. 管理员收到通知，查看申请详情和理由
5. 管理员审批 → APPROVE → 临时授权（有效期 24h）
6. 员工成功执行操作

### Scenario 4: 规则管理
1. 管理员在 Web 界面创建新规则："禁止删除 `.git/` 目录"
2. 设置正则模式 `rm.*\.git(/|$)`、动作 DENY、优先级 HIGH
3. 规则立即生效，所有后续操作受此规则约束
4. 管理员可通过 Git 历史追溯规则变更

## 5. Scope

### In Scope
- 5 级风险分类体系（safe / low / medium / high / critical）
- `RuleMatcher` 权限适配（从 nudge 系统复用）
- `ReasoningJudge` 权限适配（从 nudge 系统复用）
- `PermissionRule` 实体与 CRUD API
- `PermissionAuditLog` 实体与查询 API
- `PermissionOverrideRequest` 实体与审批 API
- 权限评估端点（`POST /api/permissions/evaluate`）
- 权限中间件集成（替换现有 `PermissionController`）
- 前端：权限规则管理页面
- 前端：审计日志查看页面
- 前端：越权申请与审批页面

### Non-Goals
- RBAC（用户角色权限）— 已有 JWT auth，角色 enforcement 不在此阶段
- 多租户权限隔离 — Phase 6 范围
- 动态策略学习（自动从历史生成规则）— 未来优化
- 实时告警（Slack/Email 通知）— 可作为审批流的扩展

## 6. User Stories

| ID | As a... | I want to... | So that... |
|----|---------|-------------|-----------|
| US-1 | 管理员 | 创建和编辑权限规则 | 系统按安全策略拦截危险操作 |
| US-2 | 管理员 | 查看权限审计日志 | 追溯所有权限决策和原因 |
| US-3 | 管理员 | 审批越权申请 | 在安全控制下允许特殊操作 |
| US-4 | 业务负责人 | 为团队员工定制权限 | 权限策略匹配业务需求 |
| US-5 | 数字员工 | 执行安全操作时无延迟 | 不影响正常工作效率 |
| US-6 | 运维人员 | 查看权限拦截统计 | 了解系统安全态势 |
| US-7 | 管理员 | 禁用/启用规则 | 灵活调整安全策略 |

## 7. Architecture

### 7.1 Dual-Layer Permission Engine

```
Tool Call (tool_name, tool_input, employee_id)
         ↓
┌──────────────────────────────────────┐
│  Layer 1: Risk Classifier            │
│  - Classify risk level by tool_name  │
│    + tool_input analysis             │
│  - safe/low → ALLOW (fast path)      │
│  - medium+ → continue                │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│  Layer 2: RuleMatcher (Fast Path)    │
│  - Regex pattern matching            │
│  - Keyword detection                 │
│  - Employee constraints check        │
│  - Match → ALLOW / DENY             │
│  - No Match → continue               │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│  Layer 3: ReasoningJudge (Slow Path) │
│  - LLM evaluates action context      │
│  - Considers employee role, goal     │
│  - Returns ALLOW / DENY + reasoning  │
│  - Timeout fallback → DENY (safe)    │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│  Layer 4: Audit Logger               │
│  - Log decision, evaluator, timing   │
│  - If DENY + override possible →     │
│    create PermissionOverrideRequest  │
└──────────────────────────────────────┘
```

### 7.2 Integration Point

替换现有 `SkillEventMiddleware.awrap_tool_call()` 中的权限检查逻辑：

```python
# Before (Phase 1):
perm_controller = PermissionController(self._agent, self._storage)
result = await perm_controller.is_tool_allowed(tool_name)

# After (Phase 2):
perm_engine = PermissionEngine(self._agent, self._employee_profile, self._storage)
result = await perm_engine.evaluate_action(
    tool_name=tool_name,
    tool_input=tool_input,
    context={...}
)
# result: allowed, risk_level, evaluator, reasoning, override_request_id
```

### 7.3 Risk Classification

| Risk Level | Default Action | Evaluation | Examples |
|------------|---------------|------------|----------|
| **safe** | ALLOW | RuleMatcher only | `read_file`, `Calculator`, web_search |
| **low** | ALLOW | RuleMatcher only | `write_file` (非关键路径), `arxiv` |
| **medium** | ALLOW (logged) | Dual-layer | `write_file` (config files), `generate_image` |
| **high** | DENY unless approved | Dual-layer | `bash` (危险命令), `execute_script` |
| **critical** | DENY always | Dual-layer + hard block | `rm -rf /`, drop database, prod deploy |

### 7.4 Data Flow

```
Write path (permission rule):
  API → PermissionRuleService → Git store (primary) → SQLite (sync)

Read path (permission evaluation):
  Tool call → PermissionEngine → SQLite (rule cache) → Git (fallback)

Audit path:
  Decision → AuditLogger → SQLite (async, fire-and-forget)

Override path:
  Denied action → OverrideService → Notification → Admin approval → Temp grant
```

## 8. Data Model

### 8.1 PermissionRule

```
id: UUID
name: str (max 200)
description: str (max 1000)
category: Enum(READ, WRITE, DELETE, EXECUTE, NETWORK, PRODUCTION)
risk_level: Enum(SAFE, LOW, MEDIUM, HIGH, CRITICAL)
pattern: str (regex, max 500)
action: Enum(ALLOW, DENY, REQUIRE_APPROVAL)
priority: int (1-10, higher = checked first)
enabled: bool
employee_id: UUID | None (None = global rule)
git_path: str
created_at: datetime
updated_at: datetime
created_by: UUID (user_id)
```

### 8.2 PermissionAuditLog

```
id: UUID (auto-increment)
employee_id: UUID
agent_id: UUID
tool_name: str
tool_input: str (truncated to 2000 chars)
risk_level: Enum(SAFE, LOW, MEDIUM, HIGH, CRITICAL)
decision: Enum(ALLOW, DENY, REQUIRE_APPROVAL)
evaluator: Enum(RULE_MATCHER, REASONING_JUDGE, HARDCODED)
matched_rule_id: UUID | None
reasoning: str (max 2000)
latency_ms: int
timestamp: datetime
```

### 8.3 PermissionOverrideRequest

```
id: UUID
employee_id: UUID
agent_id: UUID
tool_name: str
tool_input: str (truncated)
risk_level: Enum(HIGH, CRITICAL)
reason: str (max 2000)
requested_by: UUID (user_id who submitted)
requested_at: datetime
status: Enum(PENDING, APPROVED, REJECTED, EXPIRED)
approved_by: UUID | None
approved_at: datetime | None
rejection_reason: str (max 1000) | None
expires_at: datetime (24h after approval)
```

### 8.4 Agent (extended)

```
... existing fields ...
permission_profile_id: UUID | None  # 关联权限配置（可选，默认使用全局规则）
```

## 9. API Endpoints

### 9.1 Permission Rules

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/permissions/rules` | List all rules (?employee_id=&enabled=) |
| GET | `/api/permissions/rules/{id}` | Get rule detail |
| POST | `/api/permissions/rules` | Create rule |
| PUT | `/api/permissions/rules/{id}` | Update rule |
| DELETE | `/api/permissions/rules/{id}` | Delete rule (soft delete → enabled=false) |
| PUT | `/api/permissions/rules/{id}/toggle` | Enable/disable rule |
| GET | `/api/permissions/rules/{id}/git-log` | Get Git history |

### 9.2 Permission Evaluation

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/permissions/evaluate` | Evaluate an action (tool_name + tool_input) |

**Request body:**
```json
{
  "employee_id": "uuid",
  "agent_id": "uuid",
  "tool_name": "bash",
  "tool_input": {"command": "rm -rf /tmp/data"},
  "context": {"working_directory": "/home/user/project"}
}
```

**Response:**
```json
{
  "allowed": false,
  "risk_level": "high",
  "decision": "DENY",
  "evaluator": "RULE_MATCHER",
  "matched_rule_id": "uuid",
  "reasoning": "Detected recursive deletion pattern matching dangerous rule #42",
  "latency_ms": 12,
  "override_request_id": "uuid"  // if override is possible
}
```

### 9.3 Audit Logs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/permissions/audit-logs` | List audit logs (?employee_id=&decision=&risk_level=&limit=) |
| GET | `/api/permissions/audit-logs/stats` | Get audit statistics (by risk level, decision, time range) |

### 9.4 Override Requests

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/permissions/overrides` | Create override request |
| GET | `/api/permissions/overrides` | List override requests (?status=pending&employee_id=) |
| GET | `/api/permissions/overrides/{id}` | Get override detail |
| POST | `/api/permissions/overrides/{id}/approve` | Approve override |
| POST | `/api/permissions/overrides/{id}/reject` | Reject override |

### 9.5 Default Rules (Seed Data)

系统初始化时自动创建以下默认规则（可被管理员修改）：

| # | Name | Category | Pattern | Action | Risk |
|---|------|----------|---------|--------|------|
| 1 | Safe file read | READ | `^(?!.*\.(env|key|pem)$).*$` | ALLOW | safe |
| 2 | Config file write | WRITE | `\.(yaml|yml|json|toml|ini)$` | ALLOW | low |
| 3 | Delete detection | DELETE | `(rm|rmdir|unlink|DROP|DELETE FROM)` | DENY | high |
| 4 | Dangerous bash | EXECUTE | `(rm\s+-rf|mkfs|dd\s+if=|chmod\s+777)` | DENY | critical |
| 5 | Production access | PRODUCTION | `(prod|production|live)` in path | REQUIRE_APPROVAL | high |
| 6 | Network allowlist | NETWORK | `^(https?://api\.allowed-domain\.com/)` | ALLOW | low |
| 7 | Secret file access | READ | `\.(env|key|pem|credentials)$` | DENY | high |
| 8 | Script execution | EXECUTE | `\.(sh|py|js|rb)$` executed via bash | ALLOW | medium |

## 10. Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|-------------|
| AC-1 | 安全操作（read_file 非敏感文件）→ RuleMatcher ALLOW，耗时 < 50ms | 时间戳对比 |
| AC-2 | `rm -rf /` → Critical 规则拦截，DENY | 审计日志验证 |
| AC-3 | 删除 `.env` 文件 → Secret 规则拦截，DENY | 审计日志验证 |
| AC-4 | 复杂 bash 命令（无明确规则）→ ReasoningJudge 判断 | 日志确认 evaluator=REASONING_JUDGE |
| AC-5 | ReasoningJudge 超时（> 5s）→ 默认 DENY（安全降级） | 模拟 LLM 超时 |
| AC-6 | 所有权限决策记录在审计日志中 | `SELECT count(*) FROM permission_audit_logs` = 操作次数 |
| AC-7 | 管理员可创建/编辑/删除规则 | API 响应 + Git commit 验证 |
| AC-8 | 越权申请流程完整（创建 → 审批 → 临时授权） | 端到端测试 |
| AC-9 | 过期越权授权自动失效 | 等待 24h 后验证 |
| AC-10 | 规则变更后立即生效（无需重启 Worker） | 创建规则 → 立即测试 |
| AC-11 | 前端规则管理页面可 CRUD 操作 | 手动验证 |
| AC-12 | 前端审计日志页面展示筛选后的日志 | 手动验证 |
| AC-13 | 前端越权申请页面支持提交和审批 | 手动验证 |
| AC-14 | 内置工具不再绕过权限检查 | 测试 `bash` 危险命令被拦截 |

## 11. Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM 判断延迟影响用户体验 | High | High | RuleMatcher 缓存 + 5s 超时降级为 DENY |
| 误报阻断正常业务操作 | High | Medium | 越权审批流程 + 规则调优机制 |
| 规则数量增长导致匹配慢 | Medium | Medium | 规则优先级索引 + 缓存热点规则 |
| 审计日志写入拖慢主流程 | Medium | Low | 异步写入（fire-and-forget），失败仅日志 |
| 规则与员工约束不一致 | Medium | Low | 规则创建时校验员工 constraints 一致性 |
| 越权授权被滥用 | High | Low | 24h 过期 + 审批留痕 + 审计可追溯 |

## 12. Rollout Plan

| Phase | Action | Owner | Timeline |
|-------|--------|-------|----------|
| 1 | 设计权限数据模型 + 默认规则 | Lisa | Day 1 |
| 2 | 后端开发（PermissionRule, PermissionEngine, API） | Wilde | Day 2-5 |
| 3 | 后端开发（AuditLogger, OverrideService, 集成中间件） | Wilde | Day 5-7 |
| 4 | 前端开发（规则管理、审计日志、越权审批页面） | Flora | Day 7-10 |
| 5 | 集成测试 + 规则调优 | Wilde + Lisa | Day 10-12 |
| 6 | UAT + 修复 | 全员 | Day 12-14 |
| 7 | 上线部署 | Wilde | Day 14 |

## 13. Related Documents

| Document | Path |
|----------|------|
| Phase 1 PRD | `docs/phase1-product-design.md` |
| Phase 1 API Reference | `docs/phase1-api.md` |
| 6-Phase Transformation PRD | `docs/qoderwake-transformation-prd.md` |
| Existing Permission Controller | `backend/app/deepagents/permission.py` |
| Existing RuleMatcher | `backend/app/application/nudge/rule_matcher.py` |
| Existing ReasoningJudge | `backend/app/application/nudge/reasoning_judge.py` |
| Skills Middleware | `backend/app/deepagents/skills_middleware.py` |
| Employee Profile Entity | `backend/app/domain/employee_profile.py` |

## 14. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-24 | Lisa | Initial Phase 2 PRD |
