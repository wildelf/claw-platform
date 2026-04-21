# Claw Platform 设计文档

## 项目概述

**项目名称**: Claw Platform
**项目类型**: 自主执行型智能体平台
**核心功能**: 用户可创建智能体(Agent)、技能(Skill)、工具(Tool)，配置多模型协作，通过反馈驱动 Skill 自动进化
**技术栈**: Python (FastAPI) + Vue

---

## 一、核心领域实体

### 1.1 Agent (智能体)

```python
class Agent:
    id: str                          # UUID
    name: str                        # 名称
    description: str                 # 描述
    role: str                        # 角色描述
    goal: str                        # 目标
    backstory: str                   # 背景故事
    skill_ids: List[str]            # 关联的 Skills
    tool_ids: List[str]             # 关联的 Tools
    model_config_id: str             # 使用的模型配置
    status: AgentStatus              # pending / active / paused
    user_id: str                     # 所属用户
    created_at: datetime
    updated_at: datetime
```

### 1.2 Skill (技能)

```python
class Skill:
    id: str                          # UUID
    name: str                        # 标识符 (max 64 chars, lowercase alphanumeric + hyphens)
    description: str                 # 描述 (max 1024 chars)
    path: str                        # 存储路径 (如 /skills/user/web-research/)
    files: List[SkillFile]           # 文件列表
    status: SkillStatus               # pending / trained / evolved
    feedback_count: int              # 累积正反馈数
    version: int                     # 版本号
    metadata: Dict[str, Any]        # 扩展元数据 (license, compatibility 等)
    user_id: str                     # 所属用户
    created_at: datetime
    updated_at: datetime

class SkillFile:
    filename: str                    # 文件名 (SKILL.md, helper.py 等)
    content: bytes                   # 文件内容
    file_type: FileType              # markdown / python / other
```

**Skill 文件结构**:
```
/skills/{user_id}/{skill-name}/
├── SKILL.md          # 必需: YAML frontmatter + markdown 指令
└── helper.py         # 可选: Python 辅助代码
```

**SKILL.md 格式**:
```markdown
---
name: web-research
description: Structured approach to conducting thorough web research
license: MIT
---

# Web Research Skill

## When to Use
- User asks you to research a topic
...
```

### 1.3 Tool (工具)

```python
class Tool:
    id: str                          # UUID
    name: str                        # 工具名称
    description: str                 # 描述
    type: ToolType                   # mcp / custom
    config: Dict[str, Any]          # MCP 连接配置或自定义配置
    allowed_tools: List[str]        # 允许调用的子工具列表 (MCP)
    user_id: str                     # 所属用户
    created_at: datetime
```

### 1.4 ModelConfig (模型配置)

```python
class ModelConfig:
    id: str                          # UUID
    name: str                        # 配置名称
    type: ModelProviderType          # openai / anthropic / local / deepseek 等
    model: str                       # 模型 ID (如 gpt-4, claude-3-opus)
    api_key: Optional[str]           # API Key (可加密存储)
    base_url: Optional[str]          # 自定义 API 端点
    config: Dict[str, Any]          # 额外配置 (temperature, max_tokens 等)
    user_id: str                     # 所属用户
    created_at: datetime

class ModelRole:
    PLANNER = "planner"              # 规划模型
    EXECUTOR = "executor"            # 执行模型
    CRITIC = "critic"                # 评判模型
```

### 1.5 FeedbackEvent (反馈事件)

```python
class FeedbackEvent:
    id: str                          # UUID
    agent_id: str                    # 关联的 Agent
    skill_id: str                    # 关联的 Skill
    task_id: str                     # 关联的任务
    result: str                      # 执行结果
    rating: FeedbackRating            # positive / negative
    context: Dict[str, Any]          # 执行上下文
    created_at: datetime
```

### 1.6 User (用户)

```python
class User:
    id: str                          # UUID
    username: str                     # 用户名
    email: str                        # 邮箱
    password_hash: str                # 密码哈希
    role: UserRole                    # admin / user
    is_active: bool                  # 是否激活
    created_at: datetime
```

---

## 二、系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Vue Frontend (管理界面)                      │
├─────────────────────────────────────────────────────────────┤
│                      FastAPI REST API                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Agent API   │  │ Skill API   │  │ Tool/Model/User API │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ AgentService │  │SkillService │  │ FeedbackService     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  │Agent │ │Skill │ │ Tool │ │Model │ │ User │            │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘            │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                       │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Storage Adapter │  │  MCP Adapter   │  │Model Adapter │  │
│  │  (可插拔存储)    │  │ (MCP 协议)     │  │ (模型调用)   │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    deepagents 运行时                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ LangGraph    │  │SkillsMiddleware│ │ SubAgent           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 项目结构

