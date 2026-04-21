"""Model adapter interface."""

from typing import Protocol

from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult


class ModelAdapter(Protocol):
    """Model adapter protocol.

    All model provider implementations must implement this interface.
    """

    async def chat(self, messages: list[BaseMessage], **kwargs) -> ChatResult: ...

    async def complete(self, prompt: str, **kwargs) -> str: ...
