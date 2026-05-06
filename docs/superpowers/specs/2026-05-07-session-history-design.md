# 历史会话功能设计

## 概述

在侧边栏提供可折叠的全局会话列表，支持跨 Agent 统一管理、会话切换、新建、编辑名称、删除。

## 数据模型

### Session 表（新建）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (PK) | session_id，UUID |
| name | TEXT | 会话名称，默认首条消息前50字符，可编辑 |
| agent_id | TEXT | 关联的 Agent ID |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 最后活动时间 |
| message_count | INT | 消息数量（冗余字段，方便列表展示） |

LogModel 表保持不变，继续存储详细日志。

## 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sessions` | 获取所有会话列表，按 updated_at 倒序 |
| GET | `/sessions/{id}` | 获取单个会话详情 |
| POST | `/sessions` | 创建新会话（返回 id） |
| PATCH | `/sessions/{id}` | 更新会话名称 |
| DELETE | `/sessions/{id}` | 删除会话 |

## 前端结构

- **Store**：`/src/stores/sessions.ts` — 管理会话列表状态
- **组件**：`/src/components/SessionsDrawer.vue` — 可折叠侧边抽屉
- **修改**：`AgentDetailView.vue` — 集成抽屉，切换会话时刷新消息

## 交互流程

1. 点击抽屉图标 → 展开会话列表（按更新时间倒序）
2. 点击某会话 → 切换 currentSessionId，加载该会话消息
3. 新建会话 → 生成 UUID，清空消息区，开始新对话
4. Hover 会话项 → 显示编辑/删除图标
5. 编辑名称 → inline 编辑框，失焦保存

## 实现顺序

1. 后端：SessionModel + CRUD API
2. 前端：sessions Store
3. 前端：SessionsDrawer 抽屉组件
4. 集成：AgentDetailView 对接会话切换逻辑
