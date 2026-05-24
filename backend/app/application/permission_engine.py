"""Permission engine: 4-layer evaluation (RiskClassifier + RuleMatcher + ReasoningJudge + AuditLogger)."""

import asyncio
import json
import logging
import re
import time
from typing import List, Optional

from app.domain.base import EntityId
from app.domain.permission_audit_log import EvaluatorType, PermissionDecision
from app.domain.permission_override_request import PermissionOverrideRequest
from app.domain.permission_result import PermissionEvaluationResult
from app.domain.permission_rule import PermissionRule, RiskLevel, RuleAction
from app.infrastructure.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class RiskClassifier:
    """Layer 1: Fast risk classification based on tool_name and tool_input."""

    TOOL_RISK_MAP = {
        # safe
        "read_file": RiskLevel.SAFE,
        "Calculator": RiskLevel.SAFE,
        "web_search": RiskLevel.SAFE,
        "arxiv": RiskLevel.SAFE,
        # low
        "write_file": RiskLevel.LOW,
        "generate_image": RiskLevel.LOW,
        # medium
        "execute_script": RiskLevel.MEDIUM,
        # high
        "bash": RiskLevel.HIGH,
        "shell": RiskLevel.HIGH,
    }

    ESCALATION_PATTERNS = [
        (r"rm\s+-rf", RiskLevel.CRITICAL),
        (r"mkfs|dd\s+if=|chmod\s+777", RiskLevel.CRITICAL),
        (r"\.(env|key|pem|credentials)", RiskLevel.HIGH),
        (r"prod|production|live", RiskLevel.HIGH),
        (r"DROP\s+|DELETE\s+FROM|TRUNCATE", RiskLevel.CRITICAL),
        (r"\.(yaml|yml|json|toml|ini)$", RiskLevel.MEDIUM),
    ]

    RISK_ORDER = {
        RiskLevel.SAFE: 0,
        RiskLevel.LOW: 1,
        RiskLevel.MEDIUM: 2,
        RiskLevel.HIGH: 3,
        RiskLevel.CRITICAL: 4,
    }

    def classify(self, tool_name: str, tool_input: str) -> RiskLevel:
        """
        Classify risk level. Returns the highest applicable level.
        1. Look up baseline from TOOL_RISK_MAP
        2. Scan tool_input for escalation patterns
        3. Return max(baseline, escalation)
        """
        baseline = self.TOOL_RISK_MAP.get(tool_name, RiskLevel.MEDIUM)

        max_level = baseline
        for pattern, level in self.ESCALATION_PATTERNS:
            if re.search(pattern, tool_input, re.IGNORECASE):
                if self.RISK_ORDER.get(level, 0) > self.RISK_ORDER.get(max_level, 0):
                    max_level = level

        return max_level


