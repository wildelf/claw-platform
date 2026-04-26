# Agent 模型选择与文生图功能设计

## 1. 概述

为Agent平台添加两个功能：
1. **模型选择**：Agent可配置默认模型，执行时也可临时切换
2. **文生图/图生图**：Agent调用多模态模型返回图片时，前端实时内联展示

## 2. 数据模型

### 2.1 ModelConfig（模型配置）

存储在 `model_configs` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| name | TEXT | 配置名称（如 "OpenAI GPT-4o"） |
| provider | TEXT | 提供商：openai / anthropic / azure / 自定义 |
| model | TEXT | 模型名称（如 "gpt-4o"、"claude-3-sonnet-20240229"） |
| base_url | TEXT (nullable) | API端点（可选，用于自定义base_url） |
| api_key | TEXT (nullable) | API密钥 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 2.2 Agent 模型扩展

Agent 表已有 `model_config_id` 字段（可选），用于指定默认模型。

### 2.3 RunAgentRequest 扩展

```python
class RunAgentRequest(BaseModel):
    task: str
    images: list[str] = Field(default_factory=list, description="Base64 encoded images")
    model_config_id: str | None = Field(default=None, description="临时覆盖默认模型")
```

## 3. 后端实现

### 3.1 模型配置管理API

新增 `backend/app/api/models.py`：

```
GET    /api/models              - 列出用户的模型配置
POST   /api/models              - 创建模型配置
GET    /api/models/{id}         - 获取单个模型配置
PUT    /api/models/{id}         - 更新模型配置
DELETE /api/models/{id}         - 删除模型配置
```

### 3.2 Agent执行API扩展

`POST /api/agents/{id}/run` 支持临时模型覆盖：

- 如果请求中传入 `model_config_id`，则使用该模型而非Agent默认模型
- 如果不传，则使用Agent的 `model_config_id`（如果有的话）
- 如果都没有，使用系统默认模型

### 3.3 SSE事件流扩展

新增事件类型：

```json
// 图片事件 - Agent返回图片时触发
{"type": "image", "url": "https://storage.example.com/image.png", "alt": "生成图片描述"}

{
  "type": "start",
  "task": "画一只可爱的猫",
  "model": "gpt-4o"  // 新增：显示当前使用的模型
}
```

## 4. 前端实现

### 4.1 Agent执行页面 (AgentDetailView)

**模型选择器**：
- 位置：任务输入框上方
- 样式：下拉选择框
- 选项：
  - Agent默认模型（如果已配置）
  - 系统默认模型
  - 用户配置的其他模型（从 `/api/models` 获取）
- 临时切换不影响Agent的默认配置

**任务输入区域**：
- 输入框：多行文本
- 图片上传按钮（支持同时上传多张图片作为参考）
- 执行按钮

### 4.2 对话展示区域

**消息气泡**：
- AI回复以气泡形式展示
- 支持Markdown渲染
- 图片内联显示在文字中

**图片渲染**：
- 监听SSE的 `image` 事件
- 收到后立即在当前AI回复位置插入图片
- 图片样式：圆角，最大宽度100%，点击可放大

**图片放大预览**：
- 点击图片弹出Modal
- 支持ESC关闭
- 背景半透明遮罩

### 4.3 模型配置管理页面（可选）

路径：`/models`

- 列表展示用户的所有模型配置
- 可创建、编辑、删除模型配置
- 每个配置显示：名称、提供商、模型名称、base_url

## 5. 事件格式详解

### 5.1 Agent执行事件流

```
连接建立
  ↓
start 事件（包含task和model信息）
  ↓
preparing 事件（准备执行环境）
  ↓
skill_loading / skill_loaded 事件（加载技能）
  ↓
thinking 事件（AI思考中）
  ↓
content 事件（AI回复内容，token-by-token）
  ↓
image 事件（图片生成，可多次触发）
  ↓
tool_call 事件（如有工具调用）
  ↓
done 事件（执行完成）
```

### 5.2 图片事件格式

```json
{
  "type": "image",
  "url": "https://example.com/generated-image.png",
  "alt": "一只橘猫在阳光下打盹"
}
```

前端收到后：
1. 找到当前正在显示的AI消息气泡
2. 在文字内容后追加图片
3. 图片使用 `<img>` 标签，支持点击放大

## 6. 技术细节

### 6.1 图片URL处理

- 图片URL由Agent调用的多模态模型返回
- 前端直接渲染URL，无需额外下载
- 如果图片是base64格式，事件中传递完整data URL

### 6.2 模型解析

`DeepAgentsRunner._resolve_model()` 方法扩展：
1. 检查请求中是否有 `model_config_id`
2. 如果有，使用该配置
3. 否则使用Agent的 `model_config_id`
4. 都没有则使用系统默认模型

### 6.3 前端SSE处理

```typescript
// 处理image事件
if (event.type === 'image') {
  appendImageToCurrentMessage(event.url, event.alt);
}
```

## 7. 实现步骤

1. 后端：添加 ModelConfig 数据模型和CRUD API
2. 后端：修改 Agent 执行端点，支持临时模型覆盖
3. 后端：SSE事件流新增 `image` 事件类型
4. 前端：模型选择器组件
5. 前端：SSE事件处理，图片内联渲染
6. 前端：图片点击放大功能

## 8. 影响范围

- 新增 `model_configs` 表
- 修改 `agents` 表（已有 `model_config_id` 字段，无需迁移）
- 修改 `agents.py` API
- 修改 `wrapper.py` runner
- 新增前端模型配置页面（可选）
- 修改 AgentDetailView 页面