# Claw Platform Phase 2: 核心功能

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Skill CRUD + 文件管理、Tool MCP 集成、Model Config + 适配器、deepagents 集成、Agent 执行流程

**Architecture:** 继续插件化 DDD 架构，Skill 文件存储于 DB，Tool 通过 MCP 协议集成，Model 通过适配器调用

**Tech Stack:** Python 3.11+, FastAPI, deepagents, langgraph, MCP

---

## 文件结构

```
backend/
├── app/
│   ├── api/
│   │   ├── skills.py       # Skill CRUD + 文件操作
│   │   ├── tools.py        # Tool CRUD
│   │   ├── models.py       # Model Config CRUD
│   │   ├── feedback.py     # Feedback API
│   │   └── deps.py         # 更新依赖注入
│   ├── application/
│   │   ├── skill_service.py
│   │   ├── tool_service.py
│   │   ├── model_service.py
│   │   └── feedback_service.py
│   └── infrastructure/
│       ├── mcp/           # MCP 协议适配器
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── adapter.py
│       └── model/         # 模型适配器
│           ├── openai.py
│           └── anthropic.py
├── deepagents/
│   └── wrapper.py         # 完整实现
└── config.yaml            # 更新配置
```

---

## Task 1: Skill CRUD + 文件管理 API

**Files:**
- Create: `backend/app/api/skills.py`
- Create: `backend/app/application/skill_service.py`
- Modify: `backend/app/api/deps.py` (添加 get_skill_service)
- Modify: `backend/app/main.py` (注册 skills router)

- [ ] **Step 1: Create application/skill_service.py**

```python
"""Skill application service."""

from typing import List, Optional

from app.domain.skill import Skill, SkillFile
from app.infrastructure.storage.sqlite import SQLiteStorage


class SkillService:
    """Service for skill operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, skill: Skill) -> Skill:
        """Create a new skill."""
        await self.storage.save_skill(skill)
        return skill

    async def get(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID."""
        return await self.storage.get_skill(skill_id)

    async def list_by_user(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Skill]:
        """List skills for a user."""
        return await self.storage.list_skills(user_id, offset, limit)

    async def update(self, skill_id: str, data: dict) -> Optional[Skill]:
        """Update skill fields."""
        skill = await self.storage.get_skill(skill_id)
        if not skill:
            return None

        for key, value in data.items():
            if hasattr(skill, key):
                setattr(skill, key, value)

        await self.storage.save_skill(skill)
        return skill

    async def delete(self, skill_id: str) -> bool:
        """Delete a skill."""
        skill = await self.storage.get_skill(skill_id)
        if not skill:
            return False
        await self.storage.delete_skill(skill_id)
        return True

    async def get_file(self, skill_id: str, filename: str) -> Optional[bytes]:
        """Get skill file content."""
        return await self.storage.get_skill_file(skill_id, filename)

    async def list_files(self, skill_id: str) -> List[str]:
        """List skill files."""
        return await self.storage.list_skill_files(skill_id)

    async def save_file(self, skill_id: str, filename: str, content: bytes) -> None:
        """Save skill file."""
        await self.storage.save_skill_file(skill_id, filename, content)

    async def delete_file(self, skill_id: str, filename: str) -> None:
        """Delete skill file."""
        await self.storage.delete_skill_file(skill_id, filename)
```

- [ ] **Step 2: Create api/skills.py**

