"""Storage adapters."""

from app.infrastructure.storage.base import StorageAdapter
from app.infrastructure.storage.sqlite import SQLiteStorage

__all__ = ["StorageAdapter", "SQLiteStorage"]
