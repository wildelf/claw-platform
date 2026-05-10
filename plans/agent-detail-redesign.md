# Agent Detail 页面优化计划

## 目标
优化 Agent Detail 页面的可用性，使执行流程更清晰、状态感知更强、视觉层级更合理。

## 设计决策

### 1. Language — 全部中文
页面标题、按钮、标签全部统一为中文：
- "Agent Details" → "Agent 信息"
- "Run Agent" → "执行 Agent"
- "Edit" → "编辑"
- "执行中..." / "已完成" / "新对话" / "对话历史"

### 2. Layout — 2-column，stacked on mobile
```
+------------------+------------------------+
|   Agent 信息      |    执行面板             |
|   (compact)      |    Task input          |
|                  |    Model selector       |
|                  |    Execute button      |
|                  +------------------------+
|                  |    Output              |
|                  |    Thinking (展开)     |
+------------------+------------------------+
```
- 移动端 (< 768px): 上下堆叠，Agent 信息收起为可展开 header

### 3. Thinking — 默认展开
- 思考过程区域默认展开，实时更新
- 不再依赖 collapsible 交互

### 4. Visual Style — Utilitarian workspace
- 删除 emoji 状态图标，替换为文字+颜色
- 状态颜色: 执行中=蓝色, 完成=绿色, 错误=红色
- 背景中性灰色，字体清晰，无装饰元素

### 5. Status Display — 简化
- 当前事件直接显示在执行面板内，不在独立区域
- Event log 作为可折叠小组件，不主导 UI
- 执行状态: 顶部条显示 "执行中..." + 当前步骤

### 6. Task Input — 3行高度
保持 rows=3，超出滚动，不撑开页面高度

## 状态覆盖规格

| 状态 | 显示方式 |
|------|----------|
| Idle | Output 区显示 "等待输入..."，非执行状态不显示 event log |
| 执行中 | 顶部蓝色进度条 + 当前步骤文字 |
| 思考中 | Thinking 区实时展开，不折叠 |
| 完成 | 绿色文字 "执行完成"，Output 正常展示 |
| 错误 | 红色文字 + 错误信息突出显示 |

## 移动端行为
- < 768px: 单列布局，Agent 信息默认收起，显示为 "Agent 信息 ▼" 可展开 header
- 执行面板全宽

## NOT in scope
- Agent 信息卡片的编辑功能（已有 Edit 按钮，跳转 AgentEditView）
- 多 agent 并行执行
- 执行历史持久化（当前 session 内存级别）

## What already exists
- UI 组件: Card, Button, Badge, Select — 复用现有
- API: `/api/agents/{id}/run` SSE 流已就绪
- 状态管理: agentsStore, modelsStore

## Implementation
1. 修改 AgentDetailView.vue:
   - 重构为 2-column grid 布局
   - 替换 emoji 为文字+颜色状态
   - Thinking 区默认展开 (regression test 见下文)
   - 执行状态条简化
   - 统一中文文案
2. 响应式: md:grid-cols-2 + stacked on mobile

## Regression Tests (CRITICAL)
Existing test `src/views/AgentDetailView.test.ts:163-166` — "should start with thinking collapsed"
必须更新为 "should start with thinking expanded" — 这是 plan 改变的行为

## What already exists
- UI 组件: Card, Button, Badge, Select — 复用现有
- API: `/api/agents/{id}/run` SSE 流已就绪 (无需修改)
- 状态管理: agentsStore, modelsStore
- 已有测试: `src/views/AgentDetailView.test.ts` — SSE parse、Thinking、Session Memory
- handleEvent (~112 行 switch) — 存在但 plan 不修改，保持原样

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | issues_open | 0 issues, 1 CRITICAL regression test |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | issues_open | score: 4/10 → 8/10, 6 decisions |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**CODEX:** skipped (small frontend refactor, outside voice not useful)
**UNRESOLVED:** 0
**VERDICT:** Design Review CLEARED — Eng Review CLEARED — ready to implement