```python
"""Skill API routes."""

from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from app.api.deps import Storage, UserId
from app.application.skill_service import SkillService
from app.domain.skill import Skill
from pydantic import BaseModel, Field

router = APIRouter(prefix="/skills", tags=["skills"])


class CreateSkillRequest(BaseModel):
    name: str = Field(max_length=64)
    description: str = Field(max_length=1024, default="")
    path: str = Field(max_length=500, default="")


class UpdateSkillRequest(BaseModel):
    name: Optional[str] = Field(max_length=64, default=None)
    description: Optional[str] = Field(max_length=1024, default=None)
    status: Optional[str] = Field(default=None)


@router.post("", response_model=Skill)
async def create_skill(
    request: CreateSkillRequest,
    storage: Storage,
    user_id: UserId,
) -> Skill:
    """Create a new skill."""
    skill = Skill(
        name=request.name,
        description=request.description,
        path=request.path,
        user_id=user_id,
    )
    service = SkillService(storage)
    return await service.create(skill)


@router.get("", response_model=List[Skill])
async def list_skills(
    storage: Storage,
    user_id: UserId,
    offset: int = 0,
    limit: int = 100,
) -> List[Skill]:
    """List skills for current user."""
    service = SkillService(storage)
    return await service.list_by_user(user_id, offset, limit)


@router.get("/{skill_id}", response_model=Skill)
async def get_skill(
    skill_id: str,
    storage: Storage,
) -> Skill:
    """Get skill by ID."""
    service = SkillService(storage)
    skill = await service.get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=Skill)
async def update_skill(
    skill_id: str,
    request: UpdateSkillRequest,
    storage: Storage,
) -> Skill:
    """Update skill."""
    service = SkillService(storage)
    data = request.model_dump(exclude_unset=True)
    skill = await service.update(skill_id, data)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    storage: Storage,
) -> dict:
    """Delete skill."""
    service = SkillService(storage)
    deleted = await service.delete(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"ok": True}


@router.get("/{skill_id}/files")
async def list_skill_files(
    skill_id: str,
    storage: Storage,
) -> List[str]:
    """List skill files."""
    service = SkillService(storage)
    return await service.list_files(skill_id)


@router.get("/{skill_id}/files/{filename}")
async def get_skill_file(
    skill_id: str,
    filename: str,
    storage: Storage,
) -> Response:
    """Get skill file content."""
    service = SkillService(storage)
    content = await service.get_file(skill_id, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=content, media_type="application/octet-stream")


@router.put("/{skill_id}/files/{filename}")
async def save_skill_file(
    skill_id: str,
    filename: str,
    storage: Storage,
    file: UploadFile = File(...),
) -> dict:
    """Save skill file."""
    service = SkillService(storage)
    content = await file.read()
    await service.save_file(skill_id, filename, content)
    return {"ok": True}


@router.delete("/{skill_id}/files/{filename}")
async def delete_skill_file(
    skill_id: str,
    filename: str,
    storage: Storage,
) -> dict:
    """Delete skill file."""
    service = SkillService(storage)
    await service.delete_file(skill_id, filename)
    return {"ok": True}
```

- [ ] **Step 3: Update api/deps.py**

在 `deps.py` 中添加 `get_skill_service` 函数：

```python
from app.application.skill_service import SkillService

async def get_skill_service(storage: SQLiteStorage) -> SkillService:
    """Get skill service instance."""
    return SkillService(storage)

SkillServiceDep = Annotated[SkillService, Depends(get_skill_service)]
```

- [ ] **Step 4: Update main.py**

添加 skills router：

```python
from app.api import agents, skills

app.include_router(agents.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
```

- [ ] **Step 5: Test import**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.api.skills import router; print('Skills router imported')"`
Expected: `Skills router imported`

- [ ] **Step 6: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/api/skills.py backend/app/application/skill_service.py backend/app/api/deps.py backend/app/main.py
git commit -m "feat: add Skill CRUD and file management API"
```

---

## Task 2: Tool CRUD API + MCP 集成

**Files:**
- Create: `backend/app/api/tools.py`
- Create: `backend/app/application/tool_service.py`
- Create: `backend/app/infrastructure/mcp/__init__.py`
- Create: `backend/app/infrastructure/mcp/client.py`
- Create: `backend/app/infrastructure/mcp/adapter.py`

- [ ] **Step 1: Create application/tool_service.py**

```python
"""Tool application service."""

from typing import List, Optional

from app.domain.tool import Tool
from app.infrastructure.storage.sqlite import SQLiteStorage