class PermissionEngine:
    """
    4-layer permission evaluation engine.

    Layer 1: RiskClassifier - fast risk classification
    Layer 2: RuleMatcher - regex rule matching (fast path)
    Layer 3: ReasoningJudge - LLM-based reasoning (slow path)
    Layer 4: AuditLogger - decision logging + override creation
    """

    REASONING_JUDGE_TIMEOUT = 5.0  # seconds

    def __init__(
        self,
        storage: SQLiteStorage,
        rule_service=None,
        override_service=None,
        risk_classifier: RiskClassifier | None = None,
    ):
        self.storage = storage
        self.rule_service = rule_service
        self.override_service = override_service
        self.risk_classifier = risk_classifier or RiskClassifier()
        self._rules_cache: List[PermissionRule] = []
        self._rules_cache_loaded = False

    def _serialize_input(self, tool_input: dict | str) -> str:
        """Serialize tool input to string for pattern matching."""
        if isinstance(tool_input, str):
            return tool_input
        return json.dumps(tool_input, ensure_ascii=False)

    async def _load_rules(self) -> List[PermissionRule]:
        """Load active rules from service, caching for performance."""
        if self.rule_service:
            self._rules_cache = await self.rule_service.load_active_rules()
            self._rules_cache_loaded = True
        return self._rules_cache

    def _match_rules(
        self, rules: List[PermissionRule],
        tool_name: str, tool_input: str,
        employee_id: str
    ) -> Optional[PermissionRule]:
        """
        Match rules in priority order (highest first).
        Employee-specific rules take priority over global rules.
        """
        employee_rules = [r for r in rules if str(r.employee_id) == employee_id and r.enabled]
        global_rules = [r for r in rules if r.employee_id is None and r.enabled]
        candidate_rules = sorted(employee_rules, key=lambda r: r.priority, reverse=True) + \
                          sorted(global_rules, key=lambda r: r.priority, reverse=True)

        for rule in candidate_rules:
            if rule.matches(tool_name, tool_input):
                return rule
        return None

    async def _maybe_create_override(
        self, result: PermissionEvaluationResult,
        employee_id: str, agent_id: str,
        tool_name: str, tool_input: str,
        risk_level: RiskLevel,
    ) -> PermissionEvaluationResult:
        """Create an override request when action is DENY and override is possible."""
        if self.override_service and risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            try:
                req = await self.override_service.create_request(
                    employee_id=employee_id,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    tool_input=tool_input[:2000],
                    risk_level=risk_level.value,
                    reason=f"Auto-created: {result.reasoning}",
                    requested_by=employee_id,
                )
                result.override_request_id = req.id
            except Exception as e:
                logger.error(f"Failed to create override request: {e}")
        return result

    async def _log_audit(
        self,
        result: PermissionEvaluationResult,
        employee_id: str,
        agent_id: str,
        tool_name: str,
        tool_input: str,
        start_time: float,
    ) -> None:
        """Fire-and-forget audit log write."""
        from app.domain.permission_audit_log import PermissionAuditLog
        latency_ms = int((time.monotonic() - start_time) * 1000)
        audit_log = PermissionAuditLog(
            employee_id=EntityId(employee_id),
            agent_id=EntityId(agent_id),
            tool_name=tool_name,
            tool_input=tool_input[:2000],
            risk_level=result.risk_level.value if hasattr(result.risk_level, 'value') else str(result.risk_level),
            decision=result.decision,
            evaluator=result.evaluator,
            matched_rule_id=result.matched_rule_id,
            reasoning=result.reasoning[:2000],
            latency_ms=latency_ms,
        )
        try:
            await self.storage.save_audit_log(audit_log)
        except Exception as e:
            logger.error(f"Audit log write failed (non-critical): {e}")

    async def _reasoning_judge_evaluate(
        self,
        tool_name: str,
        tool_input: str,
        risk_level: RiskLevel,
        employee_id: str,
        agent_id: str,
        context: dict | None,
        start_time: float,
    ) -> PermissionEvaluationResult:
        """
        Evaluate with LLM reasoning (Layer 3).
        Falls back to DENY on timeout or error.
        """
        # For now, default to DENY as safe fallback since we don't have LLM configured
        # In production, this would call an LLM endpoint
        logger.info(
            f"ReasoningJudge evaluation for tool '{tool_name}' "
            f"(risk={risk_level.value}, no LLM configured - safe DENY)"
        )
        return PermissionEvaluationResult(
            allowed=False,
            risk_level=risk_level,
            decision=PermissionDecision.DENY,
            evaluator=EvaluatorType.REASONING_JUDGE,
            reasoning=f"No matching rule found. LLM evaluation not configured - safe fallback DENY for {tool_name}.",
        )

    async def evaluate_action(
        self,
        tool_name: str,
        tool_input: dict | str,
        employee_id: str,
        agent_id: str,
        context: dict | None = None,
    ) -> PermissionEvaluationResult:
        """
        Main evaluation entry point. Runs the 4-layer pipeline.
        """
        start_time = time.monotonic()
        tool_input_str = self._serialize_input(tool_input)

        # Layer 1: Risk Classification
        risk_level = self.risk_classifier.classify(tool_name, tool_input_str)

        # Fast path: safe/low tools auto-allowed
        if risk_level in (RiskLevel.SAFE, RiskLevel.LOW):
            result = PermissionEvaluationResult(
                allowed=True,
                risk_level=risk_level,
                decision=PermissionDecision.ALLOW,
                evaluator=EvaluatorType.RISK_CLASSIFIER,
                reasoning=f"Risk classifier: {risk_level.value} - auto-allowed",
            )
            await self._log_audit(result, employee_id, agent_id, tool_name, tool_input_str, start_time)
            return result

        # Check for active override (bypass for approved requests)
        if self.override_service and await self.override_service.is_override_active(employee_id, agent_id, tool_name):
            result = PermissionEvaluationResult(
                allowed=True,
                risk_level=risk_level,
                decision=PermissionDecision.ALLOW,
                evaluator=EvaluatorType.RISK_CLASSIFIER,
                reasoning="Active override request approved",
            )
            await self._log_audit(result, employee_id, agent_id, tool_name, tool_input_str, start_time)
            return result

        # Layer 2: Rule Matching (fast path for medium+)
        rules = await self._load_rules()
        matched_rule = self._match_rules(rules, tool_name, tool_input_str, employee_id)

        if matched_rule:
            decision = PermissionDecision(matched_rule.action)
            allowed = decision == PermissionDecision.ALLOW
            result = PermissionEvaluationResult(
                allowed=allowed,
                risk_level=risk_level,
                decision=decision,
                evaluator=EvaluatorType.RULE_MATCHER,
                matched_rule_id=matched_rule.id,
                reasoning=f"Matched rule '{matched_rule.name}': {matched_rule.action.value if hasattr(matched_rule.action, 'value') else matched_rule.action}",
            )

            # If DENY and override possible, create override request
            if decision == PermissionDecision.DENY and risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                result = await self._maybe_create_override(
                    result, employee_id, agent_id, tool_name, tool_input_str, risk_level
                )

            await self._log_audit(result, employee_id, agent_id, tool_name, tool_input_str, start_time)
            return result

        # Layer 3: Reasoning Judge (slow path - LLM)
        result = await self._reasoning_judge_evaluate(
            tool_name, tool_input_str, risk_level, employee_id, agent_id, context, start_time
        )

        # Layer 4: Audit log (always)
        await self._log_audit(result, employee_id, agent_id, tool_name, tool_input_str, start_time)
        return result