```
claw-platform/
├── backend/
│   ├── app/
│   │   ├── api/                    # FastAPI 路由
│   │   │   ├── __init__.py
│   │   │   ├── agents.py           # Agent CRUD + run/stop
│   │   │   ├── skills.py           # Skill CRUD + 文件操作
│   │   │   ├── tools.py            # Tool 注册管理
│   │   │   ├── models.py           # Model Config CRUD
│   │   │   ├── users.py            # 用户认证
│   │   │   ├── feedback.py         # 反馈提交
│   │   │   └── deps.py             # 依赖注入
│   │   ├── application/            # Use Cases, Services, Events
│   │   │   ├── __init__.py
│   │   │   ├── agent_service.py
│   │   │   ├── skill_service.py
│   │   │   ├── tool_service.py
│   │   │   ├── model_service.py
│   │   │   ├── feedback_service.py
│   │   │   └── events.py           # 事件定义
│   │   ├── domain/                 # 领域实体
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── skill.py
│   │   │   ├── tool.py
│   │   │   ├── model_config.py
│   │   │   ├── feedback.py
│   │   │   └── user.py
│   │   └── infrastructure/         # 可插拔实现
│   │       ├── __init__.py
│   │       ├── storage/            # 存储适配器
│   │       │   ├── __init__.py
│   │       │   ├── base.py         # StorageAdapter 接口
│   │       │   ├── sqlite.py       # SQLite 实现
│   │       │   ├── postgres.py     # PostgreSQL 实现
│   │       │   └── memory.py       # 内存实现 (测试用)
│   │       ├── mcp/                # MCP 协议适配器
│   │       │   ├── __init__.py
│   │       │   ├── client.py       # MCP Client
│   │       │   └── adapter.py     # Tool 适配
│   │       └── model/               # 模型适配器
│   │           ├── __init__.py
│   │           ├── base.py         # ModelAdapter 接口
│   │           ├── openai.py
│   │           ├── anthropic.py
│   │           └── local.py
│   ├── deepagents/                  # deepagents 集成
│   │   ├── __init__.py
│   │   └── wrapper.py              # DeepAgentsRunner
│   ├── config.yaml                 # 配置文件
│   ├── main.py                     # FastAPI 入口
│   └── requirements.txt
├── frontend/                       # Vue 项目 (待定)
├── skills/                        # 本地 Skill 示例
│   └── examples/
├── docs/
│   └── specs/
└── tests/
```

---

## 三、API 路由设计

### 3.1 Agent API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/agents` | 创建 Agent |
| GET | `/api/agents` | 列表 Agents (分页) |
| GET | `/api/agents/{id}` | 获取 Agent |
| PUT | `/api/agents/{id}` | 更新 Agent |
| DELETE | `/api/agents/{id}` | 删除 Agent |
| POST | `/api/agents/{id}/run` | 执行任务 |
| POST | `/api/agents/{id}/stop` | 停止执行 |

### 3.2 Skill API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/skills` | 创建 Skill |
| GET | `/api/skills` | 列表 Skills |
| GET | `/api/skills/{id}` | 获取 Skill |
| PUT | `/api/skills/{id}` | 更新 Skill |
| DELETE | `/api/skills/{id}` | 删除 Skill |
| GET | `/api/skills/{id}/files` | 获取 Skill 文件列表 |
| GET | `/api/skills/{id}/files/{filename}` | 获取 Skill 文件内容 |
| PUT | `/api/skills/{id}/files/{filename}` | 更新 Skill 文件 |

### 3.3 Tool API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tools` | 注册 Tool |
| GET | `/api/tools` | 列表 Tools |
| GET | `/api/tools/{id}` | 获取 Tool |
| PUT | `/api/tools/{id}` | 更新 Tool |
| DELETE | `/api/tools/{id}` | 删除 Tool |

### 3.4 Model API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/models` | 创建 Model Config |
| GET | `/api/models` | 列表 Models |
| GET | `/api/models/{id}` | 获取 Model |
| PUT | `/api/models/{id}` | 更新 Model |
| DELETE | `/api/models/{id}` | 删除 Model |

### 3.5 Feedback API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/feedback` | 提交反馈 |
| GET | `/api/feedback` | 列表反馈 (可按 skill_id 筛选) |
| GET | `/api/feedback/{id}` | 获取反馈详情 |

