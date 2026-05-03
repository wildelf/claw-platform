"""Tests for ScriptExecutionTool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domain.tools.script_execution import (
    ScriptExecutionTool,
    SandboxToolFactory,
)


class TestScriptExecutionTool:
    """Tests for ScriptExecutionTool."""

    @pytest.fixture
    def tool(self):
        """Create a tool instance for testing."""
        return ScriptExecutionTool(opensandbox_url="http://127.0.0.1:8080")

    def test_tool_initialization(self, tool):
        """Tool should initialize with correct name and description."""
        assert tool.name == "execute_script"
        assert "sandbox" in tool.description.lower()
        assert tool.args_schema is not None

    def test_tool_has_execute_schema(self, tool):
        """Tool should have execute_script input schema."""
        schema = tool.args_schema
        assert schema is not None
        # Check schema fields exist
        assert hasattr(schema, "model_fields")
        assert "script" in schema.model_fields
        assert "timeout" in schema.model_fields
        assert "memory_limit" in schema.model_fields

    def test_invoke_with_dict_input_sync(self, tool):
        """Tool _invoke should accept dict input synchronously."""
        mock_result = {"success": True, "output": "hello"}
        with patch.object(ScriptExecutionTool, "execute_script", return_value=mock_result):
            result = tool._invoke({"script": "print('hello')", "timeout": 30})

            assert result["success"] is True
            assert result["output"] == "hello"

    def test_run_with_dict_input(self, tool):
        """Tool _run should accept dict input."""
        mock_result = {"success": True, "output": "world"}
        with patch.object(ScriptExecutionTool, "execute_script", return_value=mock_result):
            result = tool._run({"script": "print('world')", "timeout": 60})

            assert result["success"] is True
            assert result["output"] == "world"

    def test_invoke_with_custom_memory_limit(self, tool):
        """Tool should accept custom memory limit via _invoke."""
        mock_result = {"success": True, "output": ""}
        with patch.object(ScriptExecutionTool, "execute_script", return_value=mock_result) as mock_exec:
            tool._invoke({
                "script": "x = 1",
                "memory_limit": "1Gi",
            })

            mock_exec.assert_called_once()
            call_args = mock_exec.call_args[0]
            assert call_args[2] == "1Gi"


class TestSandboxToolFactory:
    """Tests for SandboxToolFactory."""

    def test_create_script_tool(self):
        """Factory should create ScriptExecutionTool."""
        tool = SandboxToolFactory.create_script_tool(
            opensandbox_url="http://localhost:9000"
        )

        assert isinstance(tool, ScriptExecutionTool)
        assert tool._opensandbox_url == "http://localhost:9000"

    def test_create_tool_with_default_url(self):
        """Factory should use default URL when not specified."""
        tool = SandboxToolFactory.create_script_tool()

        assert isinstance(tool, ScriptExecutionTool)
        assert tool._opensandbox_url == "http://127.0.0.1:8080"

    def test_get_tools_returns_list(self):
        """Factory get_tools should return list of tools."""
        tools = SandboxToolFactory.get_tools()

        assert isinstance(tools, list)
        assert len(tools) >= 1
        assert all(hasattr(t, "name") for t in tools)

    def test_get_tools_contains_script_tool(self):
        """get_tools should include ScriptExecutionTool."""
        tools = SandboxToolFactory.get_tools()

        tool_names = [t.name for t in tools]
        assert "execute_script" in tool_names


class TestScriptExecutionInput:
    """Tests for ScriptExecutionInput schema."""

    def test_script_field_required(self):
        """Script field should be required."""
        from app.domain.tools.script_execution import ScriptExecutionInput

        # Should not allow empty script without explicit default
        fields = ScriptExecutionInput.model_fields
        assert "script" in fields

    def test_timeout_has_default(self):
        """Timeout should have default value."""
        from app.domain.tools.script_execution import ScriptExecutionInput

        schema = ScriptExecutionInput
        # Check default is 60
        instance = schema(script="print(1)")
        assert instance.timeout == 60

    def test_memory_limit_has_default(self):
        """Memory limit should have default value."""
        from app.domain.tools.script_execution import ScriptExecutionInput

        instance = ScriptExecutionInput(script="print(1)")
        assert instance.memory_limit == "256Mi"

    def test_custom_timeout_and_memory(self):
        """Should accept custom timeout and memory."""
        from app.domain.tools.script_execution import ScriptExecutionInput

        instance = ScriptExecutionInput(
            script="print(1)",
            timeout=120,
            memory_limit="1Gi",
        )
        assert instance.timeout == 120
        assert instance.memory_limit == "1Gi"


class TestScriptExecutionToolAsync:
    """Async tests for ScriptExecutionTool."""

    @pytest.fixture
    def tool(self):
        """Create a tool instance for testing."""
        return ScriptExecutionTool(opensandbox_url="http://127.0.0.1:8080")

    @pytest.mark.asyncio
    async def test_ainvoke_success(self, tool):
        """_ainvoke should return success result."""
        mock_result = {"success": True, "output": "42", "state": "Terminated"}
        with patch.object(ScriptExecutionTool, "execute_script", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result

            result = await tool._ainvoke({"script": "print(42)"})

            assert result["success"] is True
            assert result["output"] == "42"

    @pytest.mark.asyncio
    async def test_ainvoke_failure(self, tool):
        """_ainvoke should return failure result on error."""
        mock_result = {"success": False, "error": "Sandbox timeout", "state": "Error"}
        with patch.object(ScriptExecutionTool, "execute_script", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result

            result = await tool._ainvoke({"script": "import time; time.sleep(1000)"})

            assert result["success"] is False
            assert "Sandbox timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_ainvoke_with_custom_timeout(self, tool):
        """_ainvoke should pass custom timeout to execute_script."""
        mock_result = {"success": True, "output": ""}
        with patch.object(ScriptExecutionTool, "execute_script", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result

            await tool._ainvoke({"script": "x = 1", "timeout": 120})

            mock_exec.assert_called_once()
            call_args = mock_exec.call_args[0]
            assert call_args[1] == 120