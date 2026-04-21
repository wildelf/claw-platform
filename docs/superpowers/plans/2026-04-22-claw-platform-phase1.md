# Claw Platform Phase 1: 基础框架

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立项目基础框架，包括目录结构、配置系统、领域实体、存储层抽象和 SQLite 实现、基础 Agent CRUD API

**Architecture:** 采用插件化 DDD 架构，领域层通过接口与基础设施层通信，配置驱动存储和模型适配器切换

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy, SQLite/PostgreSQL

---

## 文件结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置加载器
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # 依赖注入
│   │   └── agents.py        # Agent API 路由
│   ├── application/
│   │   ├── __init__.py
│   │   └── agent_service.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── base.py          # 基础实体类
│   │   ├── agent.py         # Agent 实体
│   │   ├── skill.py         # Skill 实体
│   │   ├── tool.py          # Tool 实体
│   │   ├── model_config.py  # ModelConfig 实体
│   │   └── user.py          # User 实体
│   └── infrastructure/
│       ├── __init__.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── base.py      # StorageAdapter 接口
│       │   └── sqlite.py    # SQLite 实现
│       └── model/
│           ├── __init__.py
│           └── base.py       # ModelAdapter 接口
├── deepagents/
│   └── __init__.py
├── config.yaml
└── requirements.txt
```

---

## Task 1: 项目脚手架与配置系统

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.yaml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`

- [ ] **Step 1: Create requirements.txt**

```txt
# Core
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
sqlalchemy>=2.0.25
aiosqlite>=0.19.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Agent
langgraph>=0.0.20
deepagents>=0.1.0

# HTTP Client
httpx>=0.26.0

# Utils
pyyaml>=6.0.1
```

- [ ] **Step 2: Run requirements install**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && uv pip install -r requirements.txt`
Expected: 安装成功

- [ ] **Step 3: Create config.yaml**

```yaml
app:
  name: "claw-platform"
  debug: true
  host: "0.0.0.0"
  port: 8000

storage:
  type: "sqlite"
  sqlite:
    path: "./data/claw.db"

auth:
  type: "jwt"
  jwt:
    secret: "your-secret-key-change-in-production"
    algorithm: "HS256"
    expire_minutes: 1440

models:
  default:
    type: "openai"
    model: "gpt-4o"
```

- [ ] **Step 4: Create app/__init__.py**

```python
"""Claw Platform Backend Application."""
```

- [ ] **Step 5: Create config.py**

```python
"""Configuration loader for Claw Platform."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    name: str = "claw-platform"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


class SQLiteConfig(BaseModel):
    path: str = "./data/claw.db"


class PostgresConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "claw"
    username: str = "user"
    password: str = "pass"
    pool_size: int = 10


class StorageConfig(BaseModel):
    type: str = "sqlite"  # sqlite, postgres, memory
    sqlite: SQLiteConfig = SQLiteConfig()
    postgres: PostgresConfig = PostgresConfig()


class JWTConfig(BaseModel):
    secret: str
    algorithm: str = "HS256"
    expire_minutes: int = 1440


class AuthConfig(BaseModel):
    type: str = "jwt"
    jwt: JWTConfig


class ModelConfigItem(BaseModel):
    type: str
    model: str
    api_key: str | None = None
    base_url: str | None = None


class ModelsConfig(BaseModel):
    default: ModelConfigItem


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    storage: StorageConfig = StorageConfig()
    auth: AuthConfig
    models: ModelsConfig

    @classmethod
    def from_yaml(cls, path: Path | str) -> "Settings":
        """Load settings from YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(**data)


