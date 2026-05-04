"""Image generation tool using configured image model."""

import logging
from typing import Any, Literal

import httpx
from langchain_core.tools import BaseTool

from app.domain.model_config import ModelConfig

logger = logging.getLogger(__name__)


class ImageGenerationTool(BaseTool):
    """Tool for generating images via a configured image model.

    Dynamically created at agent runtime when image_model_config_id is set.
    NOT persisted to the database.
    """

    name: Literal["generate_image"] = "generate_image"
    description: str = (
        "Generates images from text descriptions. "
        "Use this when the user asks to create, generate, draw, or paint an image. "
        "Arguments: {prompt: str}"
    )

    def __init__(self, model_config: ModelConfig, **kwargs):
        super().__init__(**kwargs)
        self._model_config = model_config

    async def _ainvoke(self, tool_input: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Execute image generation asynchronously."""
        logger.info("ImageGenerationTool invoked with input: %s", tool_input)
        prompt = tool_input.get("prompt", "")
        if not prompt:
            return {"error": "prompt is required"}

        model = self._model_config.model
        api_key = self._model_config.api_key
        base_url = self._model_config.base_url

        if not api_key:
            return {"error": "image_model api_key is not configured"}
        if not base_url:
            return {"error": "image_model base_url is not configured"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": self._model_config.config.get("size", "1024x1024"),
            "quality": self._model_config.config.get("quality", "standard"),
        }

        try:
            async with httpx.AsyncClient() as client:
                url = f"{base_url.rstrip('/')}/image_generation"
                logger.info("ImageGenerationTool making request to: %s", url)
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=60.0,
                )
                logger.info("ImageGenerationTool response status: %s", response.status_code)
                logger.info("ImageGenerationTool response body: %s", response.text[:500])
                response.raise_for_status()
        except httpx.TimeoutException:
            logger.error("ImageGenerationTool timeout")
            return {"error": "Image generation timed out"}
        except httpx.HTTPError as e:
            logger.error("ImageGenerationTool HTTP error: %s", e)
            return {"error": f"Image generation request failed: {e}"}

        try:
            result = response.json()
        except Exception:
            logger.error("ImageGenerationTool invalid JSON response")
            return {"error": "Invalid response from image model"}

        logger.info("ImageGenerationTool result: %s", result)
        # Handle different API response formats
        data = result.get("data", {})
        if isinstance(data, dict):
            # MiniMax format: data.image_urls [...]
            image_url = data.get("image_urls", [None])[0]
        else:
            # OpenAI format: data[0].url
            image_url = data[0].get("url") if data else None

        if not image_url:
            return {"error": f"No image_url in response: {result}"}

        revised_prompt = None
        if isinstance(data, dict):
            revised_prompt = data.get("revised_prompt")
        else:
            revised_prompt = data[0].get("revised_prompt") if data else None

        return {
            "image_url": image_url,
            "revised_prompt": revised_prompt,
        }

    def _run(self, tool_input: str | dict[str, Any], **kwargs) -> dict[str, Any]:
        """Sync invoke."""
        import asyncio
        if isinstance(tool_input, str):
            import json
            try:
                tool_input = json.loads(tool_input)
            except json.JSONDecodeError:
                tool_input = {"prompt": tool_input}
        return asyncio.run(self._ainvoke(tool_input, **kwargs))