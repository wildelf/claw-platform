"""Tests for model service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.model_service import ModelService
from app.domain.model_config import ModelConfig, ModelProviderType
from app.domain.base import EntityId


@pytest.fixture
def mock_storage():
    """Create a mock storage."""
    storage = MagicMock()
    storage.get_model_config = AsyncMock()
    storage.save_model_config = AsyncMock(return_value=None)
    storage.delete_model_config = AsyncMock(return_value=None)
    storage.list_model_configs = AsyncMock(return_value=[])
    return storage


@pytest.fixture
def sample_model_config():
    """Create a sample model config for testing."""
    return ModelConfig(
        name="test-model",
        type=ModelProviderType.OPENAI,
        model="gpt-4",
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        user_id=EntityId.generate(),
    )


class TestModelService:
    """Tests for ModelService."""

    @pytest.mark.asyncio
    async def test_create_model_config(self, mock_storage, sample_model_config):
        """Creating a model config should save it to storage."""
        service = ModelService(mock_storage)
        result = await service.create(sample_model_config)
        assert result.name == sample_model_config.name
        mock_storage.save_model_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_model_config_returns_none_when_not_found(self, mock_storage):
        """get_model_config should return None for non-existent config."""
        mock_storage.get_model_config.return_value = None
        service = ModelService(mock_storage)
        result = await service.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_model_config_returns_config(self, mock_storage, sample_model_config):
        """get_model_config should return config when found."""
        mock_storage.get_model_config.return_value = sample_model_config
        service = ModelService(mock_storage)
        result = await service.get(sample_model_config.id)
        assert result == sample_model_config

    @pytest.mark.asyncio
    async def test_update_model_config(self, mock_storage, sample_model_config):
        """Updating a model config should save it."""
        mock_storage.get_model_config.return_value = sample_model_config
        service = ModelService(mock_storage)
        result = await service.update(sample_model_config.id, {"name": "updated-model"})
        assert result.name == "updated-model"
        mock_storage.save_model_config.assert_called()

    @pytest.mark.asyncio
    async def test_update_model_config_returns_none_when_not_found(self, mock_storage):
        """update_model_config should return None for non-existent config."""
        mock_storage.get_model_config.return_value = None
        service = ModelService(mock_storage)
        result = await service.update("nonexistent", {"name": "test"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_model_config_returns_true_when_found(self, mock_storage, sample_model_config):
        """delete_model_config should return True when config exists."""
        mock_storage.get_model_config.return_value = sample_model_config
        mock_storage.delete_model_config.return_value = True
        service = ModelService(mock_storage)
        result = await service.delete(sample_model_config.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_model_config_returns_false_when_not_found(self, mock_storage):
        """delete_model_config should return False when config doesn't exist."""
        mock_storage.get_model_config.return_value = None
        service = ModelService(mock_storage)
        result = await service.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_model_configs(self, mock_storage, sample_model_config):
        """list_model_configs should return list of configs."""
        mock_storage.list_model_configs.return_value = [sample_model_config]
        service = ModelService(mock_storage)
        result = await service.list_by_user("user-1")
        assert len(result) == 1
        assert result[0].name == "test-model"


class TestModelProviderType:
    """Tests for ModelProviderType enum."""

    def test_openai_type_value(self):
        """OpenAI type should have correct value."""
        assert ModelProviderType.OPENAI.value == "openai"

    def test_anthropic_type_value(self):
        """Anthropic type should have correct value."""
        assert ModelProviderType.ANTHROPIC.value == "anthropic"

    def test_all_provider_types_defined(self):
        """All expected provider types should be defined."""
        assert hasattr(ModelProviderType, "OPENAI")
        assert hasattr(ModelProviderType, "ANTHROPIC")