def get_settings() -> Settings:
    """Get application settings."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    return Settings.from_yaml(config_path)


settings = get_settings()
```

- [ ] **Step 6: Run to verify config loading**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.config import settings; print(settings.app.name)"`
Expected: `claw-platform`

- [ ] **Step 7: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/requirements.txt backend/config.yaml backend/app/__init__.py backend/app/config.py
git commit -m "feat: add project scaffolding and config system"
```

---

## Task 2: 领域实体定义

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/domain/base.py`
- Create: `backend/app/domain/agent.py`
- Create: `backend/app/domain/skill.py`
- Create: `backend/app/domain/tool.py`
- Create: `backend/app/domain/model_config.py`
- Create: `backend/app/domain/user.py`

- [ ] **Step 1: Create domain/__init__.py**

```python
"""Domain entities for Claw Platform."""

from app.domain.base import BaseEntity, EntityId
from app.domain.agent import Agent, AgentStatus
from app.domain.skill import Skill, SkillStatus, SkillFile
from app.domain.tool import Tool, ToolType
from app.domain.model_config import ModelConfig, ModelProviderType
from app.domain.user import User, UserRole

__all__ = [
    "BaseEntity",
    "EntityId",
    "Agent",
    "AgentStatus",
    "Skill",
    "SkillStatus",
    "SkillFile",
    "Tool",
    "ToolType",
    "ModelConfig",
    "ModelProviderType",
    "User",
    "UserRole",
]
```

- [ ] **Step 2: Create domain/base.py**

```python
"""Base classes for domain entities."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EntityId(str):
    """Type-safe entity ID."""

    @classmethod
    def generate(cls) -> "EntityId":
        return cls(str(uuid.uuid4()))


class BaseEntity(BaseModel):
    """Base class for all domain entities."""

    id: EntityId = Field(default_factory=EntityId.generate)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __states: Any) -> None:
        """Update updated_at on init."""
        object.__setattr__(self, "updated_at", datetime.utcnow())
```

- [ ] **Step 3: Create domain/agent.py**

```python
"""Agent domain entity."""

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class AgentStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"


class Agent(BaseEntity):
    """Agent entity representing an AI agent."""

    name: str = Field(max_length=100)
    description: str = Field(max_length=1000, default="")
    role: str = Field(max_length=500, default="")
    goal: str = Field(max_length=1000, default="")
    backstory: str = Field(max_length=2000, default="")
    skill_ids: List[EntityId] = Field(default_factory=list)
    tool_ids: List[EntityId] = Field(default_factory=list)
    model_config_id: EntityId | None = None
    status: AgentStatus = AgentStatus.PENDING
    user_id: EntityId

    class Config:
        use_enum_values = True
```

- [ ] **Step 4: Create domain/skill.py**

```python
"""Skill domain entity."""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class SkillStatus(str, Enum):
    PENDING = "pending"
    TRAINED = "trained"
    EVOLVED = "evolved"
    NEEDS_REVIEW = "needs_review"


class FileType(str, Enum):
    MARKDOWN = "markdown"
    PYTHON = "python"
    OTHER = "other"


class SkillFile(BaseEntity):
    """File within a skill."""

    filename: str = Field(max_length=255)
    content: bytes = b""
    file_type: FileType = FileType.OTHER

    class Config:
        use_enum_values = True


class Skill(BaseEntity):
    """Skill entity representing an agent capability."""

    name: str = Field(max_length=64)
    description: str = Field(max_length=1024, default="")
    path: str = Field(max_length=500, default="")
    status: SkillStatus = SkillStatus.PENDING
    feedback_count: int = 0
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_id: EntityId

    class Config:
        use_enum_values = True
```

- [ ] **Step 5: Create domain/tool.py**

```python
"""Tool domain entity."""

from enum import Enum
from typing import Dict, Any

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class ToolType(str, Enum):
    MCP = "mcp"
    CUSTOM = "custom"


class Tool(BaseEntity):
    """Tool entity representing an external tool or MCP server."""

    name: str = Field(max_length=100)
    description: str = Field(max_length=500, default="")
    type: ToolType = ToolType.CUSTOM
    config: Dict[str, Any] = Field(default_factory=dict)
    allowed_tools: list[str] = Field(default_factory=list)
    user_id: EntityId

    class Config:
        use_enum_values = True
```

- [ ] **Step 6: Create domain/model_config.py**

```python
"""ModelConfig domain entity."""

from enum import Enum
from typing import Dict, Any

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class ModelProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    DEEPSEEK = "deepseek"
    OTHER = "other"


