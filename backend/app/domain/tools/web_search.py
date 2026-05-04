"""Web search tool using MiniMax MCP or fallback."""

import asyncio
import json
import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Literal

import httpx
from langchain_core.tools import BaseTool
from pydantic import Field

from app.config import settings

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Tool for web search via MiniMax MCP or DuckDuckGo fallback.

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

    def __init__(self, api_key: str | None = None, base_url: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._api_key = api_key or settings.web_search.api_key
        self._base_url = base_url or settings.web_search.base_url
        self._mcp_command = settings.web_search.mcp_command
        self._mcp_args = settings.web_search.mcp_args

    async def _ainvoke(self, tool_input: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Execute web search asynchronously."""
        logger.info("WebSearchTool invoked with input: %s", tool_input)
        query = tool_input.get("query", "")
        if not query:
            return {"error": "query is required"}

        # Try MiniMax MCP first if configured
        if self._api_key and self._api_key != "your-api-key-here":
            result = await self._search_via_mcp(query)
            if result:
                return result

        # Fallback to DuckDuckGo
        logger.info("Trying DuckDuckGo fallback for query: %s", query)
        result = await self._search_fallback(query)
        if result.get("results"):
            return result

        # If fallback failed, return error with suggestion
        return {
            "error": f"Web search failed. MiniMax MCP not configured or unavailable. Query: {query}",
            "results": [],
            "suggestion": "Please configure a valid MiniMax API key in config.yaml to enable web search"
        }

    async def _search_via_mcp(self, query: str) -> dict[str, Any] | None:
        """Search using MiniMax MCP server."""
        # Create temp directory for MCP if needed
        cache_dir = Path(tempfile.gettempdir()) / "minimax_mcp_cache"
        cache_dir.mkdir(exist_ok=True)

        env = {
            "MINIMAX_API_KEY": self._api_key,
            "MINIMAX_MCP_BASE_PATH": str(cache_dir),
            "MINIMAX_API_HOST": self._base_url,
            "MINIMAX_API_RESOURCE_MODE": "local",
        }

        try:
            process = await asyncio.create_subprocess_exec(
                self._mcp_command,
                *self._mcp_args,
                env={**dict(__import__("os").environ), **env},
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for MCP server to initialize
            await asyncio.sleep(2.0)

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "claw-platform", "version": "1.0.0"}
                },
            }
            process.stdin.write(json.dumps(init_request).encode() + b"\n")
            await process.stdin.drain()

            # Read initialize response
            init_response = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=10.0
            )
            logger.info("MCP init response: %s", init_response.decode()[:200])

            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
            process.stdin.write(json.dumps(initialized_notification).encode() + b"\n")
            await process.stdin.drain()

            # Send JSON-RPC request for tools/list
            request_id = 1
            list_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/list",
                "params": {},
            }
            process.stdin.write(json.dumps(list_request).encode() + b"\n")
            await process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=10.0
            )
            response = json.loads(response_line.decode())

            # Find web search tool
            tools = response.get("result", {}).get("tools", [])
            web_search_tool = None
            for tool in tools:
                if tool.get("name") == "web_search":
                    web_search_tool = tool
                    break

            if not web_search_tool:
                logger.warning("No web_search tool found in MiniMax MCP")
                process.terminate()
                return None

            # Call web_search tool
            request_id = 2
            call_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "web_search",
                    "arguments": {"query": query},
                },
            }
            process.stdin.write(json.dumps(call_request).encode() + b"\n")
            await process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=30.0
            )
            result = json.loads(response_line.decode())

            process.terminate()
            await process.wait()

            content = result.get("result", {}).get("content", [])
            if content and isinstance(content, list):
                text = content[0].get("text", "")
                return {"results": [], "raw": text}
            return {"results": [], "raw": ""}

        except Exception as e:
            logger.error("MiniMax MCP search failed: %s", e)
            return None

    async def _search_fallback(self, query: str) -> dict[str, Any]:
        """Fallback search using DuckDuckGo HTML."""
        results = []
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
                logger.info("DuckDuckGo response status: %s", response.status_code)
                response.raise_for_status()
                html = response.text
                logger.info("DuckDuckGo HTML length: %d", len(html))

                # Try multiple patterns to extract results
                patterns = [
                    r'<a class="result__a" href="([^"]+)">([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]+)</a>',
                    r'<a href="([^"]+)" class="result__a"[^>]*>([^<]+)</a>',
                    r'data-src="([^"]+)"[^>]*>[^<]*<div class="result__title">([^<]+)</div>',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.DOTALL)
                    if matches:
                        for url, title, snippet in matches[:5]:
                            results.append({
                                "title": title.strip(),
                                "url": url,
                                "snippet": snippet.strip().replace("<b>", "").replace("</b>", "") if snippet else "",
                            })
                        break

                logger.info("Parsed %d results from DuckDuckGo", len(results))
                return {
                    "results": results,
                    "answer": None,
                }
        except httpx.ConnectTimeout as e:
            logger.error("WebSearchTool DuckDuckGo connection timeout: %s", e)
            return {"error": f"Connection timeout: {e}", "results": []}
        except httpx.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            if status:
                logger.error("WebSearchTool fallback HTTP error: %s, status: %s", e, status)
            else:
                logger.error("WebSearchTool fallback HTTP error: %s", e)
            return {"error": f"HTTP error: {e}", "results": []}
        except Exception as e:
            logger.error("WebSearchTool fallback search failed: %s (%s)", e, type(e).__name__)
            return {"error": f"Web search failed: {e}", "results": []}

    def _run(self, tool_input: str | dict[str, Any], **kwargs) -> dict[str, Any]:
        """Sync invoke."""
        if isinstance(tool_input, str):
            try:
                tool_input = json.loads(tool_input)
            except json.JSONDecodeError:
                tool_input = {"query": tool_input}
        return asyncio.run(self._ainvoke(tool_input, **kwargs))

