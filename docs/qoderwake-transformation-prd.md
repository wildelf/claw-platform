# Claw Platform → QoderWake-Like 24/7 AI Digital Employee Platform

## Comprehensive 6-Phase Product Requirements Document

---

## 1. Executive Summary

Claw Platform 当前是一个 AI Agent 管理平台。本 PRD 定义了将其转型为 **QoderWake-like 24/7 AI 数字员工平台** 的完整 6 阶段路线图。

核心愿景：将 AI Agent 从"被动工具"升级为"主动数字员工"，具备持久身份、跨会话记忆、可进化技能、分工协作、权限红线和多租户组织能力。

**5 层架构模型**：
| Layer | Name | Core Concept |
|-------|------|-------------|
| 1 | Identity | Git-managed employee profiles |
| 2 | Memory | FTS5 cross-session memory |
| 3 | Skills | Auto-evolving tool/skill registry |
| 4 | Division | Workflow routing and team collaboration |
| 5 | Red Lines | Dual-layer permission verification |

---

## 2. Background and Evidence

### 2.1 Current State
- Claw Platform 已有基础 Agent 管理功能（CRUD、工具绑定、模型配置）
- 已有 FTS5 记忆系统（跨会话对话检索）
- 已有 DeepAgents 引擎集成（LangGraph-based）
- **缺失**：持久身份管理、常驻执行能力、权限控制、分工协作、技能进化

### 2.2 Market Signal: QoderWake
QoderWake 代表了一种新型 AI 开发平台范式：
- **Git-Managed Identity**: 所有配置以 Markdown 文件存储，Git 版本控制
- **24/7 Always-On**: Worker 守护进程持续运行，自动执行任务
- **Anti-Rot Governance**: 自动检测配置漂移、文档过期、测试退化
- **Multi-Tenant**: 组织级隔离，团队协作

### 2.3 Business Value
| Stakeholder | Value |
|------------|-------|
| 企业用户 | 降低 AI 使用门槛，数字员工替代重复性工作 |
| 开发者 | Git 工作流管理 AI 配置，与现有 DevOps 集成 |
| 运维 | 24/7 自动运行，减少人工干预 |
| 管理者 | 多租户隔离，团队级 AI 能力分配 |

---

## 3. Goals and Success Criteria

### 3.1 Overall Goals

| Goal | Success Metric | Target |
|------|---------------|--------|
| 完整的数字员工生命周期 | 从创建到退休全流程可追溯 | 100% Git commit 覆盖 |
| 24/7 无人值守运行 | Worker uptime | > 99.5% |
| 任务自动执行 | 任务响应延迟 | < 5s (P95) |
| 权限安全 | 危险操作拦截率 | 100% |
| 技能自动进化 | 技能使用频率 → 优化优先级 | Top 10 skills auto-optimized |
| 多租户隔离 | 组织间数据零泄漏 | 0 incidents |

### 3.2 Phase-Level Goals

| Phase | Goal | Done When |
|-------|------|-----------|
| 1 | Git 身份 + 常驻 Worker | 员工可创建、任务可自动执行 |
| 2 | 双层权限验证 | 危险操作被拦截，安全操作直通 |
| 3 | 确定性工作流引擎 | 多员工协作完成复杂任务 |
| 4 | 防退化治理 | 自动检测并修复配置漂移 |
| 5 | 会话检查点 + 崩溃恢复 | 长时间任务可中断恢复 |
| 6 | 多租户组织支持 | 多团队隔离使用 |

---

## 4. Users and Scenarios

### 4.1 User Personas

| Persona | Role | Primary Need |
|---------|------|-------------|
| **Platform Admin** | 平台管理员 | 全局配置、监控、运维 |
| **Team Lead** | 团队负责人 | 创建和管理团队数字员工 |
| **Developer (Wilde)** | 后端开发 | API 开发、Worker 架构、权限引擎 |
| **Frontend Dev (Flora)** | 前端开发 | 用户界面、交互体验 |
| **Digital Employee** | AI 数字员工 | 执行任务、遵循约束、持续学习 |
| **Business User** | 业务使用者 | 提交任务、查看结果 |

