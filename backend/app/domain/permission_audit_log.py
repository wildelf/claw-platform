"""Permission audit log domain entity."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.domain.base import EntityId


class PermissionDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class EvaluatorType(str, Enum):
    RISK_CLASSIFIER = "RISK_CLASSIFIER"
    RULE_MATCHER = "RULE_MATCHER"
    REASONING_JUDGE = "REASONING_JUDGE"


@dataclass
class PermissionAuditLog:
    """Permission audit log entity."""
    employee_id: EntityId
    agent_id: EntityId
    tool_name: str
    tool_input: str
    risk_level: str
    decision: PermissionDecision
    evaluator: EvaluatorType
    matched_rule_id: Optional[EntityId] = None
    reasoning: str = ""
    latency_ms: int = 0
    id: Optional[EntityId] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = EntityId.generate()
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
