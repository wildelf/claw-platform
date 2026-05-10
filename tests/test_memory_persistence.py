import pytest
import tempfile
import shutil
from pathlib import Path
from app.application.memory.memory_persistence import MemoryPersistence, MemoryType


@pytest.fixture
def temp_mem_dir():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.mark.asyncio
async def test_save_to_memory_md(temp_mem_dir):
    persistence = MemoryPersistence(base_dir=temp_mem_dir)
    await persistence.save(
        agent_id="agent-123",
        memory_type=MemoryType.MEMORY_MD,
        content="# Test Memory\n记住这个配置",
    )
    memory_file = temp_mem_dir / "agent-123" / "MEMORY.md"
    assert memory_file.exists()
    assert "Test Memory" in memory_file.read_text()


@pytest.mark.asyncio
async def test_save_to_user_md(temp_mem_dir):
    persistence = MemoryPersistence(base_dir=temp_mem_dir)
    await persistence.save(
        agent_id="agent-123",
        memory_type=MemoryType.USER_MD,
        content="# User Preferences\n用户喜欢中文",
    )
    user_file = temp_mem_dir / "agent-123" / "USER.md"
    assert user_file.exists()
    assert "User Preferences" in user_file.read_text()


@pytest.mark.asyncio
async def test_read_empty(temp_mem_dir):
    persistence = MemoryPersistence(base_dir=temp_mem_dir)
    content = await persistence.read("nonexistent", MemoryType.MEMORY_MD)
    assert content == ""