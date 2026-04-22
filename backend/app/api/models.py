"""Model Config API routes."""

from typing import List, Optional

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
    api_key: Optional[str] = None
    base_url: Optional[str] = None
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