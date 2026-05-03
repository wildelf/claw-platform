"""Tests for OpenSandbox client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.opensandbox import OpenSandboxClient


class TestOpenSandboxClient:
    """Tests for OpenSandboxClient."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx AsyncClient."""
        client = MagicMock()
        client.get = AsyncMock()
        client.post = AsyncMock()
        client.put = AsyncMock()
        client.delete = AsyncMock()
        client.aclose = AsyncMock()
        return client

    @pytest.fixture
    def client_with_mock(self, mock_httpx_client):
        """Create client with mocked HTTP client."""
        client = OpenSandboxClient(base_url="http://127.0.0.1:8080")
        client._client = mock_httpx_client
        return client

    def test_client_initialization(self):
        """Client should initialize with correct defaults."""
        client = OpenSandboxClient()
        assert client.base_url == "http://127.0.0.1:8080"
        assert client.timeout == 300

    def test_client_custom_url(self):
        """Client should accept custom base_url."""
        client = OpenSandboxClient(base_url="http://localhost:9000")
        assert client.base_url == "http://localhost:9000"

    def test_client_strips_trailing_slash(self):
        """Client should strip trailing slash from base_url."""
        client = OpenSandboxClient(base_url="http://localhost:8080/")
        assert client.base_url == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_health_check_success(self, client_with_mock, mock_httpx_client):
        """Health check should return True when server is healthy."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_httpx_client.get.return_value = mock_response

        result = await client_with_mock.health_check()
        assert result is True
        mock_httpx_client.get.assert_called_once_with("http://127.0.0.1:8080/health")

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client_with_mock, mock_httpx_client):
        """Health check should return False when server is unhealthy."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "unhealthy"}
        mock_httpx_client.get.return_value = mock_response

        result = await client_with_mock.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, client_with_mock, mock_httpx_client):
        """Health check should return False on exception."""
        mock_httpx_client.get.side_effect = Exception("Connection error")

        result = await client_with_mock.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_create_sandbox_success(self, client_with_mock, mock_httpx_client):
        """Create sandbox should return sandbox ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test-sandbox-123",
            "status": {"state": "Pending"},
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        sandbox_id = await client_with_mock.create_sandbox(
            image="python:3.12-slim",
            entrypoint=["python", "-c", "print('hello')"],
            timeout=300,
            memory_limit="512Mi",
        )

        assert sandbox_id == "test-sandbox-123"
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "http://127.0.0.1:8080/v1/sandboxes"

    @pytest.mark.asyncio
    async def test_create_sandbox_default_entrypoint(self, client_with_mock, mock_httpx_client):
        """Create sandbox should use default entrypoint when not specified."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "sandbox-456"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.post.return_value = mock_response

        await client_with_mock.create_sandbox(image="python:3.12-slim")

        call_args = mock_httpx_client.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["entrypoint"] == ["python", "-c", "import sys; print('sandbox ready')"]

    @pytest.mark.asyncio
    async def test_get_sandbox_status(self, client_with_mock, mock_httpx_client):
        """Get sandbox status should return status dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "sandbox-123",
            "status": {"state": "Running", "message": "Container started"},
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response

        status = await client_with_mock.get_sandbox_status("sandbox-123")

        assert status["id"] == "sandbox-123"
        assert status["status"]["state"] == "Running"
        mock_httpx_client.get.assert_called_with("http://127.0.0.1:8080/v1/sandboxes/sandbox-123")

    @pytest.mark.asyncio
    async def test_delete_sandbox(self, client_with_mock, mock_httpx_client):
        """Delete sandbox should make DELETE request."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.delete.return_value = mock_response

        await client_with_mock.delete_sandbox("sandbox-123")

        mock_httpx_client.delete.assert_called_with("http://127.0.0.1:8080/v1/sandboxes/sandbox-123")

    @pytest.mark.asyncio
    async def test_delete_sandbox_handles_exception(self, client_with_mock, mock_httpx_client):
        """Delete sandbox should not raise on exception."""
        mock_httpx_client.delete.side_effect = Exception("Not found")

        # Should not raise
        await client_with_mock.delete_sandbox("nonexistent")

    @pytest.mark.asyncio
    async def test_wait_for_sandbox_ready_true(self, client_with_mock, mock_httpx_client):
        """Wait for sandbox should return True when sandbox is running."""
        mock_response = MagicMock()
        mock_response.json.side_effect = [
            {"status": {"state": "Pending"}},
            {"status": {"state": "Running"}},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response

        result = await client_with_mock.wait_for_sandbox_ready("sandbox-123", timeout=5)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_sandbox_ready_false_on_terminated(self, client_with_mock, mock_httpx_client):
        """Wait for sandbox should return False when sandbox is terminated."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": {"state": "Terminated"}}
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response

        result = await client_with_mock.wait_for_sandbox_ready("sandbox-123", timeout=5)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_sandbox_logs(self, client_with_mock, mock_httpx_client):
        """Get sandbox logs should return log string."""
        mock_response = MagicMock()
        mock_response.text = "2026-05-03 output line1\n2026-05-03 output line2"
        mock_response.raise_for_status = MagicMock()
        mock_httpx_client.get.return_value = mock_response

        logs = await client_with_mock.get_sandbox_logs("sandbox-123")

        assert "output line1" in logs
        mock_httpx_client.get.assert_called_with(
            "http://127.0.0.1:8080/v1/sandboxes/sandbox-123/diagnostics/logs"
        )


class TestExecuteInSandbox:
    """Tests for execute_in_sandbox function."""

    @pytest.mark.asyncio
    async def test_execute_in_sandbox_success(self):
        """Execute script should return success result."""
        from app.infrastructure.opensandbox import execute_in_sandbox

        with patch("app.infrastructure.opensandbox.OpenSandboxClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_sandbox = AsyncMock(return_value="exec-sandbox-123")
            mock_client.get_sandbox_logs = AsyncMock(return_value="42")
            mock_client.get_sandbox_status = AsyncMock(return_value={
                "status": {"state": "Terminated"}
            })
            mock_client.delete_sandbox = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await execute_in_sandbox(
                script="print(42)",
                image="python:3.12-slim",
                timeout=60,
            )

            assert result["success"] is True
            assert result["sandbox_id"] == "exec-sandbox-123"
            assert result["output"] == "42"

    @pytest.mark.asyncio
    async def test_execute_in_sandbox_failure(self):
        """Execute script should return failure result on error."""
        from app.infrastructure.opensandbox import execute_in_sandbox

        with patch("app.infrastructure.opensandbox.OpenSandboxClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.create_sandbox = AsyncMock(side_effect=Exception("Server error"))
            mock_client.delete_sandbox = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await execute_in_sandbox(script="print('test')")

            assert result["success"] is False
            assert "error" in result
            assert "Server error" in result["error"]


class TestGetOpenSandboxClient:
    """Tests for get_opensandbox_client function."""

    def test_returns_client_instance(self):
        """Should return OpenSandboxClient instance."""
        from app.infrastructure.opensandbox import get_opensandbox_client

        # Reset global
        import app.infrastructure.opensandbox
        app.infrastructure.opensandbox._default_client = None

        client = get_opensandbox_client()

        assert isinstance(client, OpenSandboxClient)
        assert client.base_url == "http://127.0.0.1:8080"

    def test_returns_cached_instance(self):
        """Should return same instance on multiple calls."""
        from app.infrastructure.opensandbox import get_opensandbox_client

        # Reset global
        import app.infrastructure.opensandbox
        app.infrastructure.opensandbox._default_client = None

        client1 = get_opensandbox_client()
        client2 = get_opensandbox_client()

        assert client1 is client2