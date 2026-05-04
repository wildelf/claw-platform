"""OpenSandbox Backend implementing BackendProtocol for deepagents."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from deepagents.backends.protocol import (
    BackendProtocol,
    EditResult,
    ExecuteResponse,
    FileData,
    FileDownloadResponse,
    FileInfo,
    FileUploadResponse,
    GlobResult,
    GrepMatch,
    GrepResult,
    LsResult,
    ReadResult,
    SandboxBackendProtocol,
    WriteResult,
)

from app.config import settings
from opensandbox.sandbox import Sandbox
from opensandbox.config import ConnectionConfig
from opensandbox.models.filesystem import SearchEntry, WriteEntry

logger = logging.getLogger(__name__)

VIRTUAL_ROOT = "/workspace"


class OpenSandboxBackend(SandboxBackendProtocol):
    """OpenSandbox implementation of BackendProtocol.

    Uses the official OpenSandbox Python SDK to provide file operations
    inside a persistent sandbox container. Virtual paths map to sandbox
    filesystem paths under /workspace.

    Security:
    - Path traversal is blocked (no `..`, no `~`)
    - Sandbox isolation provides process and filesystem containment
    """

    def __init__(
        self,
        base_url: str | None = None,
        image: str = "python:3.12-slim",
        default_timeout: int = 300,
        memory_limit: str = "512Mi",
        sandbox_id: str | None = None,
    ):
        """Initialize OpenSandbox backend.

        Args:
            base_url: OpenSandbox server URL (from settings if None)
            image: Docker image for sandbox
            default_timeout: Default operation timeout in seconds
            memory_limit: Memory limit (e.g., "512Mi")
            sandbox_id: Optional existing sandbox ID to reuse
        """
        config = settings.opensandbox
        self.base_url = base_url or config.base_url
        self.default_image = image or config.default_image
        self.default_timeout = default_timeout or config.timeout
        self.memory_limit = memory_limit or config.memory_limit

        self._sandbox: Sandbox | None = None
        self._sandbox_id: str | None = sandbox_id
        self._initialized = False
        self._cleanup_lock = asyncio.Lock()

    @property
    def id(self) -> str:
        """Unique identifier for the sandbox backend instance."""
        if self._sandbox is None:
            raise RuntimeError("Sandbox not initialized")
        return self._sandbox.id

    async def initialize(self) -> None:
        """Create and start the persistent sandbox."""
        if self._initialized:
            return

        # Use ConnectionConfig with use_server_proxy=True for containerized deployments
        connection_config = ConnectionConfig(
            domain=self.base_url,
            use_server_proxy=True,
        )

        self._sandbox = await Sandbox.create(
            image=self.default_image,
            timeout=timedelta(seconds=self.default_timeout),
            entrypoint=["tail", "-f", "/dev/null"],
            connection_config=connection_config,
            skip_health_check=True,
        )
        self._initialized = True
        logger.info(f"OpenSandboxBackend initialized with sandbox {self._sandbox.id}")

    async def cleanup(self) -> None:
        """Destroy the sandbox and release resources."""
        async with self._cleanup_lock:
            if self._sandbox is not None:
                try:
                    await self._sandbox.close()
                except Exception as e:
                    logger.warning(f"Error closing sandbox {self._sandbox.id}: {e}")
                self._sandbox = None
            self._initialized = False

    # -------------------------------------------------------------------------
    # Path resolution
    # -------------------------------------------------------------------------

    def _resolve_virtual_path(self, path: str) -> str:
        """Convert virtual path to sandbox filesystem path.

        Args:
            path: Virtual path like "/skills/xxx/SKILL.md"

        Returns:
            Absolute path inside sandbox like "/workspace/skills/xxx/SKILL.md"

        Raises:
            ValueError: If path traversal is detected
        """
        vpath = path if path.startswith("/") else "/" + path
        if ".." in vpath or vpath.startswith("~"):
            raise ValueError("Path traversal not allowed")
        clean_path = vpath.lstrip("/")
        return f"{VIRTUAL_ROOT}/{clean_path}"

    def _to_virtual_path(self, sandbox_path: str) -> str:
        """Convert sandbox filesystem path to virtual path."""
        if not sandbox_path.startswith(VIRTUAL_ROOT):
            raise ValueError(f"Path {sandbox_path} outside sandbox root")
        return "/" + sandbox_path[len(VIRTUAL_ROOT) + 1:]

    # -------------------------------------------------------------------------
    # Command execution
    # -------------------------------------------------------------------------

    async def aexecute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Execute a shell command inside the sandbox."""
        if not self._initialized:
            await self.initialize()

        if self._sandbox is None:
            return ExecuteResponse(output="Sandbox not initialized", exit_code=1)

        try:
            timeout_td = timedelta(seconds=timeout) if timeout else None
            result = await self._sandbox.commands.run(command)
            return ExecuteResponse(
                output=result.text,
                exit_code=result.exit_code,
                truncated=False,
            )
        except Exception as e:
            logger.error(f"Execute failed: {e}")
            return ExecuteResponse(output=str(e), exit_code=1)

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Execute a shell command inside the sandbox (sync)."""
        return asyncio.run(self.aexecute(command, timeout=timeout))

    # -------------------------------------------------------------------------
    # BackendProtocol implementation - file operations
    # -------------------------------------------------------------------------

    def ls(self, path: str) -> LsResult:
        """List files in directory."""
        return asyncio.run(self.als(path))

    async def als(self, path: str) -> LsResult:
        """Async implementation of ls."""
        if not self._initialized:
            await self.initialize()

        sandbox_path = self._resolve_virtual_path(path)

        try:
            # Use exec to run ls
            result = await self._sandbox.commands.run(f"ls -la '{sandbox_path}' 2>/dev/null || echo 'NOT_FOUND'")
            output = result.text

            if "NOT_FOUND" in output:
                return LsResult(error=f"Directory '{path}' not found")

            entries = self._parse_ls_output(output)
            return LsResult(entries=entries)
        except Exception as e:
            return LsResult(error=str(e))

    def ls_info(self, path: str) -> list[FileInfo]:
        """List file info in directory."""
        return asyncio.run(self.als_info(path))

    async def als_info(self, path: str) -> list[FileInfo]:
        """Async implementation of ls_info."""
        result = await self.als(path)
        return result.entries if result.entries is not None else []

    def _parse_ls_output(self, output: str) -> list[FileInfo]:
        """Parse `ls -la` output into FileInfo entries."""
        entries = []
        lines = output.strip().split("\n")

        for line in lines[1:]:  # Skip "total" line
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 8:
                continue

            perms = parts[0]
            size = int(parts[4]) if parts[4].isdigit() else 0
            date_str = " ".join(parts[5:8])
            name = " ".join(parts[8:])
            if not name:
                continue

            is_dir = perms.startswith("d")
            if is_dir and name.endswith("/"):
                name = name[:-1]
            name_path = "/" + name.lstrip("/")

            entries.append(FileInfo(
                path=name_path,
                is_dir=is_dir,
                size=size,
                modified_at=date_str,
            ))

        return entries

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult:
        """Read file content."""
        return asyncio.run(self.aread(file_path, offset, limit))

    async def aread(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult:
        """Async implementation of read."""
        if not self._initialized:
            await self.initialize()

        sandbox_path = self._resolve_virtual_path(file_path)

        try:
            content = await self._sandbox.files.read_file(sandbox_path)

            # Handle offset/limit via exec
            if offset > 0 or limit < 2000:
                cmd = f"sed -n '{offset+1},{offset+limit}p' '{sandbox_path}' 2>/dev/null"
                result = await self._sandbox.commands.run(cmd)
                content = result.text

            return ReadResult(file_data=FileData(content=content, encoding="utf-8"))
        except Exception as e:
            return ReadResult(error=str(e))

    def write(self, file_path: str, content: str) -> WriteResult:
        """Write content to a new file."""
        return asyncio.run(self.awrite(file_path, content))

    async def awrite(self, file_path: str, content: str) -> WriteResult:
        """Async implementation of write."""
        if not self._initialized:
            await self.initialize()

        sandbox_path = self._resolve_virtual_path(file_path)

        try:
            # Ensure parent directory exists
            parent = str(Path(sandbox_path).parent)
            if parent and parent != "/":
                await self._sandbox.commands.run(f"mkdir -p '{parent}'")

            await self._sandbox.files.write_file(sandbox_path, content)
            return WriteResult(path=file_path)
        except Exception as e:
            return WriteResult(error=str(e))

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        """Edit file content."""
        return asyncio.run(self.aedit(file_path, old_string, new_string, replace_all))

    async def aedit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        """Async implementation of edit."""
        if not self._initialized:
            await self.initialize()

        sandbox_path = self._resolve_virtual_path(file_path)

        try:
            content = await self._sandbox.files.read_file(sandbox_path)

            old_normalized = old_string.replace("\r\n", "\n").replace("\r", "\n")
            new_normalized = new_string.replace("\r\n", "\n").replace("\r", "\n")

            if replace_all:
                if old_normalized not in content:
                    return EditResult(error=f"String '{old_string}' not found in file")
                new_content = content.replace(old_normalized, new_normalized)
                occurrences = content.count(old_normalized)
            else:
                if old_normalized not in content:
                    return EditResult(error=f"String '{old_string}' not found in file")
                count = content.count(old_normalized)
                if count > 1:
                    return EditResult(error=f"Multiple ({count}) occurrences of '{old_string}' found. Use replace_all=True.")
                new_content = content.replace(old_normalized, new_normalized, 1)
                occurrences = 1

            await self._sandbox.files.write_file(sandbox_path, new_content)
            return EditResult(path=file_path, occurrences=occurrences)
        except Exception as e:
            return EditResult(error=str(e))

    def grep(self, pattern: str, path: str | None = None, glob: str | None = None) -> GrepResult:
        """Search for pattern in files."""
        return asyncio.run(self.agrep(pattern, path, glob))

    async def agrep(self, pattern: str, path: str | None = None, glob: str | None = None) -> GrepResult:
        """Async implementation of grep."""
        if not self._initialized:
            await self.initialize()

        search_path = self._resolve_virtual_path(path or "/")

        try:
            # Use grep command
            if glob:
                cmd = f"grep -rHnF '{pattern}' '{search_path}' --include='{glob}' 2>/dev/null || echo ''"
            else:
                cmd = f"grep -rHnF '{pattern}' '{search_path}' 2>/dev/null || echo ''"

            result = await self._sandbox.commands.run(cmd)
            output = result.text

            if not output.strip():
                return GrepResult(matches=[])

            matches = []
            for line in output.strip().split("\n"):
                if not line:
                    continue
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    try:
                        line_num = int(parts[1])
                    except ValueError:
                        continue
                    text = parts[2]
                    full_path = parts[0]
                    virt_path = self._to_virtual_path(full_path)
                    matches.append(GrepMatch(path=virt_path, line=line_num, text=text))

            return GrepResult(matches=matches)
        except Exception as e:
            return GrepResult(error=str(e))

    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        """Raw grep returning matches or raw output."""
        return asyncio.run(self.agrep_raw(pattern, path, glob))

    async def agrep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        """Async implementation of grep_raw."""
        result = await self.agrep(pattern, path, glob)
        if result.error:
            return result.error
        return result.matches if result.matches else []

    def glob(self, pattern: str, path: str = "/") -> GlobResult:
        """Find files matching glob pattern."""
        return asyncio.run(self.aglob(pattern, path))

    async def aglob(self, pattern: str, path: str = "/") -> GlobResult:
        """Async implementation of glob."""
        if not self._initialized:
            await self.initialize()

        search_path = self._resolve_virtual_path(path)

        try:
            # Convert glob pattern to find expression
            find_pattern = pattern.replace("**/", "**/").replace("**", "**")
            search_entry = SearchEntry(
                path=search_path,
                pattern=find_pattern,
                recursive=True,
            )
            results = await self._sandbox.files.search(entry=search_entry)

            matches = []
            for entry in results:
                virt_path = self._to_virtual_path(entry.path)
                matches.append(FileInfo(
                    path=virt_path,
                    is_dir=False,
                    size=entry.size,
                    modified_at=entry.modified_at.isoformat() if entry.modified_at else "",
                ))

            return GlobResult(matches=matches)
        except Exception as e:
            return GlobResult(error=str(e))

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Find files matching glob pattern, returning FileInfo list."""
        return asyncio.run(self.aglob_info(pattern, path))

    async def aglob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Async implementation of glob_info."""
        result = await self.aglob(pattern, path)
        return result.matches if result.matches else []

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload files to sandbox."""
        return asyncio.run(self.aupload_files(files))

    async def aupload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Async implementation of upload_files."""
        responses = []

        for file_path, content in files:
            try:
                sandbox_path = self._resolve_virtual_path(file_path)
                parent = str(Path(sandbox_path).parent)
                if parent and parent != "/":
                    await self._sandbox.commands.run(f"mkdir -p '{parent}'")
                await self._sandbox.files.write_file(sandbox_path, content)
                responses.append(FileUploadResponse(path=file_path, error=None))
            except Exception as e:
                responses.append(FileUploadResponse(path=file_path, error="invalid_path"))

        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download files from sandbox."""
        return asyncio.run(self.adownload_files(paths))

    async def adownload_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Async implementation of download_files."""
        responses = []

        for file_path in paths:
            try:
                sandbox_path = self._resolve_virtual_path(file_path)
                content = await self._sandbox.files.read_file(sandbox_path)
                responses.append(FileDownloadResponse(
                    path=file_path,
                    content=content.encode("utf-8"),
                    error=None,
                ))
            except Exception as e:
                responses.append(FileDownloadResponse(path=file_path, content=None, error="file_not_found"))

        return responses


class OpenSandboxBackendFactory:
    """Factory for creating OpenSandboxBackend instances."""

    def __init__(
        self,
        base_url: str | None = None,
        image: str = "python:3.12-slim",
        default_timeout: int = 300,
        memory_limit: str = "512Mi",
    ):
        self.base_url = base_url
        self.image = image
        self.default_timeout = default_timeout
        self.memory_limit = memory_limit

    def __call__(self, runtime: Any = None) -> OpenSandboxBackend:
        """Create a new OpenSandboxBackend instance."""
        return OpenSandboxBackend(
            base_url=self.base_url,
            image=self.image,
            default_timeout=self.default_timeout,
            memory_limit=self.memory_limit,
        )