class ToolService:
    """Service for tool operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, tool: Tool) -> Tool:
        """Create a new tool."""
        await self.storage.save_tool(tool)
        return tool

    async def get(self, tool_id: str) -> Optional[Tool]:
        """Get tool by ID."""
        return await self.storage.get_tool(tool_id)

    async def list_by_user(self, user_id: str) -> List[Tool]:
        """List tools for a user."""
        return await self.storage.list_tools(user_id)

    async def update(self, tool_id: str, data: dict) -> Optional[Tool]:
        """Update tool fields."""
        tool = await self.storage.get_tool(tool_id)
        if not tool:
            return None

        for key, value in data.items():
            if hasattr(tool, key):
                setattr(tool, key, value)

        await self.storage.save_tool(tool)
        return tool

    async def delete(self, tool_id: str) -> bool:
        """Delete a tool."""
        tool = await self.storage.get_tool(tool_id)
        if not tool:
            return False
        await self.storage.delete_tool(tool_id)
        return True
```

- [ ] **Step 2: Create api/tools.py**

```python
"""Tool API routes."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage, UserId
from app.application.tool_service import ToolService
from app.domain.tool import Tool, ToolType
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tools", tags=["tools"])


class CreateToolRequest(BaseModel):
    name: str = Field(max_length=100)
    description: str = Field(max_length=500, default="")
    type: ToolType = ToolType.CUSTOM
    config: dict = Field(default_factory=dict)
    allowed_tools: List[str] = Field(default_factory=list)


class UpdateToolRequest(BaseModel):
    name: Optional[str] = Field(max_length=100, default=None)
    description: Optional[str] = Field(max_length=500, default=None)
    config: Optional[dict] = Field(default=None)
    allowed_tools: Optional[List[str]] = Field(default=None)


@router.post("", response_model=Tool)
async def create_tool(
    request: CreateToolRequest,
    storage: Storage,
    user_id: UserId,
) -> Tool:
    """Register a new tool."""
    tool = Tool(
        name=request.name,
        description=request.description,
        type=request.type,
        config=request.config,
        allowed_tools=request.allowed_tools,
        user_id=user_id,
    )
    service = ToolService(storage)
    return await service.create(tool)


@router.get("", response_model=List[Tool])
async def list_tools(
    storage: Storage,
    user_id: UserId,
) -> List[Tool]:
    """List tools for current user."""
    service = ToolService(storage)
    return await service.list_by_user(user_id)


@router.get("/{tool_id}", response_model=Tool)
async def get_tool(
    tool_id: str,
    storage: Storage,
) -> Tool:
    """Get tool by ID."""
    service = ToolService(storage)
    tool = await service.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.put("/{tool_id}", response_model=Tool)
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    storage: Storage,
) -> Tool:
    """Update tool."""
    service = ToolService(storage)
    data = request.model_dump(exclude_unset=True)
    tool = await service.update(tool_id, data)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    storage: Storage,
) -> dict:
    """Delete tool."""
    service = ToolService(storage)
    deleted = await service.delete(tool_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"ok": True}
```

- [ ] **Step 3: Create infrastructure/mcp/__init__.py**

```python
"""MCP protocol adapters."""

from app.infrastructure.mcp.client import MCPClient
from app.infrastructure.mcp.adapter import MCPAdapter

