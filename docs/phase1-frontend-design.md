# Phase 1 前端设计规范

## 1. 概述

本文档定义 Phase 1（Git 管理员工身份 + 常驻 Worker）的前端设计规范，包括页面结构、组件设计、交互流程和样式规范。

**目标**：为前端工程师 Flora 提供完整的设计指引，确保前端实现与产品需求一致。

## 2. 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.x | UI 框架（Composition API） |
| TypeScript | 5.x | 类型安全 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由管理 |
| Tailwind CSS | 3.x | 样式框架 |
| Axios | 1.x | HTTP 客户端 |
| Monaco Editor | 0.45+ | Markdown 代码编辑器 |

## 3. 页面结构

### 3.1 路由设计

```
/employees                    → EmployeeList（员工列表页）
/employees/new                → EmployeeForm（新建员工）
/employees/:id                → EmployeeDetail（员工详情）
/employees/:id/edit           → EmployeeForm（编辑员工）
/operations                   → OperationsDashboard（运维面板）
```

### 3.2 导航结构

```
Sidebar
├── 数字员工
│   ├── 员工列表
│   └── 新建员工
├── 运维面板
│   ├── Worker 状态
│   ├── 任务队列
│   └── 任务管理
└── 设置
```

## 4. 页面设计

### 4.1 员工列表页（/employees）

**布局**：
- 顶部：页面标题 "数字员工" + "新建员工" 按钮
- 主体：卡片网格（响应式，3 列 → 2 列 → 1 列）
- 每张卡片：员工名称、角色、状态标签、操作按钮（查看/编辑/删除）
- 空状态：无员工时显示引导文案和创建按钮

**卡片设计**：
```
┌─────────────────────────────────┐
│  [头像]  张三                    │
│          AI 客服专员             │
│                                  │
│  目标: 处理客户咨询和投诉...      │
│                                  │
│  [● Active]    [查看] [编辑]     │
└─────────────────────────────────┘
```

**状态标签**：
- Active: 绿色圆点 + "活跃"
- Paused: 黄色圆点 + "暂停"
- Retired: 灰色圆点 + "已退休"

**交互**：
- 点击卡片或"查看"→ 跳转到员工详情页
- 点击"编辑"→ 跳转到编辑表单
- 点击"删除"→ 弹出确认对话框，确认后调用 DELETE API

### 4.2 员工新建/编辑页（/employees/new, /employees/:id/edit）

**布局**：
- 顶部：页面标题 + "保存"按钮 + "取消"按钮
- 主体：分栏布局（左侧基本信息表单，右侧文件编辑器）

**左侧表单**：
| 字段 | 类型 | 验证 |
|------|------|------|
| 名称 | TextInput | 必填，max 100 |
| 角色 | TextInput | 必填，max 500 |
| 目标 | Textarea | 必填，max 1000 |
| 背景故事 | Textarea | 可选，max 2000 |
| 性格特征 | Textarea | 可选，max 1000 |
| 状态 | Select | Active/Paused/Retired |

**右侧文件编辑器**（Monaco Editor）：
- Tab 1: `profile.md`（自动生成，只读）
- Tab 2: `constraints.md`（可编辑）
- Tab 3: `working_rules.md`（可编辑）

**交互**：
- 保存：先校验表单，然后调用 POST/PUT API
- 保存成功后跳转到列表页
- 取消：弹出确认对话框（如有未保存更改）
- 文件编辑器实时预览（可选）

### 4.3 员工详情页（/employees/:id）

**布局**：
- 顶部：返回按钮 + 员工名称 + "编辑"按钮 + "删除"按钮
- 基本信息区：名称、角色、目标、背景故事、性格、状态
- 文件区：3 个 Markdown 文件的只读预览

**文件预览**：
- 使用 Markdown 渲染（marked.js 或 similar）
- 支持代码块高亮
- 显示文件名和最后修改时间

### 4.4 运维面板（/operations）

**布局**：三栏 Dashboard

