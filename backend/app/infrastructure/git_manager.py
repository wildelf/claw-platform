"""Git integration for employee profiles."""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GitManager:
    """Manages Git operations for employee profile directories."""

    def __init__(self, git_executable: str = "git"):
        self._git = git_executable

    async def _run_git(self, repo_path: Path, *args: str) -> str:
        """Run a git command in the given repository path."""
        import asyncio
        import shlex

        cmd = [self._git] + list(args)
        logger.debug("Running git command: %s in %s", shlex.join(cmd), repo_path)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "GIT_AUTHOR_NAME": "Claw Platform", "GIT_AUTHOR_EMAIL": "platform@claw.local", "GIT_COMMITTER_NAME": "Claw Platform", "GIT_COMMITTER_EMAIL": "platform@claw.local"},
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace").strip()
            logger.warning("Git command failed: %s — %s", shlex.join(cmd), error_msg)

        return stdout.decode("utf-8", errors="replace").strip()

    async def init_repo(self, repo_path: Path) -> bool:
        """Initialize a git repository if one does not already exist."""
        git_dir = repo_path / ".git"
        if git_dir.exists():
            return True
        try:
            await self._run_git(repo_path, "init")
            return True
        except Exception as e:
            logger.error("Failed to init git repo at %s: %s", repo_path, e)
            return False

    async def add_and_commit(self, repo_path: Path, message: str) -> bool:
        """Stage all changes and commit with the given message."""
        try:
            await self.init_repo(repo_path)
            await self._run_git(repo_path, "add", "-A")
            # Check if there are changes to commit
            status = await self._run_git(repo_path, "status", "--porcelain")
            if not status:
                logger.debug("No changes to commit in %s", repo_path)
                return True
            await self._run_git(repo_path, "commit", "-m", message)
            return True
        except Exception as e:
            logger.error("Failed to commit in %s: %s", repo_path, e)
            return False

    async def remove_and_commit(self, repo_path: Path, message: str) -> bool:
        """Remove all tracked files and commit."""
        try:
            await self.init_repo(repo_path)
            await self._run_git(repo_path, "rm", "-rf", ".")
            status = await self._run_git(repo_path, "status", "--porcelain")
            if not status:
                logger.debug("No changes to commit in %s", repo_path)
                return True
            await self._run_git(repo_path, "commit", "-m", message)
            return True
        except Exception as e:
            logger.error("Failed to remove and commit in %s: %s", repo_path, e)
            return False

    async def get_log(self, repo_path: Path, max_commits: int = 10) -> list[dict]:
        """Get recent commit log."""
        try:
            output = await self._run_git(
                repo_path,
                "log",
                f"--max-count={max_commits}",
                "--format=%H|%s|%ai",
            )
            if not output:
                return []
            entries = []
            for line in output.split("\n"):
                parts = line.split("|", 2)
                if len(parts) == 3:
                    entries.append({
                        "hash": parts[0],
                        "message": parts[1],
                        "date": parts[2],
                    })
            return entries
        except Exception as e:
            logger.error("Failed to get git log for %s: %s", repo_path, e)
            return []
