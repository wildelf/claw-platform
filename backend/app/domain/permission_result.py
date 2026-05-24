"""Permission evaluation result entity."""

from dataclasses import dataclass
from typing import Optional

from app.domain.base import EntityId
from app.domain.permission_audit_log import EvaluatorType
from app.domain.permission_rule import RiskLevel
from app.domain.permission_audit_log import PermissionDecision


@dataclass
class PermissionEvaluationResult:
    """Result of a permission evaluation."""
    allowed: bool
    risk_level: RiskLevel
    decision: PermissionDecision
    evaluator: EvaluatorType
    matched_rule_id: Optional[EntityId] = None
    reasoning: str = ""
    latency_ms: int = 0
    override_request_id: Optional[EntityId] = None
