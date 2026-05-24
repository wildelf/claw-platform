"""Configuration loader for Claw Platform."""

from pathlib import Path

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


class EvolutionConfig(BaseModel):
    generation_threshold: int = 3
    auto_evolve: bool = False
    max_versions: int = 10


class SkillCreatorConfig(BaseModel):
    path: str = ""


class OpenSandboxConfig(BaseModel):
    enabled: bool = False
    base_url: str = "http://127.0.0.1:8080"
    default_image: str = "python:3.12-slim"
    timeout: int = 300
    memory_limit: str = "512Mi"


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None


class WebSearchConfig(BaseModel):
    enabled: bool = False
    provider: str = "auto"  # auto, minimax, duckduckgo
    api_key: str | None = None
    base_url: str = "https://api.minimaxi.com"
    mcp_command: str = "uvx"
    mcp_args: list[str] = ["minimax-coding-plan-mcp"]


class WorkerConfig(BaseModel):
    heartbeat_interval: int = 30
    stale_threshold: int = 60
    max_retries: int = 3


class Settings(BaseSettings):
    model_config = {"extra": "ignore"}

    app: AppConfig = AppConfig()
    storage: StorageConfig = StorageConfig()
    auth: AuthConfig
    models: ModelsConfig
    evolution: EvolutionConfig = EvolutionConfig()
    skill_creator: SkillCreatorConfig = SkillCreatorConfig()
    opensandbox: OpenSandboxConfig = OpenSandboxConfig()
    redis: RedisConfig = RedisConfig()
    web_search: WebSearchConfig = WebSearchConfig()
    worker: WorkerConfig = WorkerConfig()
    identity_root: str = "~/.claw/employees"
    memory_storage_path: str = "~/.claw/memories"
    skills_cache_path: str = "~/.claw/skills"
    permission_rules_root: str = "~/.claw/permission-rules"

    @classmethod
    def from_yaml(cls, path: Path | str) -> "Settings":
        """Load settings from YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse YAML config file: {e}") from e

        return cls(**data)


def get_settings() -> Settings:
    """Get application settings."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    return Settings.from_yaml(config_path)


settings = get_settings()