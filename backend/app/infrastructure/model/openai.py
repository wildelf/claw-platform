"""OpenAI model adapter."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

from app.domain.model_config import ModelConfig
from app.infrastructure.model.base import ModelAdapter


class OpenAIAdapter(ModelAdapter):
    """Adapter for OpenAI models."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._llm: ChatOpenAI | None = None

    @property
    def llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                **self.config.config,
            )
        return self._llm

    async def chat(self, messages: list[BaseMessage], **kwargs) -> ChatResult:
        """Chat completion with OpenAI."""
        return await self.llm.ainvoke(messages, **kwargs)

    async def complete(self, prompt: str, **kwargs) -> str:
        """Text completion with OpenAI."""
        result = await self.llm.ainvoke(prompt, **kwargs)
        return result.content if hasattr(result, "content") else str(result)