### 3.6 Auth API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 用户登出 |
| GET | `/api/auth/me` | 获取当前用户 |

---

## 四、存储层抽象

### 4.1 StorageAdapter 接口

```python
from typing import Protocol, List, Optional
from pathlib import PurePosixPath

class StorageAdapter(Protocol):
    """存储适配器接口 - 所有存储实现必须实现此接口"""

    # Agent 操作
    async def save_agent(self, agent: Agent) -> None: ...
    async def get_agent(self, id: str) -> Optional[Agent]: ...
    async def list_agents(self, user_id: str, offset: int = 0, limit: int = 100) -> List[Agent]: ...
    async def delete_agent(self, id: str) -> None: ...

    # Skill 操作
    async def save_skill(self, skill: Skill) -> None: ...
    async def get_skill(self, id: str) -> Optional[Skill]: ...
    async def list_skills(self, user_id: str, offset: int = 0, limit: int = 100) -> List[Skill]: ...
    async def delete_skill(self, id: str) -> None: ...
    async def save_skill_file(self, skill_id: str, filename: str, content: bytes) -> None: ...
    async def get_skill_file(self, skill_id: str, filename: str) -> Optional[bytes]: ...
    async def list_skill_files(self, skill_id: str) -> List[str]: ...
    async def delete_skill_file(self, skill_id: str, filename: str) -> None: ...

    # Feedback 操作
    async def save_feedback(self, feedback: FeedbackEvent) -> None: ...
    async def get_feedback(self, id: str) -> Optional[FeedbackEvent]: ...
    async def list_feedback(self, skill_id: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[FeedbackEvent]: ...

    # Tool 操作
    async def save_tool(self, tool: Tool) -> None: ...
    async def get_tool(self, id: str) -> Optional[Tool]: ...
    async def list_tools(self, user_id: str) -> List[Tool]: ...
    async def delete_tool(self, id: str) -> None: ...

    # ModelConfig 操作
    async def save_model_config(self, config: ModelConfig) -> None: ...
    async def get_model_config(self, id: str) -> Optional[ModelConfig]: ...
    async def list_model_configs(self, user_id: str) -> List[ModelConfig]: ...
    async def delete_model_config(self, id: str) -> None: ...
```

### 4.2 配置驱动

```yaml
# config.yaml
storage:
  type: "sqlite"  # 可选: sqlite, postgres, memory

  # SQLite 配置
  sqlite:
    path: "./data/claw.db"

  # PostgreSQL 配置
  postgres:
    host: "localhost"
    port: 5432
    database: "claw"
    username: "user"
    password: "pass"
    pool_size: 10

  # 内存实现 (测试用)
  memory: {}
```

---

## 五、Skill 自进化机制

### 5.1 反馈处理流程

```
1. Agent 执行任务
2. 任务完成，产生执行结果
3. 用户或系统提交 FeedbackEvent:
   - rating: positive / negative
   - context: { task, result, steps, tool_calls }
4. FeedbackService 处理:
   ├── positive feedback:
   │   ├── skill.feedback_count += 1
   │   └── if feedback_count >= threshold (默认 3):
   │       ├── 触发 Skill 生成流程
   │       └── 重置 feedback_count
   └── negative feedback:
       ├── 记录问题到 context.metadata
       └── 标记 skill.status = "needs_review"
```

### 5.2 Skill 生成流程

当 positive feedback 累积达到阈值时:

```
1. 收集该 skill 的所有 positive feedbacks
2. 分析 context，提取:
   - 成功的执行模式 (steps)
   - 使用的工具序列
   - 关键决策点
3. 生成 SKILL.md:
   - name: 从原 skill 继承
   - description: 自动生成描述
   - content: 基于实际执行经验编写
4. 如有辅助代码需求，生成 helper.py
5. 更新 skill.status = "trained"
```

### 5.3 Skill 进化流程

```
1. 持续收集执行反馈
2. positive feedback:
   └── 优化 SKILL.md 中的指令和示例
3. negative feedback:
   └── 在 SKILL.md 中添加警告和注意事项
   └── 版本号 +1
```

---

## 六、MCP 工具集成

### 6.1 MCP Adapter

```python
# backend/app/infrastructure/mcp/adapter.py
class MCPAdapter:
    """MCP 协议适配器 - 将 MCP Tool 转换为平台 Tool"""

    def __init__(self, mcp_client: MCPClient):
        self.client = mcp_client

    async def list_tools(self) -> List[Tool]:
        """从 MCP 服务器获取工具列表"""
        ...

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用 MCP 工具"""
        ...

    async def close(self):
        """关闭连接"""
        ...
```

