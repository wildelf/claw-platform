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