#### Tab 1: Worker 状态
```
┌─────────────────────────────────────┐
│  Worker 状态                         │
├─────────────────────────────────────┤
│  Worker ID:  worker:host:12345       │
│  状态:        [● Online]             │
│  最后心跳:     2026-05-24 10:30:15   │
│  心跳间隔:     3s 前                 │
│  启动时间:     2026-05-24 08:00:00   │
│  运行时长:     2h 30m 15s            │
│  Redis 连接:   localhost:6379        │
│                                     │
│  [重启 Worker]  [停止 Worker]         │
└─────────────────────────────────────┘
```

**交互**：
- 每 30s 自动刷新
- 点击重启/停止 → 弹出确认对话框
- 离线状态用红色警示

#### Tab 2: 任务队列
```
┌─────────────────────────────────────┐
│  队列统计                             │
├──────────┬──────────┬───────────────┤
│ 排队中    │ 执行中    │ 已完成(今日)   │
│   12     │    3     │     156       │
├──────────┴──────────┴───────────────┤
│  失败: 2    已取消: 5                 │
│                                     │
│  [清空队列]                          │
└─────────────────────────────────────┘
```

**交互**：
- 每 30s 自动刷新
- 点击清空队列 → 弹出确认对话框（显示将清空的任务数）

#### Tab 3: 任务管理
```
┌─────────────────────────────────────────────────────────┐
│  任务列表                    [刷新] [过滤: 全部 ▼]       │
├──────┬──────────┬────────┬──────────┬────────┬─────────┤
│ 任务ID│ 员工名称  │ 状态    │ 创建时间  │ 耗时    │ 操作     │
├──────┼──────────┼────────┼──────────┼────────┼─────────┤
│ t-001│ 张三      │ 执行中  │ 10:25:00 │ 5m 15s │ [取消]  │
│ t-002│ 李四      │ 排队中  │ 10:26:00 │ -      │ [取消]  │
│ t-003│ 张三      │ 已完成  │ 10:20:00 │ 3m 42s │ -       │
│ t-004│ 王五      │ 失败    │ 10:15:00 │ 1m 05s │ -       │
└──────┴──────────┴────────┴──────────┴────────┴─────────┘
```

**交互**：
- 支持按状态过滤（全部/排队中/执行中/已完成/失败）
- 每 30s 自动刷新
- 点击取消 → 弹出确认对话框
- 分页加载（默认 50 条）

## 5. 组件设计

### 5.1 可复用组件

| 组件 | 用途 | Props |
|------|------|-------|
| EmployeeCard | 员工卡片 | employee, actions |
| StatusBadge | 状态标签 | status, size |
| MarkdownPreview | Markdown 渲染 | content, readonly |
| MarkdownEditor | Monaco 编辑器 | value, onChange, language |
| ConfirmDialog | 确认对话框 | title, message, onConfirm |
| AutoRefresh | 自动刷新容器 | interval, enabled |
| EmptyState | 空状态引导 | title, description, action |

### 5.2 组件层级

```
App
├── Sidebar
├── AppHeader
└── MainContent
    ├── EmployeeListView
    │   ├── EmployeeCard × N
    │   └── EmptyState
    ├── EmployeeFormView
    │   ├── BasicInfoForm
    │   └── FileEditorTabs
    │       └── MarkdownEditor × 3
    ├── EmployeeDetailView
    │   ├── BasicInfoSection
    │   └── MarkdownPreview × 3
    └── OperationsDashboardView
        ├── WorkerStatusPanel
        ├── QueueStatsPanel
        └── TaskListPanel
```

## 6. API 集成

### 6.1 API 模块结构

```
src/api/
├── employeeProfiles.ts  — 员工 CRUD + 文件操作
├── operations.ts        — Worker/队列/任务 API
└── types.ts             — TypeScript 类型定义
```

### 6.2 类型定义