### 4.2 Key Scenarios

#### Scenario A: 创建并启动数字员工 (Phase 1)
1. Admin 在 Web 界面创建员工，填写角色、目标、约束
2. 系统生成 Markdown 文件，Git commit，同步 SQLite
3. 用户通过 API 提交任务到队列
4. Worker 守护进程自动认领并执行任务
5. 执行结果通过 SSE 推送给前端

#### Scenario B: 权限红线拦截 (Phase 2)
1. 数字员工尝试执行敏感操作（如删除生产数据）
2. RuleMatcher 快速匹配规则 → 命中 → 拦截
3. 复杂场景 → ReasoningJudge LLM 判断 → 批准/拒绝
4. 审计日志记录完整决策链

#### Scenario C: 多员工协作 (Phase 3)
1. 用户提交复杂任务："分析竞品并生成报告"
2. 工作流引擎拆解为子任务
3. 路由到不同专业员工（Researcher、Analyst、Writer）
4. 每个员工独立完成子任务
5. 引擎汇总结果，返回完整报告

#### Scenario D: 防退化治理 (Phase 4)
1. 系统定期扫描所有员工配置
2. 检测：配置文件与 DB 不一致、规则过期、技能未更新
3. 自动生成修复建议
4. Admin 确认后自动修复

#### Scenario E: 长时间任务恢复 (Phase 5)
1. 员工执行耗时任务（如大代码库重构）
2. 定期保存检查点到存储
3. Worker 崩溃 → 新 Worker 启动
4. 从最新检查点恢复，继续执行

#### Scenario F: 多团队隔离 (Phase 6)
1. 组织 A 和组织 B 使用同一平台
2. 员工、任务、记忆完全隔离
3. 组织级技能共享池
4. 管理员跨组织查看使用统计

---

## 5. Scope

### 5.1 In Scope (All 6 Phases)

| Phase | Feature | Deliverables |
|-------|---------|-------------|
| **Phase 1** | Git-Managed Identity + Always-On Worker | EmployeeProfile CRUD, Git store, Worker daemon, Operations API, Frontend UI |
| **Phase 2** | Dual-Layer Permission Verification | RuleMatcher, ReasoningJudge, Permission API, Audit logs, Frontend permission UI |
| **Phase 3** | Deterministic Workflow Engine | Workflow definition (YAML), Task router, Multi-employee orchestration, Frontend workflow UI |
| **Phase 4** | Anti-Rot Governance | Config drift detector, Doc staleness checker, Test rot analyzer, Auto-fix pipeline, Governance dashboard |
| **Phase 5** | Session Checkpointing + Crash Recovery | Checkpoint manager, State serialization, Resume-from-checkpoint, Frontend progress UI |
| **Phase 6** | Multi-Tenant Organization | Organization CRUD, Tenant isolation, Org-level skill pool, Cross-org analytics, Admin console |

### 5.2 Non-Goals

- **计费/支付系统**: 不在本次转型范围
- **移动端 App**: 仅 Web 端
- **自定义 LLM 训练**: 仅使用现有模型 API
- **CI/CD 集成**: 仅提供 API，不内置 CI/CD 插件
- **第三方 SSO**: 仅支持内置认证

### 5.3 Dependencies

| Dependency | Source | Impact |
|-----------|--------|--------|
| DeepAgents Engine | Existing | 任务执行基础 |
| FTS5 Memory | Existing | 跨会话记忆 |
| LangGraph | External | 工作流编排 |
| Redis | Existing | Worker 协调 |
| Git | System | 身份存储 |

---

## 6. Phase Details

### Phase 1: Git-Managed Identity + Always-On Worker Daemon

**Status**: Backend ✅ | Frontend ⏳

