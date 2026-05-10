import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FileStorage:
    """文件系统存储工具"""

    @staticmethod
    def ensure_dir(path: Path) -> None:
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def write(path: Path, content: str, append: bool = False) -> None:
        """写入文件"""
        if append and path.exists():
            path.write_text(path.read_text() + "\n" + content)
        else:
            path.write_text(content)

    @staticmethod
    def read(path: Path) -> str:
        """读取文件"""
        if path.exists():
            return path.read_text()
        return ""

    @staticmethod
    def delete(path: Path) -> bool:
        """删除文件"""
        if path.exists():
            path.unlink()
            return True
        return False

    @staticmethod
    def list_files(dir_path: Path, pattern: str = "*") -> list[Path]:
        """列出目录下文件"""
        if dir_path.exists():
            return list(dir_path.glob(pattern))
        return []