class ModelConfig(BaseEntity):
    """Model configuration entity."""

    name: str = Field(max_length=100)
    type: ModelProviderType = ModelProviderType.OPENAI
    model: str = Field(max_length=100, default="gpt-4o")
    api_key: str | None = None
    base_url: str | None = None
    config: Dict[str, Any] = Field(default_factory=dict)
    user_id: EntityId

    class Config:
        use_enum_values = True
```

- [ ] **Step 7: Create domain/user.py**

```python
"""User domain entity."""

from enum import Enum

from pydantic import Field, EmailStr

from app.domain.base import BaseEntity, EntityId


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseEntity):
    """User entity."""

    username: str = Field(max_length=50)
    email: str = Field(max_length=255)
    password_hash: str = Field(max_length=255)
    role: UserRole = UserRole.USER
    is_active: bool = True

    class Config:
        use_enum_values = True
```

- [ ] **Step 8: Test domain entities**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.domain import Agent, Skill, Tool, ModelConfig, User; print('All entities imported successfully')"`
Expected: `All entities imported successfully`

- [ ] **Step 9: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/domain/
git commit -m "feat: add domain entities"
```

---

## Task 3: 存储层抽象

**Files:**
- Create: `backend/app/infrastructure/__init__.py`
- Create: `backend/app/infrastructure/storage/__init__.py`
- Create: `backend/app/infrastructure/storage/base.py`
- Create: `backend/app/infrastructure/storage/sqlite.py`
- Create: `backend/app/infrastructure/model/__init__.py`
- Create: `backend/app/infrastructure/model/base.py`

- [ ] **Step 1: Create infrastructure/__init__.py**

```python
"""Infrastructure layer for Claw Platform."""
```

- [ ] **Step 2: Create infrastructure/storage/__init__.py**

```python
"""Storage adapters."""

from app.infrastructure.storage.base import StorageAdapter
from app.infrastructure.storage.sqlite import SQLiteStorage

__all__ = ["StorageAdapter", "SQLiteStorage"]
```

- [ ] **Step 3: Create infrastructure/storage/base.py**

```python
"""Storage adapter interface."""

from typing import Protocol, List, Optional

from app.domain.agent import Agent
from app.domain.skill import Skill, SkillFile
from app.domain.tool import Tool
from app.domain.model_config import ModelConfig
from app.domain.feedback import FeedbackEvent