#### 6.1.1 Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| P1-R1 | EmployeeProfile entity with Markdown-backed storage | P0 |
| P1-R2 | Git version control for all profile changes | P0 |
| P1-R3 | Dual persistence (Git primary, SQLite sync) | P0 |
| P1-R4 | Worker daemon with heartbeat (30s interval) | P0 |
| P1-R5 | Redis-based task queue (BRPOPLPUSH) | P0 |
| P1-R6 | Crash recovery for stale workers | P1 |
| P1-R7 | Operations API (worker status, queue stats, task management) | P1 |
| P1-R8 | Frontend: Employee list, detail, Operations dashboard | P1 |

#### 6.1.2 Architecture

```
Employee Profile Flow:
  API → EmployeeProfileService → GitIdentityStore (primary)
                                  ↓
                            SQLiteStorage (sync)

Worker Flow:
  WorkerService → HeartbeatManager → Redis
                 ↓
           Task Polling → DeepAgentsRunner → Task Complete
```

#### 6.1.3 Data Model

```
EmployeeProfile:
  id, name, role, goal, backstory, personality,
  constraints (markdown), working_rules (markdown),
  status (ACTIVE/PAUSED/RETIRED), user_id, organization_id,
  git_path, created_at, updated_at

Agent (extended):
  ... existing fields ...
  employee_profile_id: UUID | None
```

#### 6.1.4 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/employee-profiles` | List all profiles |
| GET | `/api/employee-profiles/{id}` | Get profile detail |
| POST | `/api/employee-profiles` | Create profile |
| PUT | `/api/employee-profiles/{id}` | Update profile |
| DELETE | `/api/employee-profiles/{id}` | Delete profile |
| GET | `/api/employee-profiles/{id}/files/{filename}` | Get raw file |
| PUT | `/api/employee-profiles/{id}/files/{filename}` | Update raw file |
| GET | `/api/employee-profiles/{id}/git-log` | Get Git history |
| POST | `/api/agents/{id}/tasks?mode=queued` | Submit queued task |
| GET | `/api/agents/{id}/tasks/{task_id}` | Get task status |
| GET | `/api/operations/worker/status` | Worker status |
| POST | `/api/operations/worker/restart` | Restart worker |
| POST | `/api/operations/worker/stop` | Stop worker |
| GET | `/api/operations/queue/stats` | Queue statistics |
| POST | `/api/operations/queue/clear` | Clear queue |
| GET | `/api/operations/tasks` | List tasks |
| POST | `/api/operations/tasks/{id}/cancel` | Cancel task |

#### 6.1.5 Frontend Pages

| Page | Description | Prototype |
|------|-------------|-----------|
| Employee List | Card grid with search/filter | `docs/prototype-employee-profiles.html` |
| Employee Detail | Split view (info + code editor) | `docs/prototype-employee-detail.html` |
| Operations Dashboard | 3 tabs (Worker, Queue, Tasks) | `docs/prototype-worker-dashboard.html` |

#### 6.1.6 Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | Create profile → Git directory has corresponding files |
| AC-2 | Create profile → SQLite has corresponding record |
| AC-3 | Update profile → Git commit history has new entry |
| AC-4 | Delete profile → Git and SQLite both cleaned |
| AC-5 | Worker starts → Redis has heartbeat record |
| AC-6 | Submit task → Worker starts execution within 5s |
| AC-7 | Worker crashes → New worker recovers uncompleted tasks |
| AC-8 | Operations API returns correct worker status |
| AC-9 | Cancel queued task → Task immediately marked cancelled |
| AC-10 | Restart signal → Worker exits within 60s |

#### 6.1.7 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Git operations slow API response | Medium | Medium | Async Git ops, timeout fallback |
| SQLite/Git data inconsistency | High | Low | Periodic validation, Git wins |
| Single worker SPOF | High | Medium | Heartbeat + task recovery |
| Redis connection loss | High | Low | Auto-reconnect, degrade to logging |

---

### Phase 2: Dual-Layer Permission Verification (Permission Red Lines)

**Status**: Not Started

