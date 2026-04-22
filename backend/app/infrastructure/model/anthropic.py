"""Anthropic model adapter."""

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

from app.domain.model_config import ModelConfig
from app.infrastructure.model.base import ModelAdapter


class AnthropicAdapter(ModelAdapter):
    """Adapter for Anthropic models."""

    def __init__(self, config: ModelConfig):
        self.config = config

    async def chat(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        """Chat completion with Anthropic."""
        llm = ChatAnthropic(
            model=self.config.model,
            anthropic_api_key=self.config.api_key,
            base_url=self.config.base_url,
            **self.config.config,
        )
        return await llm.ainvoke(messages, **kwargs)

    async def complete(self, prompt: str, **kwargs) -> str:
        """Text completion with Anthropic (uses messages API)."""
        llm = ChatAnthropic(
            model=self.config.model,
            anthropic_api_key=self.config.api_key,
            base_url=self.config.base_url,
            **self.config.config,
        )
        result = await llm.ainvoke([{"role": "user", "content": prompt}], **kwargs)
        return result.content if hasattr(result, "content") else str(result)