class StorageAdapter(Protocol):
    """Storage adapter protocol.

    All storage implementations must implement this interface.
    """

    # Agent operations
    async def save_agent(self, agent: Agent) -> None: ...
    async def get_agent(self, id: str) -> Optional[Agent]: ...
    async def list_agents(self, user_id: str, offset: int = 0, limit: int = 100) -> List[Agent]: ...
    async def delete_agent(self, id: str) -> None: ...

    # Skill operations
    async def save_skill(self, skill: Skill) -> None: ...
    async def get_skill(self, id: str) -> Optional[Skill]: ...
    async def list_skills(self, user_id: str, offset: int = 0, limit: int = 100) -> List[Skill]: ...
    async def delete_skill(self, id: str) -> None: ...
    async def save_skill_file(self, skill_id: str, filename: str, content: bytes) -> None: ...
    async def get_skill_file(self, skill_id: str, filename: str) -> Optional[bytes]: ...
    async def list_skill_files(self, skill_id: str) -> List[str]: ...
    async def delete_skill_file(self, skill_id: str, filename: str) -> None: ...

    # Feedback operations
    async def save_feedback(self, feedback: FeedbackEvent) -> None: ...
    async def get_feedback(self, id: str) -> Optional[FeedbackEvent]: ...
    async def list_feedback(self, skill_id: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[FeedbackEvent]: ...

    # Tool operations
    async def save_tool(self, tool: Tool) -> None: ...
    async def get_tool(self, id: str) -> Optional[Tool]: ...
    async def list_tools(self, user_id: str) -> List[Tool]: ...
    async def delete_tool(self, id: str) -> None: ...

    # ModelConfig operations
    async def save_model_config(self, config: ModelConfig) -> None: ...
    async def get_model_config(self, id: str) -> Optional[ModelConfig]: ...
    async def list_model_configs(self, user_id: str) -> List[ModelConfig]: ...
    async def delete_model_config(self, id: str) -> None: ...
```

- [ ] **Step 4: Create infrastructure/storage/sqlite.py**

```python
"""SQLite storage implementation."""

import json
from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship

from app.domain.agent import Agent, AgentStatus
from app.domain.skill import Skill, SkillStatus, SkillFile, FileType
from app.domain.tool import Tool, ToolType
from app.domain.model_config import ModelConfig, ModelProviderType
from app.domain.feedback import FeedbackEvent, FeedbackRating
from app.domain.user import User, UserRole
from app.infrastructure.storage.base import StorageAdapter


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


# SQLAlchemy Models
class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    role = Column(Text, default="")
    goal = Column(Text, default="")
    backstory = Column(Text, default="")
    skill_ids = Column(Text, default="[]")
    tool_ids = Column(Text, default="[]")
    model_config_id = Column(String(36), nullable=True)
    status = Column(String(20), default=AgentStatus.PENDING.value)
    user_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class SkillModel(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True)
    name = Column(String(64), nullable=False)
    description = Column(Text, default="")
    path = Column(String(500), default="")
    status = Column(String(20), default=SkillStatus.PENDING.value)
    feedback_count = Column(Integer, default=0)
    version = Column(Integer, default=1)
    metadata = Column(Text, default="{}")
    user_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class SkillFileModel(Base):
    __tablename__ = "skill_files"

    id = Column(String(36), primary_key=True)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_type = Column(String(20), default=FileType.OTHER.value)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class ToolModel(Base):
    __tablename__ = "tools"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    type = Column(String(20), default=ToolType.CUSTOM.value)
    config = Column(Text, default="{}")
    allowed_tools = Column(Text, default="[]")
    user_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class ModelConfigModel(Base):
    __tablename__ = "model_configs"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), default=ModelProviderType.OPENAI.value)
    model = Column(String(100), default="gpt-4o")
    api_key = Column(Text, nullable=True)
    base_url = Column(Text, nullable=True)
    config = Column(Text, default="{}")
    user_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class FeedbackModel(Base):
    __tablename__ = "feedbacks"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), nullable=False)
    skill_id = Column(String(36), nullable=True)
    task_id = Column(String(36), nullable=False)
    result = Column(Text, nullable=False)
    rating = Column(String(20), nullable=False)
    context = Column(Text, default="{}")
    created_at = Column(DateTime, nullable=False)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.USER.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class SQLiteStorage:
    """SQLite storage implementation."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def init_db(self):
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _to_agent(self, row: AgentModel) -> Agent:
        return Agent(
            id=row.id,
            name=row.name,
            description=row.description,
            role=row.role,
            goal=row.goal,
            backstory=row.backstory,
            skill_ids=json.loads(row.skill_ids),
            tool_ids=json.loads(row.tool_ids),
            model_config_id=row.model_config_id,
            status=AgentStatus(row.status),
            user_id=row.user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_skill(self, row: SkillModel) -> Skill:
        return Skill(
            id=row.id,
            name=row.name,
            description=row.description,
            path=row.path,
            status=SkillStatus(row.status),
            feedback_count=row.feedback_count,
            version=row.version,
            metadata=json.loads(row.metadata),
            user_id=row.user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_tool(self, row: ToolModel) -> Tool:
        return Tool(
            id=row.id,
            name=row.name,
            description=row.description,
            type=ToolType(row.type),
            config=json.loads(row.config),
            allowed_tools=json.loads(row.allowed_tools),
            user_id=row.user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_model_config(self, row: ModelConfigModel) -> ModelConfig:
        return ModelConfig(
            id=row.id,
            name=row.name,
            type=ModelProviderType(row.type),
            model=row.model,
            api_key=row.api_key,
            base_url=row.base_url,
            config=json.loads(row.config),
            user_id=row.user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_feedback(self, row: FeedbackModel) -> FeedbackEvent:
        return FeedbackEvent(
            id=row.id,
            agent_id=row.agent_id,
            skill_id=row.skill_id,
            task_id=row.task_id,
            result=row.result,
            rating=FeedbackRating(row.rating),
            context=json.loads(row.context),
            created_at=row.created_at,
        )

    def _to_user(self, row: UserModel) -> User:
        return User(
            id=row.id,
            username=row.username,
            email=row.email,
            password_hash=row.password_hash,
            role=UserRole(row.role),
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # Agent operations
    async def save_agent(self, agent: Agent) -> None:
        async with self.async_session() as session:
            model = AgentModel(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                role=agent.role,
                goal=agent.goal,
                backstory=agent.backstory,
                skill_ids=json.dumps(agent.skill_ids),
                tool_ids=json.dumps(agent.tool_ids),
                model_config_id=agent.model_config_id,
                status=agent.status,
                user_id=agent.user_id,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
            )
            session.merge(model)
            await session.commit()

    async def get_agent(self, id: str) -> Optional[Agent]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(AgentModel).where(AgentModel.id == id))
            row = result.scalar_one_or_none()
            return self._to_agent(row) if row else None

    async def list_agents(self, user_id: str, offset: int = 0, limit: int = 100) -> List[Agent]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(AgentModel)
                .where(AgentModel.user_id == user_id)
                .offset(offset)
                .limit(limit)
            )
            return [self._to_agent(row) for row in result.scalars().all()]

    async def delete_agent(self, id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(AgentModel).where(AgentModel.id == id))
            await session.commit()

    # Skill operations
    async def save_skill(self, skill: Skill) -> None:
        async with self.async_session() as session:
            model = SkillModel(
                id=skill.id,
                name=skill.name,
                description=skill.description,
                path=skill.path,
                status=skill.status,
                feedback_count=skill.feedback_count,
                version=skill.version,
                metadata=json.dumps(skill.metadata),
                user_id=skill.user_id,
                created_at=skill.created_at,
                updated_at=skill.updated_at,
            )
            session.merge(model)
            await session.commit()

    async def get_skill(self, id: str) -> Optional[Skill]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(SkillModel).where(SkillModel.id == id))
            row = result.scalar_one_or_none()
            return self._to_skill(row) if row else None

    async def list_skills(self, user_id: str, offset: int = 0, limit: int = 100) -> List[Skill]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(SkillModel)
                .where(SkillModel.user_id == user_id)
                .offset(offset)
                .limit(limit)
            )
            return [self._to_skill(row) for row in result.scalars().all()]

    async def delete_skill(self, id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(SkillModel).where(SkillModel.id == id))
            await session.commit()

    async def save_skill_file(self, skill_id: str, filename: str, content: bytes) -> None:
        from datetime import datetime
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(SkillFileModel).where(
                    SkillFileModel.skill_id == skill_id,
                    SkillFileModel.filename == filename
                )
            )
            existing = result.scalar_one_or_none()
            now = datetime.utcnow()
            
            if existing:
                existing.content = content.decode("utf-8")
                existing.updated_at = now
            else:
                from app.domain.base import EntityId
                model = SkillFileModel(
                    id=str(EntityId.generate()),
                    skill_id=skill_id,
                    filename=filename,
                    content=content.decode("utf-8"),
                    file_type=FileType.PYTHON.value if filename.endswith(".py") else FileType.MARKDOWN.value,
                    created_at=now,
                    updated_at=now,
                )
                session.add(model)
            await session.commit()

    async def get_skill_file(self, skill_id: str, filename: str) -> Optional[bytes]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(SkillFileModel).where(
                    SkillFileModel.skill_id == skill_id,
                    SkillFileModel.filename == filename
                )
            )
            row = result.scalar_one_or_none()
            return row.content.encode("utf-8") if row else None

    async def list_skill_files(self, skill_id: str) -> List[str]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(SkillFileModel.filename).where(SkillFileModel.skill_id == skill_id)
            )
            return [row[0] for row in result.all()]

    async def delete_skill_file(self, skill_id: str, filename: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(
                delete(SkillFileModel).where(
                    SkillFileModel.skill_id == skill_id,
                    SkillFileModel.filename == filename
                )
            )
            await session.commit()

    # Tool operations
    async def save_tool(self, tool: Tool) -> None:
        async with self.async_session() as session:
            model = ToolModel(
                id=tool.id,
                name=tool.name,
                description=tool.description,
                type=tool.type,
                config=json.dumps(tool.config),
                allowed_tools=json.dumps(tool.allowed_tools),
                user_id=tool.user_id,
                created_at=tool.created_at,
                updated_at=tool.updated_at,
            )
            session.merge(model)
            await session.commit()

    async def get_tool(self, id: str) -> Optional[Tool]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(ToolModel).where(ToolModel.id == id))
            row = result.scalar_one_or_none()
            return self._to_tool(row) if row else None

    async def list_tools(self, user_id: str) -> List[Tool]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ToolModel).where(ToolModel.user_id == user_id)
            )
            return [self._to_tool(row) for row in result.scalars().all()]

    async def delete_tool(self, id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(ToolModel).where(ToolModel.id == id))
            await session.commit()

    # ModelConfig operations
    async def save_model_config(self, config: ModelConfig) -> None:
        async with self.async_session() as session:
            model = ModelConfigModel(
                id=config.id,
                name=config.name,
                type=config.type,
                model=config.model,
                api_key=config.api_key,
                base_url=config.base_url,
                config=json.dumps(config.config),
                user_id=config.user_id,
                created_at=config.created_at,
                updated_at=config.updated_at,
            )
            session.merge(model)
            await session.commit()

    async def get_model_config(self, id: str) -> Optional[ModelConfig]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(ModelConfigModel).where(ModelConfigModel.id == id))
            row = result.scalar_one_or_none()
            return self._to_model_config(row) if row else None

    async def list_model_configs(self, user_id: str) -> List[ModelConfig]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ModelConfigModel).where(ModelConfigModel.user_id == user_id)
            )
            return [self._to_model_config(row) for row in result.scalars().all()]

    async def delete_model_config(self, id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(ModelConfigModel).where(ModelConfigModel.id == id))
            await session.commit()

    # Feedback operations
    async def save_feedback(self, feedback: FeedbackEvent) -> None:
        async with self.async_session() as session:
            model = FeedbackModel(
                id=feedback.id,
                agent_id=feedback.agent_id,
                skill_id=feedback.skill_id,
                task_id=feedback.task_id,
                result=feedback.result,
                rating=feedback.rating,
                context=json.dumps(feedback.context),
                created_at=feedback.created_at,
            )
            session.merge(model)
            await session.commit()

    async def get_feedback(self, id: str) -> Optional[FeedbackEvent]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(FeedbackModel).where(FeedbackModel.id == id))
            row = result.scalar_one_or_none()
            return self._to_feedback(row) if row else None

    async def list_feedback(self, skill_id: Optional[str] = None, offset: int = 0, limit: int = 100) -> List[FeedbackEvent]:
        async with self.async_session() as session:
            from sqlalchemy import select
            query = select(FeedbackModel)
            if skill_id:
                query = query.where(FeedbackModel.skill_id == skill_id)
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            return [self._to_feedback(row) for row in result.scalars().all()]
```

- [ ] **Step 5: Create infrastructure/model/__init__.py**

```python
"""Model adapters."""

from app.infrastructure.model.base import ModelAdapter

__all__ = ["ModelAdapter"]
```

- [ ] **Step 6: Create infrastructure/model/base.py**

```python
"""Model adapter interface."""

from typing import Protocol

from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult


class ModelAdapter(Protocol):
    """Model adapter protocol.

    All model provider implementations must implement this interface.
    """

    async def chat(self, messages: list[BaseMessage], **kwargs) -> ChatResult: ...

    async def complete(self, prompt: str, **kwargs) -> str: ...
```

- [ ] **Step 7: Test storage initialization**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "import asyncio; from app.infrastructure.storage.sqlite import SQLiteStorage; async def t(): s = SQLiteStorage(':memory:'); await s.init_db(); print('DB initialized'); asyncio.run(t())"`
Expected: `DB initialized`

- [ ] **Step 8: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/infrastructure/
git commit -m "feat: add storage layer abstraction and SQLite implementation"
```

---

## Task 4: Agent CRUD API

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/agents.py`
- Create: `backend/app/application/__init__.py`
- Create: `backend/app/application/agent_service.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Create api/__init__.py**

```python
"""API routes."""
```

- [ ] **Step 2: Create api/deps.py**

```python
"""Dependency injection for API routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.base import EntityId
from app.domain.user import User, UserRole
from app.infrastructure.storage.sqlite import SQLiteStorage