#### 6.2.1 Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| P2-R1 | Permission rule definition (YAML-based) | P0 |
| P2-R2 | RuleMatcher: fast rule-based evaluation | P0 |
| P2-R3 | ReasoningJudge: LLM-based complex judgment | P0 |
| P2-R4 | Permission audit log | P0 |
| P2-R5 | Permission override workflow (admin approval) | P1 |
| P2-R6 | Frontend: Permission rule management UI | P1 |
| P2-R7 | Frontend: Audit log viewer | P2 |

#### 6.2.2 Architecture

```
Action Request
     ↓
┌─────────────────────┐
│   RuleMatcher       │ ← Fast path: regex, keywords, patterns
│   (Rule-Based)      │
└────────┬────────────┘
         │ Match → ALLOW/DENY
         │ No Match ↓
┌─────────────────────┐
│   ReasoningJudge    │ ← Slow path: LLM judgment
│   (LLM-Based)       │
└────────┬────────────┘
         │
    Final Decision + Audit Log
```

#### 6.2.3 Permission Categories

| Category | Action | Default | Evaluation |
|----------|--------|---------|------------|
| **Read** | View files, read data | ALLOW | RuleMatcher only |
| **Write** | Create/edit files | ALLOW | RuleMatcher only |
| **Delete** | Remove files/data | DENY | RuleMatcher + ReasoningJudge |
| **Execute** | Run commands | DENY | Dual-layer |
| **Network** | External API calls | ALLOW | RuleMatcher (allowlist) |
| **Production** | Prod environment ops | DENY | Dual-layer + Admin approval |

#### 6.2.4 Data Model

```
PermissionRule:
  id, name, description, category, pattern (regex),
  action (ALLOW/DENY), priority, enabled, created_at

PermissionAuditLog:
  id, employee_id, action, resource, decision,
  evaluator (RuleMatcher/ReasoningJudge),
  reasoning, timestamp

PermissionOverrideRequest:
  id, employee_id, action, resource,
  requested_by, approved_by, status,
  reason, created_at, approved_at
```

#### 6.2.5 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/permissions/rules` | List permission rules |
| POST | `/api/permissions/rules` | Create rule |
| PUT | `/api/permissions/rules/{id}` | Update rule |
| DELETE | `/api/permissions/rules/{id}` | Delete rule |
| POST | `/api/permissions/evaluate` | Evaluate action |
| GET | `/api/permissions/audit-logs` | List audit logs |
| POST | `/api/permissions/overrides` | Request override |
| GET | `/api/permissions/overrides` | List override requests |
| POST | `/api/permissions/overrides/{id}/approve` | Approve override |

#### 6.2.6 Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | Safe file read → RuleMatcher allows (< 100ms) |
| AC-2 | Delete production file → Dual-layer denies |
| AC-3 | Complex scenario → ReasoningJudge evaluates correctly |
| AC-4 | All decisions logged with reasoning |
| AC-5 | Admin can approve override requests |
| AC-6 | Frontend shows real-time audit log stream |

#### 6.2.7 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM judgment slow | Medium | High | RuleMatcher cache, timeout fallback |
| False positives block legitimate ops | High | Medium | Override workflow, rule tuning |
| Rule complexity grows unmanageable | Medium | Medium | Rule versioning, testing framework |

---

### Phase 3: Deterministic Workflow Engine (Division of Labor)

**Status**: Not Started

#### 6.3.1 Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| P3-R1 | Workflow definition (YAML-based) | P0 |
| P3-R2 | Task decomposition engine | P0 |
| P3-R3 | Employee routing (skill-based assignment) | P0 |
| P3-R4 | Task dependency graph | P0 |
| P3-R5 | Parallel execution support | P1 |
| P3-R6 | Frontend: Workflow builder UI | P1 |
| P3-R7 | Frontend: Workflow execution monitor | P1 |

#### 6.3.2 Architecture