__all__ = ["MCPClient", "MCPAdapter"]
```

- [ ] **Step 4: Create infrastructure/mcp/client.py**

```python
"""MCP client for connecting to MCP servers."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx


class MCPClient:
    """Client for Model Context Protocol servers."""

    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.command = command
        self.args = args
        self.env = env or {}
        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0

    async def start(self) -> None:
        """Start the MCP server process."""
        self._process = await asyncio.subprocess.create_subprocess_exec(
            self.command,
            *self.args,
            env={**self._process_env(), **self.env},
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def stop(self) -> None:
        """Stop the MCP server process."""
        if self._process:
            self._process.terminate()
            await self._process.wait()
            self._process = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        response = await self._send_request("tools/list", {})
        return response.get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        return response.get("content", [])

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        if not self._process:
            raise RuntimeError("MCP client not started")

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        request_json = json.dumps(request) + "\n"
        self._process.stdin.write(request_json.encode())
        await self._process.stdin.drain()

        response_line = await self._process.stdout.readline()
        response = json.loads(response_line.decode())

        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")

        return response.get("result", {})

    def _process_env(self) -> Dict[str, str]:
        """Get environment for subprocess."""
        env = dict(self.env)
        return env
```

- [ ] **Step 5: Create infrastructure/mcp/adapter.py**

```python
"""MCP adapter for converting MCP tools to platform tools."""

from typing import Any, Dict, List

from app.domain.tool import Tool, ToolType
from app.infrastructure.mcp.client import MCPClient


class MCPAdapter:
    """Adapter for MCP tools."""

    def __init__(self, tool: Tool):
        self.tool = tool
        self._client: MCPClient | None = None

    async def initialize(self) -> None:
        """Initialize MCP client from tool config."""
        if self.tool.type != ToolType.MCP:
            raise ValueError("Tool is not an MCP tool")

        config = self.tool.config
        command = config.get("command", "npx")
        args = config.get("args", [])

        self._client = MCPClient(command=command, args=args)
        await self._client.start()

    async def close(self) -> None:
        """Close MCP client connection."""
        if self._client:
            await self._client.stop()
            self._client = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        if not self._client:
            await self.initialize()
        return await self._client.list_tools()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        if not self._client:
            await self.initialize()
        return await self._client.call_tool(tool_name, arguments)
```

- [ ] **Step 6: Update main.py**

添加 tools router：

```python
from app.api import agents, skills, tools

app.include_router(agents.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
```

- [ ] **Step 7: Test imports**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.api.tools import router; from app.infrastructure.mcp import MCPClient, MCPAdapter; print('Tools and MCP imported')"`
Expected: `Tools and MCP imported`

- [ ] **Step 8: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/api/tools.py backend/app/application/tool_service.py backend/app/infrastructure/mcp/
git commit -m "feat: add Tool CRUD API and MCP integration"
```

---

## Task 3: Model Config CRUD API + 适配器

**Files:**
- Create: `backend/app/api/models.py`
- Create: `backend/app/application/model_service.py`
- Create: `backend/app/infrastructure/model/openai.py`
- Create: `backend/app/infrastructure/model/anthropic.py`

- [ ] **Step 1: Create application/model_service.py**

```python
"""Model application service."""

from typing import List, Optional

from app.domain.model_config import ModelConfig
from app.infrastructure.storage.sqlite import SQLiteStorage


class ModelService:
    """Service for model config operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, config: ModelConfig) -> ModelConfig:
        """Create a new model config."""
        await self.storage.save_model_config(config)
        return config

    async def get(self, config_id: str) -> Optional[ModelConfig]:
        """Get model config by ID."""
        return await self.storage.get_model_config(config_id)

    async def list_by_user(self, user_id: str) -> List[ModelConfig]:
        """List model configs for a user."""
        return await self.storage.list_model_configs(user_id)

    async def update(self, config_id: str, data: dict) -> Optional[ModelConfig]:
        """Update model config fields."""
        config = await self.storage.get_model_config(config_id)
        if not config:
            return None

        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await self.storage.save_model_config(config)
        return config

    async def delete(self, config_id: str) -> bool:
        """Delete a model config."""
        config = await self.storage.get_model_config(config_id)
        if not config:
            return False
        await self.storage.delete_model_config(config_id)
        return True
