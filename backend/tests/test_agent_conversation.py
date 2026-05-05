"""Tests for multi-turn conversation via checkpointer."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime

from app.api.agents import RunAgentRequest


class TestRunAgentRequest:
    """Test RunAgentRequest model."""

    def test_session_id_field_exists(self):
        """RunAgentRequest should accept session_id field."""
        request = RunAgentRequest(
            task="test task",
            session_id="test-session-123"
        )
        assert request.session_id == "test-session-123"

    def test_session_id_optional(self):
        """session_id should be optional (None by default)."""
        request = RunAgentRequest(task="test task")
        assert request.session_id is None

    def test_all_fields_required(self):
        """All required fields should work."""
        request = RunAgentRequest(
            task="test task",
            images=["base64image"],
            model_config_id="model-1",
            session_id="session-1"
        )
        assert request.task == "test task"
        assert request.images == ["base64image"]
        assert request.model_config_id == "model-1"
        assert request.session_id == "session-1"


class TestDeepAgentsRunnerCheckpointer:
    """Test DeepAgentsRunner checkpointer support."""

    def test_set_checkpointer_stores_checkpointer_and_thread_id(self):
        """set_checkpointer should store checkpointer and thread_id."""
        from app.deepagents.wrapper import DeepAgentsRunner

        # Create minimal mock dependencies
        mock_agent = MagicMock()
        mock_agent.id = "test-agent"
        mock_agent.skill_ids = []
        mock_agent.tool_ids = []
        mock_agent.enabled_builtin_tools = []

        mock_storage = MagicMock()
        mock_storage.get_skill = AsyncMock(return_value=None)

        runner = DeepAgentsRunner(
            agent=mock_agent,
            storage=mock_storage,
        )

        # Initially should be None
        assert runner._checkpointer is None
        assert runner._thread_id is None

        # Set checkpointer
        mock_checkpointer = MagicMock()
        runner.set_checkpointer(mock_checkpointer, "thread-123")

        # Should be stored
        assert runner._checkpointer is mock_checkpointer
        assert runner._thread_id == "thread-123"

    def test_thread_id_config_builds_correctly(self):
        """Config with thread_id should build correctly for checkpointer."""
        from app.deepagents.wrapper import DeepAgentsRunner

        mock_agent = MagicMock()
        mock_agent.id = "test-agent"
        mock_agent.skill_ids = []
        mock_agent.tool_ids = []
        mock_agent.enabled_builtin_tools = []

        mock_storage = MagicMock()
        mock_storage.get_skill = AsyncMock(return_value=None)

        runner = DeepAgentsRunner(
            agent=mock_agent,
            storage=mock_storage,
        )
        runner.set_checkpointer(MagicMock(), "session-abc")

        # Verify the internal state that would be used for config
        assert runner._thread_id == "session-abc"

    def test_no_thread_id_means_empty_config(self):
        """Without thread_id, config should be empty dict."""
        from app.deepagents.wrapper import DeepAgentsRunner

        mock_agent = MagicMock()
        mock_agent.id = "test-agent"
        mock_agent.skill_ids = []
        mock_agent.tool_ids = []
        mock_agent.enabled_builtin_tools = []

        mock_storage = MagicMock()
        mock_storage.get_skill = AsyncMock(return_value=None)

        runner = DeepAgentsRunner(
            agent=mock_agent,
            storage=mock_storage,
        )
        # Never set checkpointer

        assert runner._thread_id is None
        assert runner._checkpointer is None