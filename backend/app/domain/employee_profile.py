"""Employee Profile domain model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.domain.base import EntityId


@dataclass
class EmployeeProfile:
    """Employee profile entity."""
    name: str
    role: str = ""
    goal: str = ""
    backstory: str = ""
    personality: str = ""
    constraints: str = ""
    working_rules: str = ""
    status: str = "active"
    git_path: str = ""
    user_id: Optional[EntityId] = None
    id: Optional[EntityId] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = EntityId.generate()
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def to_summary(self) -> dict:
        """Return a summary dict for list views."""
        return {
            "id": str(self.id),
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "status": self.status,
            "git_path": self.git_path,
        }

    def to_dict(self) -> dict:
        """Return full dict."""
        return {
            "id": str(self.id),
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
            "personality": self.personality,
            "constraints": self.constraints,
            "working_rules": self.working_rules,
            "status": self.status,
            "git_path": self.git_path,
            "user_id": str(self.user_id) if self.user_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