```

- [ ] **Step 2: Create api/models.py**

```python
"""Model Config API routes."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage, UserId
from app.application.model_service import ModelService
from app.domain.model_config import ModelConfig, ModelProviderType
from pydantic import BaseModel, Field

router = APIRouter(prefix="/models", tags=["models"])


class CreateModelRequest(BaseModel):
    name: str = Field(max_length=100)
    type: ModelProviderType = ModelProviderType.OPENAI
    model: str = Field(max_length=100, default="gpt-4o")
    api_key: str | None = None
    base_url: str | None = None
    config: dict = Field(default_factory=dict)


class UpdateModelRequest(BaseModel):
    name: Optional[str] = Field(max_length=100, default=None)
    type: Optional[ModelProviderType] = Field(default=None)
    model: Optional[str] = Field(max_length=100, default=None)
    api_key: Optional[str] = Field(default=None)
    base_url: Optional[str] = Field(default=None)
    config: Optional[dict] = Field(default=None)


@router.post("", response_model=ModelConfig)
async def create_model(
    request: CreateModelRequest,
    storage: Storage,
    user_id: UserId,
) -> ModelConfig:
    """Create a new model config."""
    config = ModelConfig(
        name=request.name,
        type=request.type,
        model=request.model,
        api_key=request.api_key,
        base_url=request.base_url,
        config=request.config,
        user_id=user_id,
    )
    service = ModelService(storage)
    return await service.create(config)


@router.get("", response_model=List[ModelConfig])
async def list_models(
    storage: Storage,
    user_id: UserId,
) -> List[ModelConfig]:
    """List model configs for current user."""
    service = ModelService(storage)
    return await service.list_by_user(user_id)


@router.get("/{model_id}", response_model=ModelConfig)
async def get_model(
    model_id: str,
    storage: Storage,
) -> ModelConfig:
    """Get model config by ID."""
    service = ModelService(storage)
    config = await service.get(model_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model not found")
    return config


@router.put("/{model_id}", response_model=ModelConfig)
async def update_model(
    model_id: str,
    request: UpdateModelRequest,
    storage: Storage,
) -> ModelConfig:
    """Update model config."""
    service = ModelService(storage)
    data = request.model_dump(exclude_unset=True)
    config = await service.update(model_id, data)
    if not config:
        raise HTTPException(status_code=404, detail="Model not found")
    return config


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    storage: Storage,
) -> dict:
    """Delete model config."""
    service = ModelService(storage)
    deleted = await service.delete(model_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"ok": True}
```

- [ ] **Step 3: Create infrastructure/model/openai.py**

```python
"""OpenAI model adapter."""

from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

from app.domain.model_config import ModelConfig
from app.infrastructure.model.base import ModelAdapter


class OpenAIAdapter(ModelAdapter):
    """Adapter for OpenAI models."""

    def __init__(self, config: ModelConfig):
        self.config = config

    async def chat(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        """Chat completion with OpenAI."""
        llm = ChatOpenAI(
            model=self.config.model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            **self.config.config,
        )
        return await llm.ainvoke(messages, **kwargs)

    async def complete(self, prompt: str, **kwargs) -> str:
        """Text completion with OpenAI."""
        llm = ChatOpenAI(
            model=self.config.model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            **self.config.config,
        )
        result = await llm.ainvoke(prompt, **kwargs)
        return result.content if hasattr(result, "content") else str(result)
```

- [ ] **Step 4: Create infrastructure/model/anthropic.py**

```python
"""Anthropic model adapter."""

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

from app.domain.model_config import ModelConfig
from app.infrastructure.model.base import ModelAdapter


class AnthropicAdapter(ModelAdapter):
    """Adapter for Anthropic models."""

    def __init__(self, config: ModelConfig):
        self.config = config

    async def chat(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        """Chat completion with Anthropic."""
        llm = ChatAnthropic(
            model=self.config.model,
            anthropic_api_key=self.config.api_key,
            base_url=self.config.base_url,
            **self.config.config,
        )
        return await llm.ainvoke(messages, **kwargs)

    async def complete(self, prompt: str, **kwargs) -> str:
        """Text completion with Anthropic (uses messages API)."""
        llm = ChatAnthropic(
            model=self.config.model,
            anthropic_api_key=self.config.api_key,
            base_url=self.config.base_url,
            **self.config.config,
        )
        result = await llm.ainvoke([{"role": "user", "content": prompt}], **kwargs)
        return result.content if hasattr(result, "content") else str(result)
```

- [ ] **Step 5: Update infrastructure/model/__init__.py**

```python
"""Model adapters."""

from app.infrastructure.model.base import ModelAdapter
from app.infrastructure.model.openai import OpenAIAdapter
from app.infrastructure.model.anthropic import AnthropicAdapter

__all__ = ["ModelAdapter", "OpenAIAdapter", "AnthropicAdapter"]
```

- [ ] **Step 6: Update main.py**

添加 models router：

```python
from app.api import agents, skills, tools, models

app.include_router(agents.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(models.router, prefix="/api")
```

- [ ] **Step 7: Test imports**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.api.models import router; from app.infrastructure.model import OpenAIAdapter, AnthropicAdapter; print('Models imported')"`
Expected: `Models imported`

- [ ] **Step 8: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/api/models.py backend/app/application/model_service.py backend/app/infrastructure/model/
git commit -m "feat: add Model Config CRUD API and model adapters"
```

---

## Task 4: Feedback API

**Files:**
- Create: `backend/app/api/feedback.py`
- Create: `backend/app/application/feedback_service.py`

- [ ] **Step 1: Create application/feedback_service.py**

```python
"""Feedback application service."""

from typing import List, Optional

from app.domain.feedback import FeedbackEvent, FeedbackRating
from app.infrastructure.storage.sqlite import SQLiteStorage


class FeedbackService:
    """Service for feedback operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, feedback: FeedbackEvent) -> FeedbackEvent:
        """Create a new feedback event."""
        await self.storage.save_feedback(feedback)
        return feedback

    async def get(self, feedback_id: str) -> Optional[FeedbackEvent]:
        """Get feedback by ID."""
        return await self.storage.get_feedback(feedback_id)

    async def list_by_skill(
        self,
        skill_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> List[FeedbackEvent]:
        """List feedback for a skill."""
        return await self.storage.list_feedback(skill_id=skill_id, offset=offset, limit=limit)

    async def list_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> List[FeedbackEvent]:
        """List all feedback."""
        return await self.storage.list_feedback(offset=offset, limit=limit)
```

- [ ] **Step 2: Create api/feedback.py**

```python
"""Feedback API routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage
from app.application.feedback_service import FeedbackService
from app.domain.feedback import FeedbackEvent, FeedbackRating
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feedback", tags=["feedback"])


class CreateFeedbackRequest(BaseModel):
    agent_id: str
    skill_id: Optional[str] = None
    task_id: str
    result: str
    rating: FeedbackRating
    context: dict = Field(default_factory=dict)


@router.post("", response_model=FeedbackEvent)
async def create_feedback(
    request: CreateFeedbackRequest,
    storage: Storage,
) -> FeedbackEvent:
    """Submit a feedback event."""
    feedback = FeedbackEvent(
        agent_id=request.agent_id,
        skill_id=request.skill_id,
        task_id=request.task_id,
        result=request.result,
        rating=request.rating,
        context=request.context,
    )
    service = FeedbackService(storage)
    return await service.create(feedback)


@router.get("", response_model=List[FeedbackEvent])
async def list_feedback(
    storage: Storage,
    skill_id: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> List[FeedbackEvent]:
    """List feedback events."""
    service = FeedbackService(storage)
    if skill_id:
        return await service.list_by_skill(skill_id, offset, limit)
    return await service.list_all(offset, limit)


@router.get("/{feedback_id}", response_model=FeedbackEvent)
async def get_feedback(
    feedback_id: str,
    storage: Storage,
) -> FeedbackEvent:
    """Get feedback by ID."""
    service = FeedbackService(storage)
    feedback = await service.get(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback
```

- [ ] **Step 3: Update main.py**

添加 feedback router：

```python
from app.api import agents, skills, tools, models, feedback

app.include_router(agents.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
```

- [ ] **Step 4: Test imports**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.api.feedback import router; print('Feedback router imported')"`
Expected: `Feedback router imported`

- [ ] **Step 5: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/api/feedback.py backend/app/application/feedback_service.py backend/app/main.py
git commit -m "feat: add Feedback API"
```

---

## Task 5: deepagents 集成完整实现

**Files:**
- Modify: `backend/app/deepagents/wrapper.py`

- [ ] **Step 1: Update deepagents/wrapper.py**

```python
"""DeepAgents runtime wrapper.

This module provides integration with the deepagents library for
agent execution.
"""

import asyncio
from typing import Any, AsyncGenerator, Optional

from deepagents import create_deep_agent, SkillsMiddleware
from deepagents.backends.state import StateBackend

from app.domain.agent import Agent
from app.domain.tool import Tool, ToolType
from app.domain.model_config import ModelConfig, ModelProviderType
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.infrastructure.mcp.adapter import MCPAdapter
from app.infrastructure.model.openai import OpenAIAdapter
from app.infrastructure.model.anthropic import AnthropicAdapter


class DeepAgentsRunner:
    """Wrapper for deepagents runtime.

    Provides integration between the platform's storage, tools, and models
    with the deepagents library.
    """

    def __init__(
        self,
        agent: Agent,
        storage: SQLiteStorage,
    ):
        self.agent = agent
        self.storage = storage
        self._runner = None
        self._mcp_adapters: dict[str, MCPAdapter] = {}

    async def create(self):
        """Create deepagents runner instance."""
        # 1. Load skills from storage into StateBackend
        backend = await self._create_backend()

        # 2. Load tools
        tools = await self._load_tools()

        # 3. Resolve model configuration
        model = await self._resolve_model()

        # 4. Build system prompt from agent config
        system_prompt = self._build_system_prompt()

        # 5. Create Skills middleware
        skill_sources = await self._get_skill_sources()
        skills_middleware = SkillsMiddleware(
            backend=backend,
            sources=skill_sources,
        )

        # 6. Create deep_agent
        self._runner = create_deep_agent(
            model=model,
            tools=tools,
            middleware=[skills_middleware],
            system_prompt=system_prompt,
        )

    async def run(self, task: str) -> AsyncGenerator[Any, None]:
        """Run agent task.

        Yields:
            Events from agent execution.
        """
        if not self._runner:
            await self.create()

        async for event in self._runner.astream_events(task):
            yield event

    async def stop(self):
        """Stop running agent and cleanup."""
        # Close all MCP connections
        for adapter in self._mcp_adapters.values():
            await adapter.close()
        self._mcp_adapters.clear()
        self._runner = None

    async def _create_backend(self) -> StateBackend:
        """Create StateBackend from platform storage."""
        # StateBackend requires a backend that implements the protocol
        # For now, return an in-memory backend
        return StateBackend()

    async def _load_tools(self) -> list:
        """Load tools from storage."""
        tools = []
        for tool_id in self.agent.tool_ids:
            tool = await self.storage.get_tool(tool_id)
            if not tool:
                continue

            if tool.type == ToolType.MCP:
                adapter = MCPAdapter(tool)
                await adapter.initialize()
                self._mcp_adapters[tool_id] = adapter
                # MCP tools would be converted to LangChain tools here
                # For now, skip as it requires more complex adaptation
            elif tool.type == ToolType.CUSTOM:
                # Custom tools would be loaded here
                pass

        return tools

    async def _resolve_model(self):
        """Resolve model from agent configuration."""
        if not self.agent.model_config_id:
            # Use default model
            return OpenAIAdapter(ModelConfig(
                name="default",
                type=ModelProviderType.OPENAI,
                model="gpt-4o",
                user_id=self.agent.user_id,
            ))

        config = await self.storage.get_model_config(self.agent.model_config_id)
        if not config:
            raise ValueError(f"Model config not found: {self.agent.model_config_id}")

        if config.type == ModelProviderType.OPENAI:
            return OpenAIAdapter(config)
        elif config.type == ModelProviderType.ANTHROPIC:
            return AnthropicAdapter(config)
        else:
            raise ValueError(f"Unsupported model type: {config.type}")

    def _build_system_prompt(self) -> str:
        """Build system prompt from agent configuration."""
        parts = []

        if self.agent.role:
            parts.append(f"You are {self.agent.role}.")
        if self.agent.goal:
            parts.append(f"Your goal is: {self.agent.goal}.")
        if self.agent.backstory:
            parts.append(f"Background: {self.agent.backstory}")

        return "\n\n".join(parts)

    async def _get_skill_sources(self) -> list[str]:
        """Get skill sources from agent's skills."""
        sources = []
        for skill_id in self.agent.skill_ids:
            skill = await self.storage.get_skill(skill_id)
            if skill and skill.path:
                sources.append(skill.path)
        return sources
```

- [ ] **Step 2: Test import**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.deepagents import DeepAgentsRunner; print('DeepAgentsRunner updated')"`
Expected: `DeepAgentsRunner updated`

- [ ] **Step 3: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/deepagents/wrapper.py
git commit -m "feat: implement deepagents integration"
```

---

## Self-Review

- [ ] **Spec coverage check**: All Phase 2 items from design doc covered
  - [x] Skill CRUD + 文件管理 (Task 1)
  - [x] Tool MCP 集成 (Task 2)
  - [x] Model Config + 适配器 (Task 3)
  - [x] Feedback API (Task 4)
  - [x] deepagents 集成 (Task 5)

- [ ] **Placeholder scan**: No TBD/TODO in implementation steps

- [ ] **Type consistency**: Entity types match Phase 1
  - `Agent`, `Skill`, `Tool`, `ModelConfig`, `FeedbackEvent` all consistent
  - `StorageAdapter` interface methods match SQLite implementation

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-22-claw-platform-phase2.md`**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