```
User submits complex task
         ↓
┌─────────────────────────┐
│  Workflow Engine         │
│  1. Parse task           │
│  2. Match workflow def   │
│  3. Decompose sub-tasks  │
│  4. Build dependency DAG │
└────────┬────────────────┘
         ↓
┌─────────────────────────┐
│  Task Router             │
│  - Match employee skills │
│  - Check availability    │
│  - Assign to queue       │
└────────┬────────────────┘
         ↓
  Multiple Workers execute sub-tasks in parallel
         ↓
┌─────────────────────────┐
│  Result Aggregator       │
│  - Collect all results   │
│  - Merge output          │
│  - Return to user        │
└─────────────────────────┘
```

#### 6.3.3 Workflow Definition (YAML)

```yaml
workflow:
  id: competitor-analysis
  name: Competitor Analysis Report
  description: Analyze competitors and generate comprehensive report

  steps:
    - id: research
      name: Research Competitors
      employee_role: "Researcher"
      required_skills: [web_scraping, data_collection]
      input: "${task.competitor_list}"
      output: raw_data

    - id: analyze
      name: Analyze Data
      employee_role: "Data Analyst"
      required_skills: [data_analysis, visualization]
      input: "${steps.research.output}"
      output: analysis_results
      depends_on: [research]

    - id: write
      name: Write Report
      employee_role: "Technical Writer"
      required_skills: [report_writing, markdown]
      input: "${steps.analyze.output}"
      output: final_report
      depends_on: [analyze]
```

#### 6.3.4 Data Model

```
Workflow:
  id, name, description, definition (YAML),
  version, status, created_by, created_at

WorkflowExecution:
  id, workflow_id, input_data, status,
  started_at, completed_at, output_data

WorkflowStep:
  id, execution_id, step_id, employee_id,
  status, input_data, output_data,
  started_at, completed_at, error_message
```

#### 6.3.5 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/workflows` | List workflows |
| POST | `/api/workflows` | Create workflow |
| GET | `/api/workflows/{id}` | Get workflow detail |
| PUT | `/api/workflows/{id}` | Update workflow |
| DELETE | `/api/workflows/{id}` | Delete workflow |
| POST | `/api/workflows/{id}/execute` | Execute workflow |
| GET | `/api/workflows/{id}/executions` | List executions |
| GET | `/api/workflows/executions/{id}` | Get execution status |
| GET | `/api/workflows/executions/{id}/steps` | Get step details |
| POST | `/api/workflows/executions/{id}/cancel` | Cancel execution |

#### 6.3.6 Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | Workflow YAML parsed and validated |
| AC-2 | Sub-tasks routed to correct employees |
| AC-3 | Dependencies respected (no out-of-order execution) |
| AC-4 | Parallel steps execute concurrently |
| AC-5 | Failed step halts dependent steps |
| AC-6 | Full execution history traceable |
| AC-7 | Frontend shows real-time workflow progress |

#### 6.3.7 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Circular dependencies | High | Low | DAG validation before execution |
| Employee unavailable | High | Medium | Fallback routing, queue wait |
| Complex workflows timeout | Medium | Medium | Step-level timeouts, auto-retry |

---

### Phase 4: Anti-Rot Governance

**Status**: Not Started

#### 6.4.1 Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| P4-R1 | Configuration drift detector | P0 |
| P4-R2 | Document staleness checker | P0 |
| P4-R3 | Test regression analyzer | P1 |
| P4-R4 | Auto-fix pipeline | P1 |
| P4-R5 | Governance dashboard | P1 |
| P4-R6 | Scheduled governance scans | P2 |

#### 6.4.2 Architecture

```
Scheduled Scan (cron)
         ↓
┌─────────────────────────┐
│  Governance Scanner      │
│                          │
│  1. Config Drift:        │
│     Git ↔ DB comparison  │
│                          │
│  2. Doc Staleness:       │
│     Last update vs age   │
│     threshold            │
│                          │
│  3. Test Rot:            │
│     Skipped/failed tests │
│     without fixes        │
└────────┬────────────────┘
         ↓
┌─────────────────────────┐
│  Report Generator        │
│  - Drift items           │
│  - Stale docs            │
│  - Rot tests             │
│  - Fix suggestions       │
└────────┬────────────────┘
         ↓
    Admin Review → Auto-Fix → Verify
```

