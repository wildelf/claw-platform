"""Tests for Employee Profile CRUD + Git integration."""

import tempfile
from pathlib import Path

import pytest

from app.domain.base import EntityId
from app.domain.employee_profile import EmployeeProfile
from app.infrastructure.git_manager import GitManager
from app.infrastructure.storage.sqlite import SQLiteStorage


@pytest.fixture
def storage():
    """Create a temporary SQLite storage."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    s = SQLiteStorage(db_path)
    import asyncio
    asyncio.get_event_loop().run_until_complete(s.init_db())
    yield s
    import asyncio
    asyncio.get_event_loop().run_until_complete(s.close())
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def git_manager():
    return GitManager()


@pytest.fixture
def profile_data():
    return {
        "name": "Test Employee",
        "role": "Developer",
        "goal": "Build great software",
        "backstory": "Experienced engineer",
        "personality": "Detail-oriented",
        "constraints": "No production deploys",
        "working_rules": "Code review required",
    }


class TestEmployeeProfileModel:
    """Test EmployeeProfile domain entity."""

    def test_create_profile(self, profile_data):
        profile = EmployeeProfile(**profile_data)
        assert profile.id is not None
        assert profile.name == "Test Employee"
        assert profile.status == "active"
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_to_dict(self, profile_data):
        profile = EmployeeProfile(**profile_data)
        d = profile.to_dict()
        assert d["name"] == "Test Employee"
        assert d["role"] == "Developer"

    def test_to_summary(self, profile_data):
        profile = EmployeeProfile(**profile_data)
        s = profile.to_summary()
        assert s["name"] == "Test Employee"
        assert "id" in s
        assert "status" in s


class TestEmployeeProfileStorage:
    """Test SQLite storage for employee profiles."""

    @pytest.mark.asyncio
    async def test_save_and_get(self, storage, profile_data):
        profile = EmployeeProfile(**profile_data, user_id=EntityId("user-1"))
        await storage.save_employee_profile(profile)

        result = await storage.get_employee_profile(str(profile.id))
        assert result is not None
        assert result.name == "Test Employee"
        assert result.role == "Developer"

    @pytest.mark.asyncio
    async def test_update_existing(self, storage, profile_data):
        profile = EmployeeProfile(**profile_data, user_id=EntityId("user-1"))
        await storage.save_employee_profile(profile)

        profile.role = "Senior Developer"
        await storage.save_employee_profile(profile)

        result = await storage.get_employee_profile(str(profile.id))
        assert result.role == "Senior Developer"

    @pytest.mark.asyncio
    async def test_list_by_user(self, storage, profile_data):
        p1 = EmployeeProfile(**profile_data, user_id=EntityId("user-1"))
        p2_data = dict(profile_data)
        p2_data["name"] = "Another"
        p2 = EmployeeProfile(**p2_data, user_id=EntityId("user-1"))
        await storage.save_employee_profile(p1)
        await storage.save_employee_profile(p2)

        results = await storage.list_employee_profiles("user-1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_delete(self, storage, profile_data):
        profile = EmployeeProfile(**profile_data, user_id=EntityId("user-1"))
        await storage.save_employee_profile(profile)

        await storage.delete_employee_profile(str(profile.id))
        result = await storage.get_employee_profile(str(profile.id))
        assert result is None

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage):
        result = await storage.get_employee_profile("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_empty(self, storage):
        results = await storage.list_employee_profiles("user-999")
        assert results == []


class TestGitManager:
    """Test Git operations."""

    @pytest.mark.asyncio
    async def test_init_and_commit(self, tmp_path):
        git = GitManager()
        repo = tmp_path / "test-repo"
        repo.mkdir()

        # Init repo
        assert await git.init_repo(repo)
        assert (repo / ".git").exists()

        # Create a file and commit
        (repo / "profile.md").write_text("# Test")
        assert await git.add_and_commit(repo, "Create test profile")

        # Check log
        log = await git.get_log(repo)
        assert len(log) >= 1
        assert "Create test profile" in log[0]["message"]

    @pytest.mark.asyncio
    async def test_no_changes_commit(self, tmp_path):
        git = GitManager()
        repo = tmp_path / "test-repo"
        repo.mkdir()
        await git.init_repo(repo)

        # Commit with no changes should succeed
        assert await git.add_and_commit(repo, "Empty commit")

    @pytest.mark.asyncio
    async def test_remove_and_commit(self, tmp_path):
        git = GitManager()
        repo = tmp_path / "test-repo"
        repo.mkdir()
        (repo / "profile.md").write_text("# Test")
        await git.add_and_commit(repo, "Create")

        # Remove and commit
        assert await git.remove_and_commit(repo, "Delete")


class TestEmployeeProfileServiceIntegration:
    """End-to-end service test with temp directory."""

    @pytest.mark.asyncio
    async def test_create_writes_git_files(self, storage, profile_data, tmp_path):
        from app.application.employee_profile_service import EmployeeProfileService
        from app.config import settings

        # Override identity_root to temp directory
        identity_root = tmp_path / "employees"
        identity_root.mkdir()

        service = EmployeeProfileService(storage)

        # Temporarily patch settings
        original = settings.identity_root
        settings.identity_root = str(identity_root)
        try:
            profile = EmployeeProfile(**profile_data, user_id=EntityId("user-1"))
            created = await service.create(profile)

            # Check SQLite
            result = await storage.get_employee_profile(str(created.id))
            assert result is not None
            assert result.name == "Test Employee"

            # Check Git
            profile_dir = identity_root / str(created.id)
            assert (profile_dir / "profile.md").exists()
            assert (profile_dir / ".git").exists()

            # Check git log
            log = await service.get_git_log(str(created.id))
            assert len(log) >= 1
            assert "Create employee" in log[0]["message"]
        finally:
            settings.identity_root = original

    @pytest.mark.asyncio
    async def test_update_writes_git_commit(self, storage, profile_data, tmp_path):
        from app.application.employee_profile_service import EmployeeProfileService
        from app.config import settings

        identity_root = tmp_path / "employees"
        identity_root.mkdir()
        service = EmployeeProfileService(storage)

        original = settings.identity_root
        settings.identity_root = str(identity_root)
        try:
            profile = EmployeeProfile(**profile_data, user_id=EntityId("user-1"))
            created = await service.create(profile)

            # Update
            updated = await service.update(str(created.id), {"role": "Senior Developer"})
            assert updated is not None
            assert updated.role == "Senior Developer"

            # Check git log has both create and update
            log = await service.get_git_log(str(created.id))
            assert len(log) >= 2
        finally:
            settings.identity_root = original

    @pytest.mark.asyncio
    async def test_delete_removes_db_and_git(self, storage, profile_data, tmp_path):
        from app.application.employee_profile_service import EmployeeProfileService
        from app.config import settings

        identity_root = tmp_path / "employees"
        identity_root.mkdir()
        service = EmployeeProfileService(storage)

        original = settings.identity_root
        settings.identity_root = str(identity_root)
        try:
            profile = EmployeeProfile(**profile_data, user_id=EntityId("user-1"))
            created = await service.create(profile)
            profile_dir = identity_root / str(created.id)
            assert profile_dir.exists()

            # Delete
            deleted = await service.delete(str(created.id))
            assert deleted is True

            # Check DB
            result = await storage.get_employee_profile(str(created.id))
            assert result is None

            # Check filesystem
            assert not profile_dir.exists()
        finally:
            settings.identity_root = original
