"""Permission rule domain entity."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.domain.base import EntityId


class RuleCategory(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    NETWORK = "NETWORK"
    PRODUCTION = "PRODUCTION"


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleAction(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass
class PermissionRule:
    """Permission rule entity."""
    name: str
    category: RuleCategory
    risk_level: RiskLevel
    pattern: str
    action: RuleAction
    description: str = ""
    priority: int = 5
    enabled: bool = True
    employee_id: Optional[EntityId] = None
    git_path: str = ""
    created_by: Optional[EntityId] = None
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

    def matches(self, tool_name: str, tool_input: str) -> bool:
        """Check if this rule matches the given tool call."""
        if not self.enabled:
            return False
        try:
            combined = f"{tool_name}:{tool_input}"
            return bool(re.search(self.pattern, combined, re.IGNORECASE))
        except re.error:
            return False