# Global storage instance
_storage: SQLiteStorage | None = None


async def get_storage() -> SQLiteStorage:
    """Get storage instance."""
    global _storage
    if _storage is None:
        _storage = SQLiteStorage(settings.storage.sqlite.path)
        await _storage.init_db()
    return _storage


# Type alias for dependency injection
Storage = Annotated[SQLiteStorage, Depends(get_storage)]


async def get_current_user_id() -> EntityId:
    """Get current user ID from auth context.

    TODO: Implement actual auth (JWT/OAuth2).
    For now, returns a default user ID for development.
    """
    # TODO: Extract from JWT token
    return EntityId("dev-user-id")


UserId = Annotated[EntityId, Depends(get_current_user_id)]
```

- [ ] **Step 3: Create api/agents.py**

```python
"""Agent API routes."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.api.deps import Storage, UserId
from app.application.agent_service import AgentService
from app.domain.agent import Agent, AgentStatus

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=Agent)
async def create_agent(
    agent: Agent,
    storage: Storage,
    user_id: UserId,
) -> Agent:
    """Create a new agent."""
    agent.user_id = user_id
    service = AgentService(storage)
    return await service.create(agent)


@router.get("", response_model=List[Agent])
async def list_agents(
    storage: Storage,
    user_id: UserId,
    offset: int = 0,
    limit: int = 100,
) -> List[Agent]:
    """List agents for current user."""
    service = AgentService(storage)
    return await service.list_by_user(user_id, offset, limit)


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    storage: Storage,
) -> Agent:
    """Get agent by ID."""
    service = AgentService(storage)
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=Agent)
async def update_agent(
    agent_id: str,
    data: dict,
    storage: Storage,
) -> Agent:
    """Update agent."""
    service = AgentService(storage)
    agent = await service.update(agent_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    storage: Storage,
) -> dict:
    """Delete agent."""
    service = AgentService(storage)
    deleted = await service.delete(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"ok": True}


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    task: str,
    storage: Storage,
) -> dict:
    """Run agent task.

    TODO: Implement actual agent execution via deepagents.
    """
    service = AgentService(storage)
    agent = await service.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # TODO: Integrate with deepagents
    return {"status": "todo", "message": "Agent execution not yet implemented"}


@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    storage: Storage,
) -> dict:
    """Stop running agent."""
    # TODO: Implement agent stop
    return {"status": "todo", "message": "Agent stop not yet implemented"}
```

- [ ] **Step 4: Create application/__init__.py**

```python
"""Application layer services."""
```

- [ ] **Step 5: Create application/agent_service.py**

```python
"""Agent application service."""

from typing import List, Optional

from app.domain.agent import Agent
from app.infrastructure.storage.sqlite import SQLiteStorage


class AgentService:
    """Service for agent operations."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create(self, agent: Agent) -> Agent:
        """Create a new agent."""
        await self.storage.save_agent(agent)
        return agent

    async def get(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return await self.storage.get_agent(agent_id)

    async def list_by_user(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Agent]:
        """List agents for a user."""
        return await self.storage.list_agents(user_id, offset, limit)

    async def update(self, agent_id: str, data: dict) -> Optional[Agent]:
        """Update agent fields."""
        agent = await self.storage.get_agent(agent_id)
        if not agent:
            return None

        for key, value in data.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        await self.storage.save_agent(agent)
        return agent

    async def delete(self, agent_id: str) -> bool:
        """Delete an agent."""
        agent = await self.storage.get_agent(agent_id)
        if not agent:
            return False
        await self.storage.delete_agent(agent_id)
        return True
```

- [ ] **Step 6: Create main.py**

```python
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents
from app.config import settings

app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/api")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
```

- [ ] **Step 7: Test API can start**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && timeout 5 python -c "from app.main import app; print('App created successfully')" || true`
Expected: `App created successfully`

- [ ] **Step 8: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/api/ backend/app/application/ backend/app/main.py
git commit -m "feat: add Agent CRUD API with FastAPI"
```

---

## Task 5: 补充 Feedback 领域实体

**Files:**
- Create: `backend/app/domain/feedback.py`

- [ ] **Step 1: Create domain/feedback.py**

```python
"""Feedback domain entity."""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from pydantic import Field

from app.domain.base import BaseEntity, EntityId


class FeedbackRating(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class FeedbackEvent(BaseEntity):
    """Feedback event from agent execution."""

    agent_id: str
    skill_id: Optional[str] = None
    task_id: str
    result: str
    rating: FeedbackRating
    context: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
```

- [ ] **Step 2: Update domain/__init__.py to export FeedbackEvent**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && sed -i '' 's/from app.domain.feedback import FeedbackEvent, FeedbackRating/from app.domain.feedback import FeedbackEvent, FeedbackRating/' app/domain/__init__.py && sed -i '' 's/"feedback",/"FeedbackEvent", "FeedbackRating",\n    "feedback",/' app/domain/__init__.py`
Expected: No output

- [ ] **Step 3: Verify imports**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.domain import FeedbackEvent, FeedbackRating; print('Feedback imports OK')"`
Expected: `Feedback imports OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/app/domain/feedback.py backend/app/domain/__init__.py
git commit -m "feat: add FeedbackEvent domain entity"
```

---

## Task 6: deepagents 集成占位

**Files:**
- Create: `backend/deepagents/__init__.py`
- Create: `backend/deepagents/wrapper.py`

- [ ] **Step 1: Create deepagents/__init__.py**

```python
"""deepagents integration module."""

from app.deepagents.wrapper import DeepAgentsRunner

__all__ = ["DeepAgentsRunner"]
```

- [ ] **Step 2: Create deepagents/wrapper.py (stub)**

```python
"""DeepAgents runtime wrapper.

This module provides integration with the deepagents library for
agent execution. Currently a stub - full implementation follows.
"""

from typing import Any, AsyncGenerator, Optional

from app.domain.agent import Agent
from app.domain.tool import Tool
from app.infrastructure.storage.sqlite import SQLiteStorage


class DeepAgentsRunner:
    """Wrapper for deepagents runtime.

    TODO: Full implementation
    - Load skills from storage
    - Load tools (MCP + custom)
    - Resolve model configuration
    - Create and run deep_agent
    """

    def __init__(
        self,
        agent: Agent,
        storage: SQLiteStorage,
    ):
        self.agent = agent
        self.storage = storage

    async def create(self):
        """Create deepagents runner instance."""
        # TODO: Implement
        pass

    async def run(self, task: str) -> AsyncGenerator[Any, None]:
        """Run agent task.

        Yields:
            Events from agent execution.
        """
        # TODO: Implement
        yield {"status": "todo", "message": "Not yet implemented"}

    async def stop(self):
        """Stop running agent."""
        # TODO: Implement
        pass
```

- [ ] **Step 3: Test import**

Run: `cd /Users/wilde/workplace/projects/claw-platform/backend && python -c "from app.deepagents import DeepAgentsRunner; print('DeepAgentsRunner imported')"`
Expected: `DeepAgentsRunner imported`

- [ ] **Step 4: Commit**

```bash
cd /Users/wilde/workplace/projects/claw-platform
git add backend/deepagents/
git commit -m "feat: add deepagents integration stub"
```

---

## Self-Review

- [ ] **Spec coverage check**: All Phase 1 items from design doc covered
  - [x] 项目脚手架 (Task 1)
  - [x] 配置系统 (Task 1)
  - [x] 领域实体 (Task 2)
  - [x] 存储层抽象 + SQLite 实现 (Task 3)
  - [x] Agent CRUD API (Task 4)
  - [x] Feedback 实体 (Task 5)
  - [x] deepagents 集成占位 (Task 6)

- [ ] **Placeholder scan**: No TBD/TODO in implementation steps (only in comments for future work)

- [ ] **Type consistency**: Entity types match across tasks
  - `Agent.user_id: EntityId` used consistently
  - `StorageAdapter` interface methods match SQLite implementation
  - API response models use domain entities

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-22-claw-platform-phase1.md`**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
