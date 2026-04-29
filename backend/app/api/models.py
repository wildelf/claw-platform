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


class TestConnectionRequest(BaseModel):
    type: ModelProviderType = ModelProviderType.OPENAI
    model: str = Field(max_length=100, default="gpt-4o")
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    modality: Optional[str] = "text"


@router.post("/test-connection")
async def test_connection(
    request: TestConnectionRequest,
) -> dict:
    """Test model connection with given configuration."""
    import httpx

    if not request.base_url:
        return {
            "ok": False,
            "message": "Base URL is required for testing connection"
        }

    # Image generation models (image-to-image, text-to-image): use images API
    if request.modality in ("image-to-image", "text-to-image"):
        try:
            headers = {
                "Authorization": f"Bearer {request.api_key}",
                "Content-Type": "application/json",
            }
            payload: dict = {
                "model": request.model,
                "prompt": "test prompt",
            }
            if request.modality == "image-to-image":
                # image-to-image needs subject_reference but we use a tiny valid base64
                # 1x1 red pixel PNG as minimal reference image
                payload["subject_reference"] = [
                    {
                        "type": "character",
                        "image_file": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg==",
                    }
                ]
                payload["aspect_ratio"] = "1:1"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{request.base_url.rstrip('/')}/image_generation",
                    json=payload,
                    headers=headers,
                    timeout=15.0,
                )
            if response.status_code == 200:
                return {
                    "ok": True,
                    "message": f"Connection successful for {request.model} image generation"
                }
            return {
                "ok": False,
                "message": f"Connection failed: HTTP {response.status_code} - {response.text[:100]}"
            }
        except Exception as e:
            return {
                "ok": False,
                "message": f"Connection failed: {str(e)[:100]}"
            }

    # Text / image-to-text models: use ChatOpenAI /chat/completions
    from langchain_openai import ChatOpenAI

    try:
        llm = ChatOpenAI(
            model=request.model,
            api_key=request.api_key or "dummy",
            base_url=request.base_url,
            timeout=15,
        )
        llm.invoke("Hi", config={"max_tokens": 1})
        return {
            "ok": True,
            "message": f"Connection successful for {request.type.value} {request.model}"
        }
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Authentication" in error_msg:
            return {
                "ok": False,
                "message": "Authentication failed. Please check your API key."
            }
        elif "403" in error_msg:
            return {
                "ok": False,
                "message": "Access forbidden. Please check your API key permissions."
            }
        elif "404" in error_msg:
            return {
                "ok": False,
                "message": "Model not found. Please check the model name."
            }
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            return {
                "ok": False,
                "message": "Connection failed. Please check the Base URL."
            }
        else:
            return {
                "ok": False,
                "message": f"Connection failed: {error_msg[:100]}"
            }