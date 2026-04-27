# 模型配置管理页面设计

## 1. 概述

为 Agent 平台添加独立的模型配置管理界面，允许用户创建、编辑、删除模型配置，并在 Agent 创建/编辑时选择默认模型。

## 2. 页面结构

### 2.1 独立模型配置页面

**列表页 `/models`**
- 表格展示所有模型配置
- 列：名称、提供商类型、模型名称、Base URL、操作
- 操作：编辑、删除

**创建页 `/models/create`**
- 表单字段：
  - 名称（必填，文本输入）
  - 提供商类型（下拉选择：openai/anthropic/local/deepseek/other）
  - 模型名称（必填，文本输入，如 gpt-4o）
  - API Key（可选，密码输入）
  - Base URL（可选，文本输入，如 https://api.openai.com/v1）

**编辑页 `/models/:id/edit`**
- 同创建表单，预填充现有数据

### 2.2 Agent 编辑页集成

**模型选择**
- 在 Agent 创建/编辑表单中添加模型选择下拉框
- 选项：
  - 系统默认（空选项）
  - 用户创建的所有模型配置（显示名称和模型名）
- 保存时将选中的 model_config_id 存储到 Agent

## 3. 数据模型

ModelConfig 已存在，字段：
- `id`: UUID
- `name`: 配置名称
- `type`: 提供商类型（openai/anthropic/local/deepseek/other）
- `model`: 模型名称
- `api_key`: API密钥（可选）
- `base_url`: API地址（可选）
- `config`: 其他配置
- `user_id`: 所属用户

## 4. API 端点

已存在：
- `GET /api/models` - 列出用户所有模型配置
- `POST /api/models` - 创建模型配置
- `GET /api/models/{id}` - 获取单个配置
- `PUT /api/models/{id}` - 更新配置
- `DELETE /api/models/{id}` - 删除配置

## 5. 前端文件

- `frontend/views/ModelsView.vue` - 列表页
- `frontend/views/ModelCreateView.vue` - 创建页
- `frontend/views/ModelEditView.vue` - 编辑页
- `frontend/api/models.ts` - API客户端（已存在）
- `frontend/stores/models.ts` - Pinia store（已存在）
- `frontend/router/index.ts` - 添加路由

## 6. 实现步骤

1. 添加路由配置
2. 创建 ModelsView 列表页
3. 创建 ModelCreateView 创建页
4. 创建 ModelEditView 编辑页
5. 在 AgentCreateView/AgentEditView 中添加模型选择下拉框

## 7. 界面风格

- 使用现有的 UI 组件（Card, Button, Table, Input）
- 遵循现有页面的布局和样式
- 表单验证：必填字段不能为空