#### 6.4.3 Governance Rules

| Rule | Check | Threshold | Action |
|------|-------|-----------|--------|
| Config Drift | Git content ≠ DB content | Any diff | Auto-sync + alert |
| Doc Staleness | Last update > 30 days | 30 days | Mark stale + alert |
| Unused Skills | Skill not used in 14 days | 14 days | Suggest deprecation |
| Orphaned Profiles | Profile without active agent | 7 days | Suggest cleanup |
| Test Regression | Test failed > 3 runs | 3 runs | Block deployment |

#### 6.4.4 Data Model

```
GovernanceScan:
  id, scan_type, status, started_at, completed_at,
  findings_count, critical_count

GovernanceFinding:
  id, scan_id, type (drift/stale/rot/orphan),
  severity, entity_type, entity_id,
  description, suggested_fix, status

GovernanceAction:
  id, finding_id, action_type, executed_by,
  status, executed_at, result
```

#### 6.4.5 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/governance/scan` | Trigger scan |
| GET | `/api/governance/scans` | List scans |
| GET | `/api/governance/scans/{id}` | Get scan result |
| GET | `/api/governance/findings` | List findings |
| POST | `/api/governance/findings/{id}/fix` | Apply auto-fix |
| GET | `/api/governance/dashboard` | Governance summary |

#### 6.4.6 Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | Config drift detected within 1 hour of occurrence |
| AC-2 | Stale docs flagged in dashboard |
| AC-3 | Auto-fix resolves 80% of drift issues |
| AC-4 | Governance scan completes within 5 minutes |
| AC-5 | Dashboard shows real-time governance health |

---

### Phase 5: Session Checkpointing + Crash Recovery

**Status**: Not Started

#### 6.5.1 Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| P5-R1 | Checkpoint manager (periodic state save) | P0 |
| P5-R2 | State serialization (conversation + context) | P0 |
| P5-R3 | Resume from latest checkpoint | P0 |
| P5-R4 | Checkpoint cleanup (retention policy) | P1 |
| P5-R5 | Frontend: Progress indicator with checkpoint markers | P1 |

#### 6.5.2 Architecture

```
Task Execution
     ↓
  Every N steps or T seconds
     ↓
┌─────────────────────────┐
│  Checkpoint Manager      │
│  1. Serialize state:     │
│     - Conversation history│
│     - Tool outputs        │
│     - Context variables   │
│  2. Save to SQLite       │
│  3. Update checkpoint ref│
└─────────────────────────┘

Worker Crash → New Worker Starts
     ↓
  Load latest checkpoint
     ↓
  Resume execution from checkpoint
```

#### 6.5.3 Data Model

```
Checkpoint:
  id, task_id, employee_id, execution_id,
  state (JSON), created_at, size_bytes,
  is_latest: boolean

CheckpointMetadata:
  id, checkpoint_id, step_number,
  tool_calls_count, tokens_used,
  estimated_recovery_time_ms
```

#### 6.5.4 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tasks/{id}/checkpoints` | List checkpoints |
| GET | `/api/tasks/{id}/checkpoints/latest` | Get latest checkpoint |
| POST | `/api/tasks/{id}/resume` | Resume from checkpoint |
| DELETE | `/api/tasks/{id}/checkpoints` | Cleanup old checkpoints |

#### 6.5.5 Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | Checkpoint created every 5 minutes or 50 steps |
| AC-2 | Resume from checkpoint restores full context |
| AC-3 | Recovery time < 30 seconds |
| AC-4 | Old checkpoints cleaned per retention policy |
| AC-5 | Frontend shows checkpoint markers on progress bar |

---

### Phase 6: Multi-Tenant Organization Support

**Status**: Not Started

#### 6.6.1 Requirements

| ID | Requirement | Priority |
|----|------------|----------|
| P6-R1 | Organization CRUD | P0 |
| P6-R2 | Tenant isolation (data, employees, tasks) | P0 |
| P6-R3 | Organization-level skill pool | P1 |
| P6-R4 | Cross-organization analytics | P1 |
| P6-R5 | Organization admin console | P1 |

