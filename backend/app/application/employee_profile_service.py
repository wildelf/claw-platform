"""Employee Profile application service."""

import logging
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.domain.employee_profile import EmployeeProfile
from app.infrastructure.storage.sqlite import SQLiteStorage
from app.infrastructure.git_manager import GitManager

logger = logging.getLogger(__name__)


class EmployeeProfileService:
    """Service for managing employee profiles with dual persistence (SQLite + Git)."""

    def __init__(self, storage: SQLiteStorage, git_manager: Optional[GitManager] = None):
        self.storage = storage
        self.git = git_manager or GitManager()

    def _get_profile_dir(self, profile: EmployeeProfile) -> Path:
        """Get the git-managed directory for a profile."""
        identity_root = Path(settings.identity_root).expanduser()
        return identity_root / str(profile.id)

    def _ensure_profile_dir(self, profile: EmployeeProfile) -> Path:
        """Create and return the profile directory."""
        profile_dir = self._get_profile_dir(profile)
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile.git_path = str(profile_dir)
        return profile_dir

    async def create(self, profile: EmployeeProfile) -> EmployeeProfile:
        """Create a new employee profile."""
        profile_dir = self._ensure_profile_dir(profile)

        # Create default profile.md
        profile_md = profile_dir / "profile.md"
        if not profile_md.exists():
            profile_md.write_text(self._generate_default_md(profile), encoding="utf-8")

        # Save to SQLite
        await self.storage.save_employee_profile(profile)

        # Commit to git
        await self.git.add_and_commit(profile_dir, f"Create employee: {profile.name}")

        return profile

    async def get(self, profile_id: str) -> Optional[EmployeeProfile]:
        """Get employee profile by ID."""
        return await self.storage.get_employee_profile(profile_id)

    async def list_by_user(self, user_id: str) -> List[EmployeeProfile]:
        """List all employee profiles for a user."""
        return await self.storage.list_employee_profiles(user_id)

    async def update(self, profile_id: str, data: dict) -> Optional[EmployeeProfile]:
        """Update employee profile fields."""
        profile = await self.get(profile_id)
        if not profile:
            return None

        for key, value in data.items():
            if hasattr(profile, key) and key not in ("id", "created_at", "updated_at"):
                setattr(profile, key, value)

        # Update git files if content fields changed
        if any(k in data for k in ("backstory", "personality", "constraints", "working_rules", "name", "role", "goal")):
            profile_dir = self._ensure_profile_dir(profile)
            profile_md = profile_dir / "profile.md"
            profile_md.write_text(self._generate_default_md(profile), encoding="utf-8")

            # Commit to git
            await self.git.add_and_commit(profile_dir, f"Update employee: {profile.name}")

        await self.storage.save_employee_profile(profile)
        return profile

    async def delete(self, profile_id: str) -> bool:
        """Delete employee profile and its git directory."""
        profile = await self.get(profile_id)
        if not profile:
            return False

        # Git remove and commit before filesystem removal
        profile_dir = self._get_profile_dir(profile)
        if profile_dir.exists() and (profile_dir / ".git").exists():
            await self.git.remove_and_commit(profile_dir, f"Delete employee: {profile.name}")

        # Remove git directory
        if profile_dir.exists():
            import shutil
            shutil.rmtree(profile_dir, ignore_errors=True)

        await self.storage.delete_employee_profile(profile_id)
        return True

    async def list_files(self, profile_id: str) -> List[str]:
        """List files in profile directory."""
        profile = await self.get(profile_id)
        if not profile:
            return []
        profile_dir = self._get_profile_dir(profile)
        if not profile_dir.exists():
            return []
        return [f.name for f in profile_dir.iterdir() if f.is_file()]

    async def get_file(self, profile_id: str, filename: str) -> Optional[dict]:
        """Get file content from profile directory."""
        profile = await self.get(profile_id)
        if not profile:
            return None
        profile_dir = self._get_profile_dir(profile)
        file_path = profile_dir / filename
        if not file_path.exists() or not file_path.is_file():
            return None
        return {
            "filename": filename,
            "content": file_path.read_text(encoding="utf-8"),
        }

    async def update_file(self, profile_id: str, filename: str, content: str) -> bool:
        """Update file content in profile directory."""
        profile = await self.get(profile_id)
        if not profile:
            return False
        profile_dir = self._ensure_profile_dir(profile)
        file_path = profile_dir / filename
        file_path.write_text(content, encoding="utf-8")

        # Commit to git
        await self.git.add_and_commit(profile_dir, f"Update file: {filename}")
        return True

    async def get_git_log(self, profile_id: str, max_commits: int = 10) -> list[dict]:
        """Get git commit log for a profile."""
        profile = await self.get(profile_id)
        if not profile:
            return []
        profile_dir = self._get_profile_dir(profile)
        if not profile_dir.exists() or not (profile_dir / ".git").exists():
            return []
        return await self.git.get_log(profile_dir, max_commits=max_commits)

    def _generate_default_md(self, profile: EmployeeProfile) -> str:
        """Generate default profile.md content."""
        sections = [
            f"# {profile.name}",
            "",
            f"**Role:** {profile.role}",
            f"**Goal:** {profile.goal}",
            "",
            "## Background",
            profile.backstory or "No background specified.",
            "",
            "## Personality",
            profile.personality or "No personality specified.",
            "",
            "## Constraints",
            profile.constraints or "No constraints specified.",
            "",
            "## Working Rules",
            profile.working_rules or "No working rules specified.",
            "",
        ]
        return "\n".join(sections)
