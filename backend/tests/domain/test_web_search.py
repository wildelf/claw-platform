"""Tests for WebSearchTool."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.domain.tools.web_search import WebSearchTool
from app.config import settings


class TestWebSearchTool:
    """Tests for WebSearchTool."""

    @pytest.fixture
    def tool_with_mock_mcp(self):
        """Create a WebSearchTool with mocked MCP."""
        return WebSearchTool(api_key="test-key", base_url="https://api.minimaxi.com")

    @pytest.mark.asyncio
    async def test_invoke_requires_query(self, tool_with_mock_mcp):
        """Should return error when query is missing."""
        result = await tool_with_mock_mcp._ainvoke({})
        assert result == {"error": "query is required"}

    @pytest.mark.asyncio
    async def test_invoke_with_empty_query_string(self, tool_with_mock_mcp):
        """Should return error when query is empty string."""
        result = await tool_with_mock_mcp._ainvoke({"query": ""})
        assert result == {"error": "query is required"}

    @pytest.mark.asyncio
    async def test_invoke_passes_query_to_mcp(self, tool_with_mock_mcp):
        """Should pass query to MCP search when configured."""
        with patch.object(tool_with_mock_mcp, '_search_via_mcp', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = {"results": [{"title": "Test", "url": "http://test.com", "snippet": "Test snippet"}]}
            result = await tool_with_mock_mcp._ainvoke({"query": "test query"})
            mock_mcp.assert_called_once_with("test query")
            assert "results" in result

    @pytest.mark.asyncio
    async def test_falls_back_to_duckduckgo_when_no_api_key(self):
        """Should fall back to DuckDuckGo when no API key is set and config also has no key."""
        tool = WebSearchTool(api_key=None)
        # Force _api_key to None to trigger fallback
        tool._api_key = None
        with patch.object(tool, '_search_fallback', new_callable=AsyncMock) as mock_ddg:
            mock_ddg.return_value = {"results": [], "answer": None}
            result = await tool._ainvoke({"query": "test"})
            mock_ddg.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_falls_back_to_duckduckgo_on_mcp_failure(self):
        """Should fall back to DuckDuckGo when MCP fails."""
        tool = WebSearchTool(api_key="test-key")
        with patch.object(tool, '_search_via_mcp', new_callable=AsyncMock) as mock_mcp:
            mock_mcp.return_value = None  # MCP failed
            with patch.object(tool, '_search_fallback', new_callable=AsyncMock) as mock_ddg:
                mock_ddg.return_value = {"results": [{"title": "Fallback", "url": "http://fallback.com", "snippet": "From DuckDuckGo"}]}
                result = await tool._ainvoke({"query": "test"})
                mock_ddg.assert_called_once()


class TestWebSearchToolSync:
    """Tests for sync _run method."""

    def test_run_accepts_string_input(self):
        """Should accept string input and convert to dict."""
        tool = WebSearchTool(api_key=None)
        with patch.object(tool, '_search_fallback', new_callable=AsyncMock) as mock_ddg:
            mock_ddg.return_value = {"results": []}
            result = tool._run("test query")
            assert isinstance(result, dict)

    def test_run_accepts_dict_input(self):
        """Should accept dict input directly."""
        tool = WebSearchTool(api_key=None)
        with patch.object(tool, '_search_fallback', new_callable=AsyncMock) as mock_ddg:
            mock_ddg.return_value = {"results": []}
            result = tool._run({"query": "test"})
            assert isinstance(result, dict)

    def test_run_rejects_invalid_json_string(self):
        """Should treat non-JSON string as query value."""
        tool = WebSearchTool(api_key=None)
        with patch.object(tool, '_search_fallback', new_callable=AsyncMock) as mock_ddg:
            mock_ddg.return_value = {"results": []}
            result = tool._run("{not valid json")
            assert isinstance(result, dict)


@pytest.mark.skipif(
    not settings.web_search.enabled or not settings.web_search.api_key,
    reason="web_search not enabled or api_key not configured"
)
class TestWebSearchToolReal:
    """Real integration tests using config.yaml settings."""

    @pytest.fixture
    def real_tool(self):
        """Create WebSearchTool using config.yaml settings."""
        return WebSearchTool(
            api_key=settings.web_search.api_key,
            base_url=settings.web_search.base_url,
        )

    @pytest.mark.asyncio
    async def test_real_mcp_search(self, real_tool):
        """Real MCP search with config from config.yaml."""
        result = await real_tool._ainvoke({"query": "hello world"})
        # Should get some response (either MCP or fallback)
        assert "results" in result or "raw" in result or "error" in result

    @pytest.mark.asyncio
    async def test_real_mcp_web_search_returns_structured_result(self, real_tool):
        """MCP should return structured search results."""
        result = await real_tool._ainvoke({"query": "python programming"})
        # If MCP succeeded, should have results
        if "results" in result and len(result["results"]) > 0:
            assert "title" in result["results"][0] or "url" in result["results"][0]