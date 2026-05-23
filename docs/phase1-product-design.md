# Phase 1: Git-Managed Employee Identity + Always-On Worker Daemon

## 1. Background

Claw Platform 当前是一个 AI Agent 管理平台，目标是转型为 **24/7 AI 数字员工平台**（类似 QoderWake 模式）。Phase 1 聚焦两个核心能力：

1. **Git 管理的员工身份**：数字员工的身份以 Markdown 文件形式存储在 `~/.qoder/employees/{id}/` 目录下，通过 Git 版本控制
2. **常驻 Worker 守护进程**：后台进程持续监听任务队列，自动执行数字员工任务

## 2. Goals

| Goal | Metric | Target |
|------|--------|--------|
| 员工身份可版本控制 | Git commit 历史 | 每次修改可追溯 |
| Worker 24/7 运行 | 心跳检测间隔 | 30s |
| 任务自动执行 | 任务响应延迟 | < 5s |
| 崩溃自动恢复 | 恢复成功率 | > 95% |

## 3. Target Users

- **平台管理员**：管理数字员工配置、监控运行状态
- **业务负责人**：创建和管理自己团队的数字员工
- **开发者**：通过 API 集成数字员工能力

## 4. Scenarios

### Scenario 1: 创建数字员工
1. 管理员在 Web 界面填写员工基本信息（名称、角色、目标、背景故事）
2. 编辑 constraints.md 和 working_rules.md 约束文件
3. 保存后自动生成 Git commit，同步到 SQLite 数据库

### Scenario 2: Worker 自动执行任务
1. 用户提交任务到队列（通过 API 或 Web）
2. Worker 守护进程轮询队列，认领任务
3. 加载对应数字员工的身份配置
4. 调用 DeepAgents 引擎执行任务
5. 完成后更新任务状态

### Scenario 3: 监控和运维
1. 管理员查看 Operations Dashboard
2. 查看 Worker 状态、心跳、队列统计
3. 查看任务列表，可取消任务
4. 可发送重启/停止信号给 Worker

## 5. Scope

### In Scope
- 数字员工 CRUD API（8 个端点）
- 员工身份文件管理（profile.md, constraints.md, working_rules.md）
- Git 版本控制集成
- SQLite 双持久化
- Worker 守护进程（心跳、任务轮询、崩溃恢复）
- Operations API（7 个端点）
- Redis 任务队列和心跳管理

### Non-Goals
- 前端界面开发（Phase 1 仅提供 API，前端由 Flora 独立开发）
- 权限控制（RBAC）
- 多租户隔离
- 任务调度策略（优先级、定时）
- Worker 水平扩展（多节点）

## 6. User Stories

| ID | As a... | I want to... | So that... |
|----|---------|-------------|-----------|
| US-1 | 管理员 | 创建数字员工档案 | 系统有可用的 AI 员工 |
| US-2 | 管理员 | 编辑员工的约束和工作规则 | 员工行为符合预期 |
| US-3 | 管理员 | 查看员工列表和详情 | 了解所有员工配置 |
| US-4 | 管理员 | 删除不再使用的员工 | 保持系统整洁 |
| US-5 | 运维人员 | 查看 Worker 实时状态 | 确认系统正常运行 |
| US-6 | 运维人员 | 查看任务队列统计 | 了解系统负载 |
| US-7 | 运维人员 | 取消卡住的任务 | 释放系统资源 |
| US-8 | 运维人员 | 重启 Worker | 处理异常情况 |

## 7. Data Model

### EmployeeProfile
```
id: UUID
name: str (max 100)
role: str (max 500)
goal: str (max 1000)
backstory: str (max 2000)
personality: str (max 1000)
constraints: str (markdown text)
working_rules: str (markdown text)
status: Enum(ACTIVE, PAUSED, RETIRED)
user_id: UUID
organization_id: UUID | None
git_path: str
created_at: datetime
updated_at: datetime
```

### Agent (extended)
```
... existing fields ...
employee_profile_id: UUID | None  # 关联数字员工身份
```

## 8. Architecture

### 5-Layer Model
```
Layer 1: Identity     — Git-managed employee profiles (markdown + YAML frontmatter)
Layer 2: Memory       — FTS5 SQLite cross-session memory (already implemented)
Layer 3: Skills       — Tool/skill registry (existing)
Layer 4: Division     — Task routing and assignment (future)
Layer 5: Red Lines    — Permission boundaries (Phase 2)
```

### Dual Persistence
```
Write path: API -> Service -> Git store (primary) -> SQLite (sync)
Read path:  API -> Service -> SQLite (primary) -> Git (fallback)
```

### Worker Architecture
```
Worker Daemon (app.worker)
  ├── Heartbeat Manager (Redis)
  │     ├── Register worker
  │     ├── Periodic heartbeat (30s)
  │     └── Signal detection (restart/stop)
  ├── Task Polling
  │     ├── BRPOPLPUSH from task:queue
  │     ├── Check cancel flag
  │     └── Execute via DeepAgents
  └── Crash Recovery
        ├── Detect stale workers
        └── Reclaim uncompleted tasks
```

## 9. Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|-------------|
| AC-1 | 创建员工后 Git 目录存在对应文件 | `ls ~/.qoder/employees/{id}/` |
| AC-2 | 创建员工后 DB 中有对应记录 | `SELECT * FROM employee_profiles` |
| AC-3 | 更新员工后 Git commit 历史有新记录 | `git log --oneline` |
| AC-4 | 删除员工后 Git 和 DB 都清理 | 文件不存在 + DB 无记录 |
| AC-5 | Worker 启动后 Redis 中有心跳记录 | `redis-cli GET worker:heartbeat:{id}` |
| AC-6 | 提交任务后 Worker 在 5s 内开始执行 | 时间戳对比 |
| AC-7 | 崩溃后任务可被新 Worker 恢复 | 模拟 kill + 重启 |
| AC-8 | Operations API 返回正确的 Worker 状态 | HTTP 响应验证 |
| AC-9 | 取消队列中的任务立即生效 | 任务状态变为 cancelled |
| AC-10 | 重启/停止信号 1 分钟内生效 | 信号发送 + Worker 退出 |

## 10. Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Git 操作慢影响 API 响应 | Medium | Medium | 异步 Git 操作，超时降级 |
| SQLite 和 Git 数据不一致 | High | Low | 定期校验，冲突时 Git 优先 |
| Worker 单点故障 | High | Medium | 心跳检测 + 任务恢复 |
| Redis 连接断开 | High | Low | 自动重连 + 降级日志 |
| 任务执行超时 | Medium | Medium | 设置超时阈值，标记 failed |

## 11. Rollout Plan

| Phase | Action | Owner | Timeline |
|-------|--------|-------|----------|
| 1 | 后端开发（domain, API, service, worker） | Wilde | Day 1-3 |
| 2 | 前端开发（员工列表、详情、Operations 面板） | Flora | Day 3-7 |
| 3 | 集成测试 + 文档 | Wilde + Flora | Day 7-8 |
| 4 | UAT + 修复 | 全员 | Day 8-10 |
| 5 | 上线部署 | Wilde | Day 10 |

## 12. Related Documents

- [Phase 1 Frontend Design Spec](./phase1-frontend-design.md)
- [Phase 1 API Reference](./phase1-api.md)
- [Employee Profiles Prototype](./prototype-employee-profiles.html)
- [Employee Detail Prototype](./prototype-employee-detail.html)
- [Worker Dashboard Prototype](./prototype-worker-dashboard.html)
