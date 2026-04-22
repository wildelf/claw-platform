"""Anthropic model adapter."""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

from app.domain.model_config import ModelConfig
from app.infrastructure.model.base import ModelAdapter


class AnthropicAdapter(ModelAdapter):
    """Adapter for Anthropic models."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._llm: ChatAnthropic | None = None

    @property
    def llm(self) -> ChatAnthropic:
        if self._llm is None:
            self._llm = ChatAnthropic(
                model=self.config.model,
                anthropic_api_key=self.config.api_key,
                base_url=self.config.base_url,
                **self.config.config,
            )
        return self._llm

    async def chat(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        """Chat completion with Anthropic."""
        return await self.llm.ainvoke(messages, **kwargs)

    async def complete(self, prompt: str, **kwargs) -> str:
        """Text completion with Anthropic (uses messages API)."""
        result = await self.llm.ainvoke([{"role": "user", "content": prompt}], **kwargs)
        return result.content if hasattr(result, "content") else str(result)