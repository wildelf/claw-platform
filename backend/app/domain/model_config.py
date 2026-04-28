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


class ModelModality(str, Enum):
    TEXT = "text"
    IMAGE_TO_TEXT = "image-to-text"
    TEXT_TO_IMAGE = "text-to-image"
    IMAGE_TO_IMAGE = "image-to-image"
    TEXT_TO_VIDEO = "text-to-video"
    VIDEO = "video"


class ModelConfig(BaseEntity):
    """Model configuration entity."""

    name: str = Field(max_length=100)
    type: ModelProviderType = ModelProviderType.OPENAI
    model: str = Field(max_length=100, default="gpt-4o")
    modality: ModelModality = ModelModality.TEXT
    api_key: str | None = None
    base_url: str | None = None
    config: Dict[str, Any] = Field(default_factory=dict)
    user_id: EntityId

    class Config:
        use_enum_values = True