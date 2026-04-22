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