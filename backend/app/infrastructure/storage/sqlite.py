"""SQLite storage implementation."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, create_engine, Index

from app.domain.base import EntityId
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship

from app.domain.agent import Agent, AgentStatus
from app.domain.scheduled_task import ScheduledTask, ScheduleType, ScheduledTaskStatus
from app.domain.skill import Skill, SkillStatus, SkillFile, FileType
from app.domain.tool import Tool, ToolType
from app.domain.model_config import ModelConfig, ModelModality, ModelProviderType
from app.domain.feedback import FeedbackEvent, FeedbackRating
from app.domain.user import User, UserRole
from app.domain.log import LogEntry, LogActionType
from app.domain.session import Session
from app.domain.conversation_memory import ConversationMemory
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
    enabled_builtin_tools = Column(Text, default="[]")
    model_config_id = Column(String(36), nullable=True)
    text_model_config_id = Column(String(36), nullable=True)
    image_model_config_id = Column(String(36), nullable=True)
    video_model_config_id = Column(String(36), nullable=True)
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
    skill_metadata = Column(Text, default="{}")
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
    # MCP-specific fields
    server_name = Column(String(100), nullable=True)
    mcp_config = Column(Text, nullable=True, comment="JSON-encoded MCPConfig")
    args = Column(Text, default="[]", comment="JSON-encoded list of ToolArg")


class ModelConfigModel(Base):
    __tablename__ = "model_configs"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), default=ModelProviderType.OPENAI.value)
    model = Column(String(100), default="gpt-4o")
    api_key = Column(Text, nullable=True)
    base_url = Column(Text, nullable=True)
    config = Column(Text, default="{}")
    modality = Column(String(20), default="text")
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


class ScheduledTaskModel(Base):
    __tablename__ = "scheduled_tasks"
    __table_args__ = (
        Index("ix_scheduled_tasks_user_id", "user_id"),
    )

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    agent_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=False)
    schedule_type = Column(String(20), nullable=False)
    cron_expression = Column(String(100), nullable=True)
    interval_seconds = Column(Integer, nullable=True)
    run_at = Column(DateTime, nullable=True)
    task_input = Column(Text, default="")
    model_config_id = Column(String(36), nullable=True)
    status = Column(String(20), default="active")
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class LogModel(Base):
    __tablename__ = "logs"
    __table_args__ = (
        Index("ix_logs_agent_id", "agent_id"),
        Index("ix_logs_session_id", "session_id"),
        Index("ix_logs_timestamp", "timestamp"),
    )

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), nullable=False)
    session_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    action_type = Column(String(30), nullable=False)
    tool_name = Column(String(100), nullable=True)
    input_json = Column(Text, nullable=True)
    output_json = Column(Text, nullable=True)
    decision_context = Column(String(100), nullable=True)
    error = Column(Text, nullable=True)
    extra = Column(Text, default="{}")
    created_at = Column(DateTime, nullable=False)


class SessionModel(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_updated_at", "updated_at"),
    )

    id = Column(String(36), primary_key=True)
    name = Column(String(255), default="")
    agent_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    message_count = Column(Integer, default=0)


class ConversationMemoryModel(Base):
    __tablename__ = "conversation_memories"
    __table_args__ = (
        Index("ix_conversation_memories_agent_session_created", "agent_id", "session_id", "created_at"),
    )

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), nullable=False)
    session_id = Column(String(36), nullable=False)
    user_input = Column(Text, nullable=False)
    agent_output = Column(Text, nullable=False)
    summary = Column(Text, default="")
    created_at = Column(DateTime, nullable=False)


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

    async def close(self):
        """Close the database connection."""
        await self.engine.dispose()

    def _to_agent(self, row: AgentModel) -> Agent:
        # Backward compat: model_config_id → text_model_config_id
        text_id = row.text_model_config_id or row.model_config_id
        return Agent(
            id=EntityId(row.id),
            name=row.name,
            description=row.description,
            role=row.role,
            goal=row.goal,
            backstory=row.backstory,
            skill_ids=[EntityId(sid) for sid in json.loads(row.skill_ids)],
            tool_ids=[EntityId(tid) for tid in json.loads(row.tool_ids)],
            enabled_builtin_tools=json.loads(row.enabled_builtin_tools or "[]"),
            text_model_config_id=EntityId(text_id) if text_id else None,
            image_model_config_id=EntityId(row.image_model_config_id) if row.image_model_config_id else None,
            video_model_config_id=EntityId(row.video_model_config_id) if row.video_model_config_id else None,
            status=AgentStatus(row.status),
            user_id=EntityId(row.user_id),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_skill(self, row: SkillModel) -> Skill:
        return Skill(
            id=EntityId(row.id),
            name=row.name,
            description=row.description,
            path=row.path,
            status=SkillStatus(row.status),
            feedback_count=row.feedback_count,
            version=row.version,
            metadata=json.loads(row.skill_metadata),
            user_id=EntityId(row.user_id),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_tool(self, row: ToolModel) -> Tool:
        from app.domain.tool import ToolArg, MCPAuthConfig, MCPConfig
        mcp_config = None
        if row.mcp_config:
            cfg_dict = json.loads(row.mcp_config)
            auth_dict = cfg_dict.get("auth", {})
            auth = MCPAuthConfig(type=auth_dict.get("type", "none"), token=auth_dict.get("token"), header_name=auth_dict.get("header_name", "X-API-Key"))
            mcp_config = MCPConfig(
                endpoint=cfg_dict.get("endpoint", ""),
                method=cfg_dict.get("method", "POST"),
                auth=auth,
                headers=cfg_dict.get("headers", {}),
                request_template=cfg_dict.get("request_template"),
                response_template=cfg_dict.get("response_template"),
            )
        args = []
        if row.args:
            for arg_dict in json.loads(row.args):
                args.append(ToolArg(name=arg_dict["name"], position=arg_dict.get("position", "body"), required=arg_dict.get("required", False), arg_type=arg_dict.get("type", "string")))
        return Tool(
            id=EntityId(row.id),
            name=row.name,
            description=row.description,
            type=ToolType(row.type),
            config=json.loads(row.config),
            allowed_tools=json.loads(row.allowed_tools),
            user_id=EntityId(row.user_id),
            created_at=row.created_at,
            updated_at=row.updated_at,
            server_name=row.server_name,
            mcp_config=mcp_config,
            args=args,
        )

    def _to_model_config(self, row: ModelConfigModel) -> ModelConfig:
        return ModelConfig(
            id=EntityId(row.id),
            name=row.name,
            type=ModelProviderType(row.type),
            model=row.model,
            modality=ModelModality(row.modality or "text"),
            api_key=row.api_key,
            base_url=row.base_url,
            config=json.loads(row.config),
            user_id=EntityId(row.user_id),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_feedback(self, row: FeedbackModel) -> FeedbackEvent:
        return FeedbackEvent(
            id=EntityId(row.id),
            agent_id=EntityId(row.agent_id),
            skill_id=EntityId(row.skill_id) if row.skill_id else None,
            task_id=EntityId(row.task_id),
            result=row.result,
            rating=FeedbackRating(row.rating),
            context=json.loads(row.context),
            created_at=row.created_at,
        )

    def _to_user(self, row: UserModel) -> User:
        return User(
            id=EntityId(row.id),
            username=row.username,
            email=row.email,
            password_hash=row.password_hash,
            role=UserRole(row.role),
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _to_scheduled_task(self, row: ScheduledTaskModel) -> ScheduledTask:
        return ScheduledTask(
            id=EntityId(row.id),
            name=row.name,
            description=row.description or "",
            agent_id=EntityId(row.agent_id),
            user_id=EntityId(row.user_id),
            schedule_type=ScheduleType(row.schedule_type),
            cron_expression=row.cron_expression,
            interval_seconds=row.interval_seconds,
            run_at=row.run_at,
            task_input=row.task_input or "",
            model_config_id=EntityId(row.model_config_id) if row.model_config_id else None,
            status=ScheduledTaskStatus(row.status),
            last_run_at=row.last_run_at,
            next_run_at=row.next_run_at,
            run_count=row.run_count or 0,
            last_error=row.last_error,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # Agent operations
    async def save_agent(self, agent: Agent) -> None:
        async with self.async_session() as session:
            from sqlalchemy import select

            # Check if agent already exists
            result = await session.execute(
                select(AgentModel).where(AgentModel.id == agent.id)
            )
            existing = result.scalar_one_or_none()

            model = AgentModel(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                role=agent.role,
                goal=agent.goal,
                backstory=agent.backstory,
                skill_ids=json.dumps(agent.skill_ids),
                tool_ids=json.dumps(agent.tool_ids),
                enabled_builtin_tools=json.dumps(agent.enabled_builtin_tools),
                text_model_config_id=agent.text_model_config_id,
                image_model_config_id=agent.image_model_config_id,
                video_model_config_id=agent.video_model_config_id,
                status=agent.status,
                user_id=agent.user_id,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
            )

            if existing:
                # Update existing record
                for key in ['name', 'description', 'role', 'goal', 'backstory',
                           'skill_ids', 'tool_ids', 'enabled_builtin_tools',
                           'text_model_config_id', 'image_model_config_id', 'video_model_config_id',
                           'status', 'updated_at']:
                    setattr(existing, key, getattr(model, key))
            else:
                # Insert new record
                session.add(model)
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
                skill_metadata=json.dumps(skill.metadata),
                user_id=skill.user_id,
                created_at=skill.created_at,
                updated_at=skill.updated_at,
            )
            session.add(model)
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
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(SkillFileModel).where(
                    SkillFileModel.skill_id == skill_id,
                    SkillFileModel.filename == filename
                )
            )
            existing = result.scalar_one_or_none()
            now = datetime.now(timezone.utc)

            if existing:
                existing.content = content.decode("utf-8")
                existing.updated_at = now
            else:
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
            from sqlalchemy import select
            # Check if tool already exists
            result = await session.execute(select(ToolModel).where(ToolModel.id == tool.id))
            existing = result.scalar_one_or_none()

            mcp_config_json = None
            if tool.mcp_config:
                mcp_config_json = json.dumps({
                    "endpoint": tool.mcp_config.endpoint,
                    "method": tool.mcp_config.method,
                    "auth": {
                        "type": tool.mcp_config.auth.type,
                        "token": tool.mcp_config.auth.token,
                        "header_name": tool.mcp_config.auth.header_name,
                    },
                    "headers": tool.mcp_config.headers,
                    "request_template": tool.mcp_config.request_template,
                    "response_template": tool.mcp_config.response_template,
                }, ensure_ascii=False)

            args_json = json.dumps([
                {"name": a.name, "position": a.position, "required": a.required, "type": a.arg_type}
                for a in tool.args
            ], ensure_ascii=False)

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
                server_name=tool.server_name,
                mcp_config=mcp_config_json,
                args=args_json,
            )

            if existing:
                for key in ['name', 'description', 'type', 'config', 'allowed_tools', 'updated_at', 'server_name', 'mcp_config', 'args']:
                    setattr(existing, key, getattr(model, key))
            else:
                session.add(model)
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
            from sqlalchemy import select

            # Check if model config already exists
            result = await session.execute(
                select(ModelConfigModel).where(ModelConfigModel.id == config.id)
            )
            existing = result.scalar_one_or_none()

            model = ModelConfigModel(
                id=config.id,
                name=config.name,
                type=config.type,
                model=config.model,
                modality=config.modality,
                api_key=config.api_key,
                base_url=config.base_url,
                config=json.dumps(config.config),
                user_id=config.user_id,
                created_at=config.created_at,
                updated_at=config.updated_at,
            )

            if existing:
                # Update existing record
                for key in ['name', 'type', 'model', 'modality', 'api_key', 'base_url', 'config', 'updated_at']:
                    setattr(existing, key, getattr(model, key))
            else:
                # Insert new record
                session.add(model)
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
            session.add(model)
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

    # User operations
    async def save_user(self, user: User) -> None:
        async with self.async_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(UserModel).where(UserModel.id == user.id)
            )
            existing = result.scalar_one_or_none()

            model = UserModel(
                id=user.id,
                username=user.username,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

            if existing:
                for key in ['username', 'email', 'password_hash', 'role', 'is_active', 'updated_at']:
                    setattr(existing, key, getattr(model, key))
            else:
                session.add(model)
            await session.commit()

    async def get_user(self, id: str) -> Optional[User]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(UserModel).where(UserModel.id == id))
            row = result.scalar_one_or_none()
            return self._to_user(row) if row else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(UserModel).where(UserModel.username == username))
            row = result.scalar_one_or_none()
            return self._to_user(row) if row else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(UserModel).where(UserModel.email == email))
            row = result.scalar_one_or_none()
            return self._to_user(row) if row else None

    async def delete_user(self, id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(UserModel).where(UserModel.id == id))
            await session.commit()

    # ScheduledTask operations
    async def save_scheduled_task(self, task: ScheduledTask) -> None:
        async with self.async_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(ScheduledTaskModel).where(ScheduledTaskModel.id == task.id)
            )
            existing = result.scalar_one_or_none()

            model = ScheduledTaskModel(
                id=task.id,
                name=task.name,
                description=task.description,
                agent_id=task.agent_id,
                user_id=task.user_id,
                schedule_type=task.schedule_type,
                cron_expression=task.cron_expression,
                interval_seconds=task.interval_seconds,
                run_at=task.run_at,
                task_input=task.task_input,
                model_config_id=task.model_config_id,
                status=task.status,
                last_run_at=task.last_run_at,
                next_run_at=task.next_run_at,
                run_count=task.run_count,
                last_error=task.last_error,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )

            if existing:
                for key in ['name', 'description', 'agent_id', 'schedule_type',
                           'cron_expression', 'interval_seconds', 'run_at',
                           'task_input', 'model_config_id', 'status',
                           'last_run_at', 'next_run_at', 'run_count', 'last_error', 'updated_at']:
                    setattr(existing, key, getattr(model, key))
            else:
                session.add(model)
            await session.commit()

    async def get_scheduled_task(self, id: str) -> Optional[ScheduledTask]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(ScheduledTaskModel).where(ScheduledTaskModel.id == id))
            row = result.scalar_one_or_none()
            return self._to_scheduled_task(row) if row else None

    async def list_scheduled_tasks(self, user_id: EntityId, offset: int = 0, limit: int = 100) -> List[ScheduledTask]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ScheduledTaskModel)
                .where(ScheduledTaskModel.user_id == user_id)
                .order_by(ScheduledTaskModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return [self._to_scheduled_task(row) for row in result.scalars().all()]

    async def delete_scheduled_task(self, id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(ScheduledTaskModel).where(ScheduledTaskModel.id == id))
            await session.commit()

    # Log operations
    def _to_log(self, row: LogModel) -> LogEntry:
        return LogEntry(
            id=EntityId(row.id),
            agent_id=EntityId(row.agent_id),
            session_id=row.session_id,
            timestamp=row.timestamp,
            action_type=LogActionType(row.action_type),
            tool_name=row.tool_name,
            input_json=row.input_json,
            output_json=row.output_json,
            decision_context=row.decision_context,
            error=row.error,
            extra=json.loads(row.extra) if row.extra else {},
            created_at=row.created_at,
        )

    async def save_log(self, entry: LogEntry) -> None:
        async with self.async_session() as session:
            model = LogModel(
                id=entry.id,
                agent_id=entry.agent_id,
                session_id=entry.session_id,
                timestamp=entry.timestamp,
                action_type=entry.action_type,
                tool_name=entry.tool_name,
                input_json=entry.input_json,
                output_json=entry.output_json,
                decision_context=entry.decision_context,
                error=entry.error,
                extra=json.dumps(entry.extra),
                created_at=datetime.now(timezone.utc),
            )
            session.add(model)
            await session.commit()

    async def query_logs(
        self,
        agent_id: str | None = None,
        session_id: str | None = None,
        action_type: str | None = None,
        tool_name: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[LogEntry]:
        async with self.async_session() as session:
            from sqlalchemy import select
            query = select(LogModel)
            if agent_id:
                query = query.where(LogModel.agent_id == agent_id)
            if session_id:
                query = query.where(LogModel.session_id == session_id)
            if action_type:
                query = query.where(LogModel.action_type == action_type)
            if tool_name:
                query = query.where(LogModel.tool_name == tool_name)
            query = query.order_by(LogModel.timestamp.desc()).offset(offset).limit(limit)
            result = await session.execute(query)
            return [self._to_log(row) for row in result.scalars().all()]

    # Session operations
    def _to_session(self, row: SessionModel) -> Session:
        return Session(
            id=EntityId(row.id),
            name=row.name,
            agent_id=EntityId(row.agent_id),
            created_at=row.created_at,
            updated_at=row.updated_at,
            message_count=row.message_count,
        )

    async def save_session(self, session: Session) -> None:
        async with self.async_session() as sess:
            from sqlalchemy import select
            result = await sess.execute(
                select(SessionModel).where(SessionModel.id == session.id)
            )
            existing = result.scalar_one_or_none()

            model = SessionModel(
                id=session.id,
                name=session.name,
                agent_id=session.agent_id,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=session.message_count,
            )

            if existing:
                for key in ['name', 'updated_at', 'message_count']:
                    setattr(existing, key, getattr(model, key))
            else:
                sess.add(model)
            await sess.commit()

    async def get_session(self, id: str) -> Optional[Session]:
        async with self.async_session() as sess:
            from sqlalchemy import select
            result = await sess.execute(select(SessionModel).where(SessionModel.id == id))
            row = result.scalar_one_or_none()
            return self._to_session(row) if row else None

    async def list_sessions(self, offset: int = 0, limit: int = 100) -> List[Session]:
        async with self.async_session() as sess:
            from sqlalchemy import select
            result = await sess.execute(
                select(SessionModel)
                .order_by(SessionModel.updated_at.desc())
                .offset(offset)
                .limit(limit)
            )
            return [self._to_session(row) for row in result.scalars().all()]

    async def delete_session(self, id: str) -> None:
        async with self.async_session() as sess:
            from sqlalchemy import delete
            await sess.execute(delete(SessionModel).where(SessionModel.id == id))
            await sess.commit()

    # ConversationMemory operations
    def _to_conversation_memory(self, row: ConversationMemoryModel) -> ConversationMemory:
        return ConversationMemory(
            id=EntityId(row.id),
            agent_id=EntityId(row.agent_id),
            session_id=row.session_id,
            user_input=row.user_input,
            agent_output=row.agent_output,
            summary=row.summary,
            created_at=row.created_at,
        )

    async def save_conversation_memory(self, memory: ConversationMemory) -> None:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ConversationMemoryModel).where(ConversationMemoryModel.id == memory.id)
            )
            existing = result.scalar_one_or_none()

            model = ConversationMemoryModel(
                id=memory.id,
                agent_id=memory.agent_id,
                session_id=memory.session_id,
                user_input=memory.user_input,
                agent_output=memory.agent_output,
                summary=memory.summary,
                created_at=memory.created_at,
            )

            if existing:
                for key in ['user_input', 'agent_output', 'summary', 'created_at']:
                    setattr(existing, key, getattr(model, key))
            else:
                session.add(model)
            await session.commit()

    async def update_conversation_memory_summary(self, id: str, summary: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import update
            await session.execute(
                update(ConversationMemoryModel).where(ConversationMemoryModel.id == id).values(summary=summary)
            )
            await session.commit()

    async def get_conversation_memories(self, agent_id: str, session_id: str, limit: int = 10) -> List[ConversationMemory]:
        async with self.async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ConversationMemoryModel)
                .where(ConversationMemoryModel.agent_id == agent_id)
                .where(ConversationMemoryModel.session_id == session_id)
                .order_by(ConversationMemoryModel.created_at.desc())
                .limit(limit)
            )
            return [self._to_conversation_memory(row) for row in result.scalars().all()]

    async def delete_conversation_memory(self, id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(ConversationMemoryModel).where(ConversationMemoryModel.id == id))
            await session.commit()

    async def delete_conversation_memories_by_session(self, agent_id: str, session_id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(
                delete(ConversationMemoryModel).where(
                    ConversationMemoryModel.agent_id == agent_id,
                    ConversationMemoryModel.session_id == session_id
                )
            )
            await session.commit()

    async def delete_conversation_memories_by_agent(self, agent_id: str) -> None:
        async with self.async_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(ConversationMemoryModel).where(ConversationMemoryModel.agent_id == agent_id))
            await session.commit()