### 6.2 Tool 注册流程

```python
# 创建 Tool 时指定 MCP 配置
tool = Tool(
    name="filesystem",
    description="File system operations",
    type=ToolType.MCP,
    config={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
)
```

---

## 七、多模型协作

### 7.1 Model Adapter 接口

```python
# backend/app/infrastructure/model/base.py
class ModelAdapter(Protocol):
    """模型适配器接口"""

    async def complete(self, prompt: str, config: ModelConfig) -> str: ...

    async def chat(self, messages: List[Message], config: ModelConfig) -> Message: ...
```

### 7.2 多模型配置示例

```yaml
# config.yaml
models:
  # 默认模型 (用于简单任务)
  default:
    type: "openai"
    model: "gpt-4o"

  # 多模型协作配置
  collaboration:
    planner:
      type: "openai"
      model: "gpt-4"
    executor:
      type: "anthropic"
      model: "claude-3-opus"
    critic:
      type: "openai"
      model: "gpt-4o-mini"
```

### 7.3 Agent 多模型使用

```python
# Agent 可指定使用多模型协作
agent = Agent(
    ...
    model_config_id="collaboration",  # 使用多模型协作
    model_roles={
        "planner": "openai/gpt-4",
        "executor": "anthropic/claude-3-opus",
        "critic": "openai/gpt-4o-mini"
    }
)
```

---

## 八、deepagents 集成

### 8.1 DeepAgentsRunner

```python
# backend/deepagents/wrapper.py
from deepagents import create_deep_agent, SkillsMiddleware
from deepagents.backends.state import StateBackend

class DeepAgentsRunner:
    """deepagents 运行时的平台层封装"""

    def __init__(
        self,
        agent_config: Agent,
        storage: StorageAdapter,
        model_adapter: ModelAdapter
    ):
        self.agent_config = agent_config
        self.storage = storage
        self.model_adapter = model_adapter

    async def create(self):
        """创建 deepagents Agent 实例"""
        # 1. 加载 Skills
        skills_middleware = SkillsMiddleware(
            backend=self._create_backend(),
            sources=await self._get_skill_sources()
        )

        # 2. 加载 Tools (包括 MCP)
        tools = await self._load_tools()

        # 3. 解析模型配置
        model = self._resolve_model()

        # 4. 构建系统提示
        system_prompt = self._build_system_prompt()

        # 5. 创建 Agent
        return create_deep_agent(
            model=model,
            tools=tools,
            middleware=[skills_middleware],
            system_prompt=system_prompt
        )

    async def run(self, task: str, callback=None):
        """执行任务"""
        agent = await self.create()
        # 通过回调返回进度
        async for event in agent.astream_events(task):
            if callback:
                await callback(event)
            yield event
```

### 8.2 Backend 适配

```python
def _create_backend(self):
    """将平台存储适配为 deepagents StateBackend"""
    # deepagents 的 StateBackend 用于存储 Skills 和状态
    # 需要实现 backend.protocol.BackendProtocol
    ...
```

---

## 九、认证与权限

### 9.1 认证方式 (可配置)

```yaml
# config.yaml
auth:
  type: "jwt"  # 可选: jwt, oauth2, api_key

  jwt:
    secret: "your-secret-key"
    algorithm: "HS256"
    expire_minutes: 60 * 24

  # 或 API Key 模式
  api_key:
    enabled: true
```

### 9.2 多租户隔离

所有数据操作必须包含 `user_id` 过滤：
- Agent, Skill, Tool, ModelConfig 都关联 `user_id`
- API 层通过 `deps.py` 注入当前用户
- 存储层自动添加用户过滤条件

---

## 十、实施计划 (建议顺序)

### Phase 1: 基础框架
1. 项目脚手架 (FastAPI + 目录结构)
2. 配置系统 (config.yaml)
3. 领域实体定义
4. 存储层抽象 + SQLite 实现
5. 基础 API (Agent CRUD)

### Phase 2: 核心功能
6. Skill CRUD + 文件管理
7. Tool MCP 集成
8. Model Config + 适配器
9. deepagents 集成
10. Agent 执行流程

### Phase 3: 自我进化
11. Feedback API
12. Skill 生成逻辑
13. Skill 进化逻辑

### Phase 4: 前端与完善
14. Vue 前端项目搭建
15. 前端 API 集成
16. 认证系统
17. 完善与测试
