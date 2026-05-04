"""Web search tool using MiniMax API or fallback."""

import logging
import re
from typing import Any, Literal

import httpx
from langchain_core.tools import BaseTool
from pydantic import Field

from app.domain.model_config import ModelConfig

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for web search via MiniMax or compatible API.

    Dynamically created at agent runtime when configured.
    NOT persisted to the database.
    """

    name: Literal["web_search"] = "web_search"
    description: str = (
        "Searches the web for current information. "
        "Use this when you need to find recent news, facts, or information "
        "that may not be in your training data. "
        "Arguments: {query: str}"
    )

    def __init__(self, model_config: ModelConfig = None, **kwargs):
        super().__init__(**kwargs)
        self._model_config = model_config

    async def _ainvoke(self, tool_input: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Execute web search asynchronously."""
        logger.info("WebSearchTool invoked with input: %s", tool_input)
        query = tool_input.get("query", "")
        if not query:
            return {"error": "query is required"}

        # Try MiniMax web search API first
        if self._model_config and self._model_config.api_key:
            result = await self._search_minimax(query)
            if result:
                return result

        # Fallback to a simple web search
        result = await self._search_fallback(query)
        return result

    async def _search_minimax(self, query: str) -> dict[str, Any] | None:
        """Try MiniMax API for web search."""
        if not self._model_config:
            return None

        api_key = self._model_config.api_key
        base_url = self._model_config.base_url

        if not api_key or not base_url:
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model_config.model,
            "query": query,
        }

        try:
            async with httpx.AsyncClient() as client:
                url = f"{base_url.rstrip('/')}/web_search"
                logger.info("WebSearchTool making request to: %s", url)
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                logger.info("WebSearchTool response status: %s", response.status_code)
                if response.status_code == 404:
                    return None  # API not available, try fallback
                response.raise_for_status()
                result = response.json()
                logger.info("WebSearchTool result: %s", str(result)[:500])
                return self._parse_web_search_result(result)
        except httpx.HTTPError as e:
            logger.error("WebSearchTool HTTP error: %s", e)
            return None

    def _parse_web_search_result(self, result: dict) -> dict[str, Any]:
        """Parse MiniMax web search response."""
        data = result.get("data", {})
        if isinstance(data, dict):
            results = data.get("results", data.get("web_pages", []))
        else:
            results = []
        return {
            "results": results,
            "answer": data.get("answer"),
        }

    async def _search_fallback(self, query: str) -> dict[str, Any]:
        """Fallback search using DuckDuckGo HTML."""
        try:
            async with httpx.AsyncClient() as client:
                url = "https://duckduckgo.com/html/"
                params = {"q": query}
                response = await client.get(
                    url,
                    params=params,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=15.0,
                )
                response.raise_for_status()
                html = response.text

                # Simple HTML parsing to extract titles and snippets
                results = []
                # Match search result patterns
                pattern = r'<a class="result__a" href="([^"]+)">([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]+)</a>'
                matches = re.findall(pattern, html, re.DOTALL)
                for url, title, snippet in matches[:5]:
                    results.append({
                        "title": title.strip(),
                        "url": url,
                        "snippet": snippet.strip().replace("<b>", "").replace("</b>", ""),
                    })

                return {
                    "results": results,
                    "answer": None,
                }
        except Exception as e:
            logger.error("WebSearchTool fallback search failed: %s", e)
            return {"error": f"Web search failed: {e}", "results": []}

    def _run(self, tool_input: str | dict[str, Any], **kwargs) -> dict[str, Any]:
        """Sync invoke."""
        import asyncio
        if isinstance(tool_input, str):
            import json
            try:
                tool_input = json.loads(tool_input)
            except json.JSONDecodeError:
                tool_input = {"query": tool_input}
        return asyncio.run(self._ainvoke(tool_input, **kwargs))