```typescript
interface EmployeeProfile {
  id: string;
  name: string;
  role: string;
  goal: string;
  backstory: string;
  personality: string;
  status: 'active' | 'paused' | 'retired';
  userId: string;
  organizationId: string | null;
  gitPath: string;
  createdAt: string;
  updatedAt: string;
}

interface WorkerStatus {
  workerId: string | null;
  status: 'online' | 'offline';
  lastHeartbeat: string | null;
  lastHeartbeatSecondsAgo: number | null;
  startedAt: string | null;
  uptimeSeconds: number | null;
  redisConnection: string;
}

interface TaskItem {
  taskId: string;
  agentId: string;
  agentName?: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  createdAt: string;
  completedAt?: string;
  error?: string;
}

interface QueueStats {
  queued: number;
  processing: number;
  completed: number;
  failed: number;
}
```

### 6.3 错误处理

```typescript
// 统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      router.push('/login');
    } else if (error.response?.status === 403) {
      showNotification('无权限操作', 'error');
    } else if (error.response?.status === 404) {
      showNotification('资源不存在', 'error');
    } else {
      showNotification(error.response?.data?.detail || '操作失败', 'error');
    }
    return Promise.reject(error);
  }
);
```

## 7. 样式规范

### 7.1 设计主题

参考 QoderWake 的深色主题风格：

| 元素 | 色值 |
|------|------|
| 背景色 | `#0d1117` |
| 卡片背景 | `#161b22` |
| 边框色 | `#30363d` |
| 主文字 | `#e6edf3` |
| 次要文字 | `#8b949e` |
| 主题色 | `#58a6ff`（蓝） |
| 成功色 | `#3fb950`（绿） |
| 警告色 | `#d29922`（黄） |
| 错误色 | `#f85149`（红） |

### 7.2 间距系统

| 级别 | 值 | 用途 |
|------|-----|------|
| xs | 4px | 图标间距 |
| sm | 8px | 内联元素间距 |
| md | 16px | 组件内边距 |
| lg | 24px | 区块间距 |
| xl | 32px | 页面级间距 |

### 7.3 字体

| 用途 | 字体 | 大小 |
|------|------|------|
| 页面标题 | System | 24px / 30px |
| 卡片标题 | System | 16px / 20px |
| 正文 | System | 14px / 20px |
| 辅助文字 | System | 12px / 16px |
| 代码 | JetBrains Mono | 13px |

## 8. 交互规范

### 8.1 加载状态
- 列表加载：Skeleton 骨架屏
- 按钮操作：Loading spinner + disabled
- 文件加载：编辑器 loading overlay

### 8.2 反馈机制
- 成功：顶部绿色 Toast，3s 自动消失
- 错误：顶部红色 Toast，手动关闭
- 确认：居中 Modal 对话框

### 8.3 自动刷新
- Operations 面板默认 30s 刷新
- 用户可手动点击刷新按钮
- 页面不可见时（visibilitychange）暂停刷新

## 9. 验收标准

| 编号 | 标准 | 验证方式 |
|------|------|---------|
| AC-F1 | 列表页正确显示所有员工 | 对比 API 返回 |
| AC-F2 | 新建员工后列表自动刷新 | 操作后验证 |
| AC-F3 | 编辑保存后详情更新 | 操作后验证 |
| AC-F4 | 删除有确认对话框 | 手动测试 |
| AC-F5 | Markdown 编辑器正常加载 | 手动测试 |
| AC-F6 | 运维面板数据实时刷新 | 计时验证 |
| AC-F7 | 深色主题样式一致 | 视觉检查 |
| AC-F8 | 响应式布局正常 | 多尺寸测试 |
| AC-F9 | 错误提示清晰友好 | 手动触发错误 |
| AC-F10 | 路由守卫正确（未登录跳转） | 手动测试 |

## 10. 开发排期

| 任务 | 负责人 | 工时 | 依赖 |
|------|--------|------|------|
| 路由 + 状态管理框架 | Flora | 0.5d | 后端 API 可用 |
| 员工列表页 | Flora | 1d | API 可用 |
| 员工新建/编辑页 | Flora | 1.5d | API 可用 + Monaco Editor |
| 员工详情页 | Flora | 1d | API 可用 |
| 运维面板 | Flora | 1.5d | Operations API 可用 |
| 联调 + 修复 | Flora + Wilde | 1d | 全部 API 可用 |
| UI 优化 | Flora | 0.5d | 联调完成 |
