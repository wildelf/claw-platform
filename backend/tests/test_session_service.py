"""Tests for session service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.session_service import SessionService
from app.domain.session import Session
from app.domain.base import EntityId


@pytest.fixture
def mock_storage():
    """Create a mock storage adapter."""
    storage = MagicMock()
    storage.get_session = AsyncMock()
    storage.save_session = AsyncMock(return_value=None)
    storage.list_sessions = AsyncMock(return_value=[])
    storage.delete_session = AsyncMock(return_value=None)
    return storage


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    return Session.create(agent_id="agent-1", name="test-session")


class TestSessionService:
    """Tests for SessionService."""

    @pytest.mark.asyncio
    async def test_create_session(self, mock_storage):
        """Creating a session should save it to storage."""
        service = SessionService(mock_storage)
        result = await service.create_session(agent_id="agent-1", name="my-session")

        assert result.agent_id == "agent-1"
        assert result.name == "my-session"
        assert result.message_count == 0
        mock_storage.save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_without_name(self, mock_storage):
        """Creating a session without a name should use empty string."""
        service = SessionService(mock_storage)
        result = await service.create_session(agent_id="agent-1")

        assert result.name == ""
        assert result.agent_id == "agent-1"
        mock_storage.save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session(self, mock_storage, sample_session):
        """Getting a session should return it from storage."""
        mock_storage.get_session.return_value = sample_session
        service = SessionService(mock_storage)

        result = await service.get_session(sample_session.id)

        assert result == sample_session
        mock_storage.get_session.assert_called_once_with(sample_session.id)

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_storage):
        """Getting a non-existent session should return None."""
        mock_storage.get_session.return_value = None
        service = SessionService(mock_storage)

        result = await service.get_session("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_sessions(self, mock_storage, sample_session):
        """Listing sessions should return them from storage."""
        mock_storage.list_sessions.return_value = [sample_session]
        service = SessionService(mock_storage)

        result = await service.list_sessions(offset=0, limit=50)

        assert len(result) == 1
        assert result[0] == sample_session
        mock_storage.list_sessions.assert_called_once_with(offset=0, limit=50)

    @pytest.mark.asyncio
    async def test_list_sessions_default_pagination(self, mock_storage):
        """Listing sessions should use default pagination."""
        mock_storage.list_sessions.return_value = []
        service = SessionService(mock_storage)

        await service.list_sessions()

        mock_storage.list_sessions.assert_called_once_with(offset=0, limit=100)

    @pytest.mark.asyncio
    async def test_update_session(self, mock_storage, sample_session):
        """Updating a session should save the changes."""
        mock_storage.get_session.return_value = sample_session
        service = SessionService(mock_storage)

        result = await service.update_session(sample_session.id, name="updated-name")

        assert result is not None
        assert result.name == "updated-name"
        mock_storage.save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, mock_storage):
        """Updating a non-existent session should return None."""
        mock_storage.get_session.return_value = None
        service = SessionService(mock_storage)

        result = await service.update_session("nonexistent-id", name="new-name")

        assert result is None
        mock_storage.save_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_session(self, mock_storage, sample_session):
        """Deleting a session should remove it from storage."""
        service = SessionService(mock_storage)

        await service.delete_session(sample_session.id)

        mock_storage.delete_session.assert_called_once_with(sample_session.id)

    @pytest.mark.asyncio
    async def test_increment_message_count(self, mock_storage, sample_session):
        """Incrementing message count should update the session."""
        initial_count = sample_session.message_count
        mock_storage.get_session.return_value = sample_session
        service = SessionService(mock_storage)

        await service.increment_message_count(sample_session.id)

        assert sample_session.message_count == initial_count + 1
        mock_storage.save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_message_count_not_found(self, mock_storage):
        """Incrementing message count on non-existent session should do nothing."""
        mock_storage.get_session.return_value = None
        service = SessionService(mock_storage)

        await service.increment_message_count("nonexistent-id")

        mock_storage.save_session.assert_not_called()