#### 6.6.2 Architecture

```
Platform Admin
     ↓
┌─────────────────────────┐
│  Organization A          │
│  ├── Employees (A1..An)  │
│  ├── Tasks               │
│  ├── Memory (isolated)   │
│  ├── Skills (shared pool)│
│  └── Workflows           │
└─────────────────────────┘

┌─────────────────────────┐
│  Organization B          │
│  ├── Employees (B1..Bn)  │
│  ├── Tasks               │
│  ├── Memory (isolated)   │
│  ├── Skills (shared pool)│
│  └── Workflows           │
└─────────────────────────┘
```

#### 6.6.3 Data Model (Tenant Isolation)

```
Organization:
  id, name, slug, status, created_by, created_at
  billing_plan, member_limit, employee_limit

OrganizationMember:
  id, org_id, user_id, role (admin/member),
  joined_at, status

All existing tables add:
  organization_id: UUID (foreign key)
  → All queries filtered by org_id
```

#### 6.6.4 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/organizations` | List organizations (admin) |
| POST | `/api/organizations` | Create organization |
| GET | `/api/organizations/{id}` | Get org detail |
| PUT | `/api/organizations/{id}` | Update org |
| GET | `/api/organizations/{id}/members` | List members |
| POST | `/api/organizations/{id}/members` | Add member |
| DELETE | `/api/organizations/{id}/members/{user_id}` | Remove member |
| GET | `/api/organizations/{id}/analytics` | Org analytics |
| GET | `/api/organizations/{id}/skills` | Org skill pool |

#### 6.6.5 Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | Org A cannot see Org B's employees/tasks/memory |
| AC-2 | Platform admin can view all organizations |
| AC-3 | Org admin can manage org members |
| AC-4 | Skill pool shared within org |
| AC-5 | Analytics aggregated per org |

---

## 7. Overall Data Model

### 7.1 Core Entities (Across All Phases)

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  User       │───<│ Organization │───<│ Employee    │
│  (existing) │    │  (Phase 6)   │    │ Profile     │
└─────────────┘    └──────────────┘    │  (Phase 1)  │
                                       └──────┬──────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
              ┌─────┴─────┐            ┌──────┴──────┐           ┌─────┴──────┐
              │  Agent    │            │  Task       │           │ Permission │
              │(existing) │            │  (Phase 1)  │           │ (Phase 2)  │
              └───────────┘            └─────────────┘           └────────────┘
                                               │
                                    ┌──────────┴──────────┐
                                    │                     │
                              ┌─────┴─────┐        ┌──────┴──────┐
                              │ Workflow  │        │ Checkpoint  │
                              │ (Phase 3) │        │ (Phase 5)   │
                              └───────────┘        └─────────────┘
