"""SQLite storage implementation."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, create_engine

from app.domain.base import EntityId
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
            metadata=json.loads(row.skill_metadata),
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
                skill_metadata=json.dumps(skill.metadata),
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
