# Claw Platform 前端设计文档

## 项目概述

**项目名称**: Claw Platform Frontend
**项目类型**: Vue 3 单页应用
**核心功能**: 为自主执行型智能体平台提供 Web 管理界面
**技术栈**: Vue 3 + Vite + TailwindCSS + Vue Router + Pinia

---

## 一、UI/UX 设计

### 1.1 布局结构

**混合模式布局**:
- 顶部导航栏：固定高度 56px，包含 Logo、主导航、用户菜单
- 可折叠侧边栏：宽度 240px（展开）/ 64px（折叠），包含快捷导航、最近使用
- 主内容区：自适应宽度，内边距 24px

### 1.2 主题配色

**浅色主题**:
- 背景色：`#FFFFFF`（主区域）、`#F8FAFC`（侧边栏）
- 文字色：`#1E293B`（主文字）、`#64748B`（次要文字）
- 强调色：`#3B82F6`（蓝色）、`#10B981`（成功）、`#EF4444`（错误）
- 边框色：`#E2E8F0`

### 1.3 Dashboard 模块

Dashboard 展示 **Agent 卡片** 和 **Skill 卡片** 混合布局：

**Agent 卡片**:
- 最近使用的 Agents 列表（最多 5 个）
- 每个条目显示：名称、状态、最后运行时间
- 快速创建按钮

**Skill 卡片**:
- Skill 统计：总数、trained、pending、needs_review
- 进化状态进度条
- 反馈计数（正/负）

---

## 二、页面结构

### 2.1 路由设计

```
/                   → Dashboard
/agents             → Agent 列表
/agents/create      → 创建 Agent
/agents/:id          → Agent 详情
/agents/:id/edit     → 编辑 Agent
/skills              → Skill 列表
/skills/:id          → Skill 详情
/skills/:id/edit     → 编辑 Skill 文件
/tools                → Tool 列表
/tools/create        → 创建 Tool
/feedback            → Feedback 历史
/login               → 登录页
/register            → 注册页
```

### 2.2 页面组件

| 页面 | 主要组件 |
|------|---------|
| Dashboard | AgentCard, SkillCard, StatsOverview |
| Agents | AgentList, AgentForm, AgentDetail |
| Skills | SkillList, SkillDetail, SkillFileEditor |
| Tools | ToolList, ToolForm, MCPConnectionStatus |
| Feedback | FeedbackList, FeedbackChart |

---

## 三、技术架构

### 3.1 项目结构

```
frontend/
├── public/
├── src/
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   │   ├── layout/       # 布局组件 (Header, Sidebar)
│   │   ├── ui/           # UI 基础组件 (Button, Input, Card)
│   │   └── agents/        # Agent 相关组件
│   │   ├── skills/        # Skill 相关组件
│   │   └── feedback/      # Feedback 相关组件
│   ├── views/            # 页面视图
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia 状态管理
│   │   ├── auth.ts
│   │   ├── agents.ts
│   │   ├── skills.ts
│   │   └── ...
│   ├── api/              # API 调用封装
│   │   ├── client.ts      # Axios 实例
│   │   ├── agents.ts
│   │   ├── skills.ts
│   │   └── ...
│   ├── types/            # TypeScript 类型定义
│   ├── utils/            # 工具函数
│   ├── App.vue
│   └── main.ts
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

### 3.2 状态管理 (Pinia Stores)

```typescript
// stores/auth.ts
interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
}

// stores/agents.ts
interface AgentsState {
  agents: Agent[]
  currentAgent: Agent | null
  loading: boolean
}

// stores/skills.ts
interface SkillsState {
  skills: Skill[]
  currentSkill: Skill | null
  files: Map<string, string>  // skill_id -> files
}
```

### 3.3 API 调用封装

```typescript
// api/client.ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
})

// 拦截器：自动添加 JWT token
api.interceptors.request.use(config => {
  const token = authStore.token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

---

## 四、组件设计

### 4.1 布局组件

**AppHeader**:
- Logo
- 主导航链接（Dashboard, Agents, Skills, Tools）
- 用户下拉菜单（设置、登出）

**AppSidebar**:
- 可折叠（hover 展开 / 点击切换）
- 快捷导航
- 最近使用的 Agents/Skills

### 4.2 UI 基础组件

| 组件 | 说明 |
|------|------|
| Button | primary, secondary, danger, ghost |
| Input | text, password, search |
| Select | 单选、多选 |
| Card | 卡片容器，带阴影和圆角 |
| Modal | 模态框 |
| Table | 数据表格，支持分页 |
| Badge | 状态标签 |
| Toast | 消息通知 |

### 4.3 业务组件

**AgentCard**:
- 状态指示器（pending/active/paused）
- 名称、描述
- 操作按钮（运行、编辑、删除）

**SkillCard**:
- 状态徽章
- 名称、版本
- 反馈统计
- 进化进度条

**SkillFileEditor**:
- Monaco Editor 集成
- Markdown 预览
- 文件切换标签

---

## 五、API 集成

### 5.1 后端 API 对应

| 前端路由 | 后端 API |
|---------|---------|
| GET /agents | `GET /api/agents` |
| POST /agents | `POST /api/agents` |
| GET /agents/:id | `GET /api/agents/{id}` |
| PUT /agents/:id | `PUT /api/agents/{id}` |
| DELETE /agents/:id | `DELETE /api/agents/{id}` |
| POST /agents/:id/run | `POST /api/agents/{id}/run` |
| GET /skills | `GET /api/skills` |
| GET /skills/:id/files | `GET /api/skills/{id}/files` |
| POST /feedback | `POST /api/feedback` |

### 5.2 认证流程

1. 用户访问 `/login`
2. 提交用户名密码到 `POST /api/auth/login`
3. 后端返回 JWT token
4. 前端存储到 Pinia (localStorage)
5. 后续请求自动带上 `Authorization: Bearer <token>`

---

## 六、配置

### 6.1 环境变量

```env
VITE_API_URL=http://localhost:8000/api
VITE_APP_TITLE=Claw Platform
```

### 6.2 Vite 配置

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## 七、实施计划

### Phase 1: 项目脚手架
1. 创建 Vue 3 + Vite 项目
2. 配置 TailwindCSS
3. 配置 Vue Router
4. 配置 Pinia
5. 创建布局组件

### Phase 2: 认证模块
6. 登录/注册页面
7. JWT 认证流程
8. 路由守卫

### Phase 3: 核心功能
9. Agent 管理（CRUD + 运行）
10. Skill 管理（CRUD + 文件编辑）
11. Tool 管理
12. Feedback 面板

### Phase 4: Dashboard
13. Dashboard 页面
14. Agent/Skill 卡片组件
15. 统计图表

---

**设计完成时间**: 2026-04-23