```

### 7.2 Cross-Cutting Tables

| Table | Phase | Purpose |
|-------|-------|---------|
| `employee_profiles` | Phase 1 | Git-managed identity |
| `permission_rules` | Phase 2 | Permission evaluation |
| `permission_audit_logs` | Phase 2 | Decision audit trail |
| `workflows` | Phase 3 | Workflow definitions |
| `workflow_executions` | Phase 3 | Execution tracking |
| `governance_scans` | Phase 4 | Scan results |
| `governance_findings` | Phase 4 | Drift/stale/rot findings |
| `checkpoints` | Phase 5 | State serialization |
| `organizations` | Phase 6 | Tenant isolation |

---

## 8. Rollout Plan

### 8.1 Timeline

| Phase | Duration | Owner | Start | End | Dependencies |
|-------|----------|-------|-------|-----|-------------|
| Phase 1 | 2 weeks | Wilde (BE) + Flora (FE) | Week 1 | Week 2 | None |
| Phase 2 | 2 weeks | Wilde | Week 3 | Week 4 | Phase 1 |
| Phase 3 | 3 weeks | Wilde | Week 5 | Week 7 | Phase 1, 2 |
| Phase 4 | 2 weeks | Wilde | Week 8 | Week 9 | Phase 1, 2, 3 |
| Phase 5 | 2 weeks | Wilde | Week 10 | Week 11 | Phase 1 |
| Phase 6 | 3 weeks | Wilde | Week 12 | Week 14 | Phase 1-5 |

**Total Estimated Duration**: 14 weeks (~3.5 months)

### 8.2 Milestones

| Milestone | Target Date | Deliverable |
|-----------|-------------|-------------|
| M1: Phase 1 Complete | Week 2 | Employee profiles + Worker daemon + Frontend |
| M2: Phase 2 Complete | Week 4 | Dual-layer permission verification |
| M3: Phase 3 Complete | Week 7 | Workflow engine + Multi-employee collaboration |
| M4: Phase 4 Complete | Week 9 | Anti-rot governance dashboard |
| M5: Phase 5 Complete | Week 11 | Checkpointing + Crash recovery |
| M6: Phase 6 Complete | Week 14 | Multi-tenant organization support |
| M7: Platform Launch | Week 14 | Full QoderWake-like platform |

### 8.3 Risk Buffer

| Risk | Buffer |
|------|--------|
| Technical complexity (LangGraph integration) | +1 week (Phase 3) |
| Permission engine tuning | +1 week (Phase 2) |
| Frontend delays (Flora availability) | +1 week (Phase 1, 3) |
| **Total Buffer** | **+3 weeks** |

**Realistic Timeline**: 17 weeks (~4 months)

---

## 9. Risks and Mitigation

### 9.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| DeepAgents/LangGraph incompatibility | High | Medium | Early prototype, fallback to custom orchestrator |
| Redis single point of failure | High | Low | Redis Sentinel or cluster |
| Git performance with many profiles | Medium | Medium | Sharding by org, pagination |
| LLM judgment cost (Phase 2) | Medium | High | RuleMatcher cache, rate limiting |
| Checkpoint storage growth | Medium | Medium | Retention policy, compression |

### 9.2 Product Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Scope creep during development | High | High | Strict non-goals, change request process |
| Flora frontend delays | Medium | Medium | Backend-first API testing, mock UI |
| User adoption resistance | Medium | Medium | Early demo, feedback loop |
| Missing market differentiation | Medium | Low | Focus on Git-managed + 24/7 unique value |

### 9.3 Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Developer bandwidth (Wilde solo BE) | High | High | Prioritize P0, defer P1/P2 |
| No dedicated QA | Medium | High | Automated tests, API contract testing |
| Documentation maintenance | Medium | Medium | Auto-generate from code, API-first docs |

---

## 10. Open Questions

| # | Question | Owner | Decision Needed By |
|---|----------|-------|-------------------|
| Q1 | Should we support multiple workers per node in Phase 1? | Wilde | Phase 1 start |
| Q2 | What LLM model to use for ReasoningJudge (Phase 2)? | Wilde | Phase 2 design |
| Q3 | Should workflows be user-editable or system-managed? | Product | Phase 3 design |
| Q4 | What is the retention policy for checkpoints? | Product | Phase 5 design |
| Q5 | Should org skill pools be shared or isolated? | Product | Phase 6 design |

---

## 11. Related Documents

| Document | Path | Phase |
|----------|------|-------|
| Phase 1 PRD | `docs/phase1-product-design.md` | 1 |
| Phase 1 Frontend Design | `docs/phase1-frontend-design.md` | 1 |
| Phase 1 API Reference | `docs/phase1-api.md` | 1 |
| Phase 1 Employee List Prototype | `docs/prototype-employee-profiles.html` | 1 |
| Phase 1 Employee Detail Prototype | `docs/prototype-employee-detail.html` | 1 |
| Phase 1 Operations Dashboard Prototype | `docs/prototype-worker-dashboard.html` | 1 |

---

## 12. Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-24 | Lisa | Initial comprehensive 6-phase PRD |
