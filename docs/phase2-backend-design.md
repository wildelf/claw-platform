# Phase 2 Backend Design: Dual-Layer Permission Verification

## 1. Overview

This document describes the backend implementation for Phase 2: Dual-Layer Permission Verification. It replaces the binary `PermissionController` with a 4-layer `PermissionEngine` that classifies risk, matches rules, applies LLM reasoning, and logs all decisions.

### 1.1 Goals

| Goal | Target |
|------|--------|
| Replace binary allow/deny with 5-level risk classification | safe / low / medium / high / critical |
| Dual-layer evaluation (RuleMatcher + ReasoningJudge) | Fast path < 50ms for safe ops |
| Full audit trail for every permission decision | 100% coverage |
| Override request + approval workflow | Admin approval with 24h expiry |
| Built-in tools no longer bypass permission checks | All tools evaluated |

### 1.2 Architecture

```
Tool Call (tool_name, tool_input, employee_id)
         ↓
┌──────────────────────────────────────┐
│  Layer 1: Risk Classifier            │
│  - Classify by tool_name + input     │
│  - safe/low → fast ALLOW             │
│  - medium+ → continue                │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│  Layer 2: RuleMatcher (Fast Path)    │
│  - Regex matching on tool_input      │
│  - Employee constraint check         │
│  - Match → ALLOW / DENY              │
│  - No Match → continue               │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│  Layer 3: ReasoningJudge (Slow Path) │
│  - LLM evaluates action context      │
│  - Returns ALLOW / DENY + reasoning  │
│  - Timeout (5s) → DENY (safe fail)   │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│  Layer 4: Audit Logger               │
│  - Log decision, evaluator, timing   │
│  - DENY + override → create request  │
└──────────────────────────────────────┘
```

### 1.3 Key Design Decisions

- **Git-backed storage for PermissionRule** follows the same dual-persistence pattern as `EmployeeProfileService` (Git primary + SQLite sync).
- **SQLite-only storage** for `PermissionAuditLog` and `PermissionOverrideRequest` (fire-and-forget write, no Git needed).
- **Reuse existing patterns**: `RuleMatcher` (regex) and `ReasoningJudge` (LLM) from the nudge system are adapted for permission evaluation with custom prompts and patterns.
- **Soft delete** for rules (`enabled=false`) preserves audit trail integrity.

---

## 2. Data Models (SQLAlchemy)

New models added to `backend/app/infrastructure/storage/sqlite.py`:

### 2.1 PermissionRuleModel

```python
class PermissionRuleModel(Base):
    __tablename__ = "permission_rules"
    __table_args__ = (
        Index("ix_permission_rules_employee_id", "employee_id"),
        Index("ix_permission_rules_priority", "priority", desc=True),
        Index("ix_permission_rules_enabled", "enabled"),
    )

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000), default="")
    category = Column(String(30), nullable=False)        # READ, WRITE, DELETE, EXECUTE, NETWORK, PRODUCTION
    risk_level = Column(String(20), nullable=False)      # safe, low, medium, high, critical
    pattern = Column(String(500), nullable=False)        # regex pattern
    action = Column(String(20), nullable=False)          # ALLOW, DENY, REQUIRE_APPROVAL
    priority = Column(Integer, default=5)                # 1-10, higher = checked first
    enabled = Column(Boolean, default=True)
    employee_id = Column(String(36), nullable=True)      # None = global rule
    git_path = Column(String(500), default="")
    created_by = Column(String(36), nullable=False)      # user_id
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```

### 2.2 PermissionAuditLogModel

```python
class PermissionAuditLogModel(Base):
    __tablename__ = "permission_audit_logs"
    __table_args__ = (
        Index("ix_audit_employee_id", "employee_id"),
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_decision", "decision"),
        Index("ix_audit_risk_level", "risk_level"),
    )

    id = Column(String(36), primary_key=True)
    employee_id = Column(String(36), nullable=False)
    agent_id = Column(String(36), nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_input = Column(Text, nullable=False)            # truncated to 2000 chars
    risk_level = Column(String(20), nullable=False)
    decision = Column(String(20), nullable=False)        # ALLOW, DENY, REQUIRE_APPROVAL
    evaluator = Column(String(30), nullable=False)       # RULE_MATCHER, REASONING_JUDGE, RISK_CLASSIFIER
    matched_rule_id = Column(String(36), nullable=True)
    reasoning = Column(String(2000), default="")
    latency_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, nullable=False)
```

### 2.3 PermissionOverrideRequestModel

```python
class PermissionOverrideRequestModel(Base):
    __tablename__ = "permission_override_requests"
    __table_args__ = (
        Index("ix_override_employee_id", "employee_id"),
        Index("ix_override_status", "status"),
        Index("ix_override_expires_at", "expires_at"),
    )

    id = Column(String(36), primary_key=True)
    employee_id = Column(String(36), nullable=False)
    agent_id = Column(String(36), nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_input = Column(Text, nullable=False)            # truncated
    risk_level = Column(String(20), nullable=False)      # high, critical
    reason = Column(String(2000), nullable=False)
    requested_by = Column(String(36), nullable=False)    # user_id
    requested_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="PENDING")       # PENDING, APPROVED, REJECTED, EXPIRED
    approved_by = Column(String(36), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(1000), nullable=True)
    expires_at = Column(DateTime, nullable=True)
```

### 2.4 SQLiteStorage New Methods

```python
class SQLiteStorage:
    # PermissionRule operations
    async def save_permission_rule(self, rule: PermissionRule) -> None
    async def get_permission_rule(self, id: str) -> Optional[PermissionRule]
    async def list_permission_rules(self, employee_id: str | None = None,
                                     enabled: bool | None = None,
                                     offset: int = 0, limit: int = 100) -> List[PermissionRule]
    async def delete_permission_rule(self, id: str) -> None
    async def list_permission_rules_by_priority(self) -> List[PermissionRule]

    # PermissionAuditLog operations
    async def save_audit_log(self, log: PermissionAuditLog) -> None
    async def query_audit_logs(self, employee_id: str | None = None,
                                decision: str | None = None,
                                risk_level: str | None = None,
                                offset: int = 0, limit: int = 100) -> List[PermissionAuditLog]
    async def get_audit_log_stats(self, days: int = 7) -> dict

    # PermissionOverrideRequest operations
    async def save_override_request(self, req: PermissionOverrideRequest) -> None
    async def get_override_request(self, id: str) -> Optional[PermissionOverrideRequest]
    async def list_override_requests(self, employee_id: str | None = None,
                                      status: str | None = None,
                                      offset: int = 0, limit: int = 100) -> List[PermissionOverrideRequest]
    async def update_override_request(self, id: str, data: dict) -> Optional[PermissionOverrideRequest]
    async def expire_overdue_overrides(self) -> int  # batch expire where expires_at < now
```

### 2.5 Domain Entity Conversions

Each model gets a `_to_*` converter method following existing patterns (`_to_agent`, `_to_skill`, etc.):

```python
def _to_permission_rule(self, row: PermissionRuleModel) -> PermissionRule
def _to_audit_log(self, row: PermissionAuditLogModel) -> PermissionAuditLog
def _to_override_request(self, row: PermissionOverrideRequestModel) -> PermissionOverrideRequest
```

---

## 3. Domain Entities

### 3.1 PermissionRule

Location: `backend/app/domain/permission_rule.py`

```python
@dataclass
class PermissionRule:
    name: str
    category: RuleCategory              # Enum: READ, WRITE, DELETE, EXECUTE, NETWORK, PRODUCTION
    risk_level: RiskLevel               # Enum: SAFE, LOW, MEDIUM, HIGH, CRITICAL
    pattern: str                        # regex
    action: RuleAction                  # Enum: ALLOW, DENY, REQUIRE_APPROVAL
    description: str = ""
    priority: int = 5                   # 1-10
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

    def matches(self, tool_name: str, tool_input: str) -> bool
        """Check if this rule matches the given tool call."""
```

Enums:

```python
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
```

### 3.2 PermissionAuditLog

Location: `backend/app/domain/permission_audit_log.py`

```python
@dataclass
class PermissionAuditLog:
    employee_id: EntityId
    agent_id: EntityId
    tool_name: str
    tool_input: str                       # truncated to 2000 chars
    risk_level: RiskLevel
    decision: PermissionDecision          # ALLOW, DENY, REQUIRE_APPROVAL
    evaluator: EvaluatorType              # RULE_MATCHER, REASONING_JUDGE, RISK_CLASSIFIER
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
```

### 3.3 PermissionOverrideRequest

Location: `backend/app/domain/permission_override_request.py`

```python
@dataclass
class PermissionOverrideRequest:
    employee_id: EntityId
    agent_id: EntityId
    tool_name: str
    tool_input: str
    risk_level: RiskLevel                 # high or critical only
    reason: str
    requested_by: EntityId
    id: Optional[EntityId] = None
    requested_at: Optional[datetime] = None
    status: OverrideStatus = OverrideStatus.PENDING
    approved_by: Optional[EntityId] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = EntityId.generate()
        now = datetime.now(timezone.utc)
        if self.requested_at is None:
            self.requested_at = now

    @property
    def is_expired(self) -> bool
        """Check if this override has expired."""

    @property
    def is_active(self) -> bool
        """Check if this override is currently valid (approved and not expired)."""
```

Enums:

```python
class PermissionDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"

class EvaluatorType(str, Enum):
    RISK_CLASSIFIER = "RISK_CLASSIFIER"
    RULE_MATCHER = "RULE_MATCHER"
    REASONING_JUDGE = "REASONING_JUDGE"

class OverrideStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
```

### 3.4 PermissionEvaluationResult

Location: `backend/app/domain/permission_result.py`

```python
@dataclass
class PermissionEvaluationResult:
    allowed: bool
    risk_level: RiskLevel
    decision: PermissionDecision
    evaluator: EvaluatorType
    matched_rule_id: Optional[EntityId] = None
    reasoning: str = ""
    latency_ms: int = 0
    override_request_id: Optional[EntityId] = None
```

---

## 4. Service Layer

### 4.1 PermissionRuleService

Location: `backend/app/application/permission_rule_service.py`

Follows the `EmployeeProfileService` pattern with dual persistence (Git + SQLite):

```python
class PermissionRuleService:
    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    def _get_rule_dir(self, rule: PermissionRule) -> Path
        """Get the git-managed directory for a rule."""
        rules_root = Path(settings.permission_rules_root).expanduser()  # e.g., ~/.claw/permission-rules
        return rules_root / str(rule.id)

    async def create(self, rule: PermissionRule) -> PermissionRule
        """Create rule: write to Git (rule.json) + sync to SQLite."""

    async def get(self, rule_id: str) -> Optional[PermissionRule]
        """Get rule by ID."""

    async def list(self, employee_id: str | None = None,
                   enabled: bool | None = None) -> List[PermissionRule]
        """List rules with optional filters."""

    async def update(self, rule_id: str, data: dict) -> Optional[PermissionRule]
        """Update rule: write to Git + sync to SQLite."""

    async def delete(self, rule_id: str) -> bool
        """Soft delete: set enabled=false."""

    async def toggle(self, rule_id: str) -> Optional[PermissionRule]
        """Toggle rule enabled/disabled."""

    async def load_active_rules(self) -> List[PermissionRule]
        """Load all enabled rules, sorted by priority (highest first)."""

    def _generate_rule_json(self, rule: PermissionRule) -> str
        """Generate rule.json content for Git storage."""
```

Config addition:

```python
# In Settings class (backend/app/config.py):
permission_rules_root: str = "~/.claw/permission-rules"
```

### 4.2 OverrideService

Location: `backend/app/application/override_service.py`

```python
class OverrideService:
    OVERRIDE_TTL_HOURS = 24  # approved overrides valid for 24h

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create_request(self, employee_id: str, agent_id: str,
                              tool_name: str, tool_input: str,
                              risk_level: str, reason: str,
                              requested_by: str) -> PermissionOverrideRequest
        """Create a new override request."""

    async def approve(self, request_id: str, approved_by: str) -> Optional[PermissionOverrideRequest]
        """Approve an override request. Sets expires_at = now + 24h."""

    async def reject(self, request_id: str, approved_by: str,
                     rejection_reason: str) -> Optional[PermissionOverrideRequest]
        """Reject an override request."""

    async def get(self, request_id: str) -> Optional[PermissionOverrideRequest]
        """Get override request by ID."""

    async def list(self, employee_id: str | None = None,
                   status: str | None = None) -> List[PermissionOverrideRequest]
        """List override requests with optional filters."""

    async def is_override_active(self, employee_id: str, agent_id: str,
                                  tool_name: str) -> bool
        """Check if there is an active (approved, not expired) override for this tool."""

    async def expire_overdue(self) -> int
        """Batch expire all overrides past their expires_at."""
```

---

## 5. Permission Engine (Core Evaluation Logic)

Location: `backend/app/application/permission_engine.py`

This is the core component that replaces `PermissionController`.

### 5.1 Risk Classifier (Layer 1)

```python
class RiskClassifier:
    """Layer 1: Fast risk classification based on tool_name and tool_input."""

    # Tool-to-risk baseline mapping
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

    # Input patterns that escalate risk
    ESCALATION_PATTERNS = [
        (r"rm\s+-rf", RiskLevel.CRITICAL),
        (r"mkfs|dd\s+if=|chmod\s+777", RiskLevel.CRITICAL),
        (r"\.(env|key|pem|credentials)", RiskLevel.HIGH),
        (r"prod|production|live", RiskLevel.HIGH),
        (r"DROP\s+|DELETE\s+FROM|TRUNCATE", RiskLevel.CRITICAL),
        (r"\.(yaml|yml|json|toml|ini)$", RiskLevel.MEDIUM),  # config writes
    ]

    def classify(self, tool_name: str, tool_input: str) -> RiskLevel
        """
        Classify risk level. Returns the highest applicable level.
        1. Look up baseline from TOOL_RISK_MAP
        2. Scan tool_input for escalation patterns
        3. Return max(baseline, escalation)
        """
```

### 5.2 PermissionEngine (4-Layer Evaluator)

```python
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
        rule_service: PermissionRuleService,
        override_service: OverrideService,
        risk_classifier: RiskClassifier | None = None,
    ):
        self.storage = storage
        self.rule_service = rule_service
        self.override_service = override_service
        self.risk_classifier = risk_classifier or RiskClassifier()
        self._rules_cache: List[PermissionRule] = []
        self._rules_cache_loaded = False

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

        Returns PermissionEvaluationResult with allowed, risk_level, decision,
        evaluator, reasoning, latency_ms, and optional override_request_id.
        """
        start_time = time.monotonic()
        tool_input_str = self._serialize_input(tool_input)

        # Layer 1: Risk Classification
        risk_level = self.risk_classifier.classify(tool_name, tool_input_str)

        # Fast path: safe tools with no escalation
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
        if await self.override_service.is_override_active(employee_id, agent_id, tool_name):
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
                reasoning=f"Matched rule '{matched_rule.name}': {matched_rule.action}",
            )

            # If DENY and override possible, create override request
            if decision == PermissionDecision.DENY and risk_level in (RiskLevel.HIGH,):
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
```

### 5.3 Rule Matching Logic

```python
    def _match_rules(
        self, rules: List[PermissionRule],
        tool_name: str, tool_input: str,
        employee_id: str
    ) -> Optional[PermissionRule]:
        """
        Match rules in priority order (highest first).

        Priority:
        1. Employee-specific rules (employee_id match)
        2. Global rules (employee_id is None)

        Within each group, sort by priority (descending).
        First match wins.
        """
        # Partition and sort
        employee_rules = [r for r in rules if str(r.employee_id) == employee_id and r.enabled]
        global_rules = [r for r in rules if r.employee_id is None and r.enabled]
        candidate_rules = sorted(employee_rules, key=lambda r: r.priority, reverse=True) + \
                          sorted(global_rules, key=lambda r: r.priority, reverse=True)

        for rule in candidate_rules:
            if rule.matches(tool_name, tool_input):
                return rule
        return None
```

### 5.4 ReasoningJudge Adaptation

Adapt the existing `ReasoningJudge` from `backend/app/application/nudge/reasoning_judge.py` for permission evaluation:

```python
class PermissionReasoningJudge:
    """LLM-based permission decision engine (adapted from ReasoningJudge)."""

    SYSTEM_PROMPT = """You are a security expert evaluating whether an AI agent should be allowed to execute a tool call.

Evaluate the following factors:
1. Tool type and input content - is this a dangerous operation?
2. Risk context - does the command target production, secrets, or destructive operations?
3. Intent analysis - does the tool_input indicate legitimate work or potential harm?

Respond with JSON:
{
  "allowed": true/false,
  "reasoning": "One sentence explaining the decision",
  "confidence": "high/medium/low"
}"""

    USER_PROMPT = """Tool: {tool_name}
Input: {tool_input}
Risk Level: {risk_level}
Employee Role: {employee_role}
Context: {context}"""

    def __init__(self):
        self._client = None

    async def judge(
        self,
        tool_name: str,
        tool_input: str,
        risk_level: str,
        employee_role: str = "",
        context: str = "",
    ) -> PermissionEvaluationResult:
        """Evaluate tool call with LLM reasoning."""
        try:
            client = self._get_client()
            user_prompt = self.USER_PROMPT.format(
                tool_name=tool_name,
                tool_input=tool_input,
                risk_level=risk_level,
                employee_role=employee_role,
                context=context,
            )
            response = await asyncio.wait_for(
                client.ainvoke([
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ]),
                timeout=PermissionEngine.REASONING_JUDGE_TIMEOUT,
            )
            # Parse JSON response...
        except asyncio.TimeoutError:
            logger.warning("ReasoningJudge timeout, defaulting to DENY")
            return PermissionEvaluationResult(
                allowed=False,
                risk_level=RiskLevel(risk_level),
                decision=PermissionDecision.DENY,
                evaluator=EvaluatorType.REASONING_JUDGE,
                reasoning="LLM judgment timed out - safe fallback DENY",
            )
        except Exception as e:
            logger.error(f"ReasoningJudge failed: {e}")
            return PermissionEvaluationResult(
                allowed=False,
                risk_level=RiskLevel(risk_level),
                decision=PermissionDecision.DENY,
                evaluator=EvaluatorType.REASONING_JUDGE,
                reasoning=f"LLM judgment failed: {str(e)}",
            )
```

### 5.5 Audit Logger

```python
    async def _log_audit(
        self,
        result: PermissionEvaluationResult,
        employee_id: str,
        agent_id: str,
        tool_name: str,
        tool_input: str,
        start_time: float,
    ) -> None:
        """
        Fire-and-forget audit log write.
        Failures are logged but do not affect the permission decision.
        """
        latency_ms = int((time.monotonic() - start_time) * 1000)
        audit_log = PermissionAuditLog(
            employee_id=EntityId(employee_id),
            agent_id=EntityId(agent_id),
            tool_name=tool_name,
            tool_input=tool_input[:2000],  # truncate
            risk_level=result.risk_level,
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
```

---

## 6. Middleware Integration

### 6.1 Changes to SkillEventMiddleware.awrap_tool_call()

Location: `backend/app/deepagents/skills_middleware.py`

Replace the existing `PermissionController` check with `PermissionEngine`:

```python
# Before (Phase 1):
if self._agent and self._storage and not self._is_builtin_tool(tool_name):
    perm_controller = PermissionController(self._agent, self._storage)
    result = await perm_controller.is_tool_allowed(tool_name)
    if not result.allowed:
        raise PermissionDeniedError(tool_name=tool_name, agent_id=str(self._agent.id))

# After (Phase 2):
if self._agent and self._storage and self._permission_engine:
    result = await self._permission_engine.evaluate_action(
        tool_name=tool_name,
        tool_input=tool_input,
        employee_id=str(self._agent.user_id),  # or employee_id from context
        agent_id=str(self._agent.id),
        context={
            "working_directory": self._get_working_directory(),
        },
    )
    if not result.allowed:
        logger.warning(
            f"Permission denied for tool '{tool_name}': "
            f"{result.reasoning} (evaluator={result.evaluator.value}, "
            f"risk={result.risk_level.value})"
        )
        raise PermissionDeniedError(
            tool_name=tool_name,
            agent_id=str(self._agent.id),
            reason=result.reasoning,
            risk_level=result.risk_level.value,
        )
```

### 6.2 PermissionDeniedError Enhancement

Location: `backend/app/deepagents/exceptions.py`

Add optional fields to support the richer error context:

```python
class PermissionDeniedError(Exception):
    def __init__(
        self,
        tool_name: str,
        agent_id: str,
        reason: str | None = None,
        risk_level: str | None = None,
        override_request_id: str | None = None,
    ):
        self.tool_name = tool_name
        self.agent_id = agent_id
        self.reason = reason
        self.risk_level = risk_level
        self.override_request_id = override_request_id
        msg = f"Agent '{agent_id}' tried to call unauthorized tool '{tool_name}'"
        if reason:
            msg += f" - {reason}"
        super().__init__(msg)
```

### 6.3 Middleware Initialization

```python
class SkillEventMiddleware(BaseSkillsMiddleware):
    def __init__(self, *, backend, sources, event_handler=None,
                 agent=None, storage=None, permission_engine=None):
        super().__init__(backend=backend, sources=sources)
        self._event_handler = event_handler
        self._agent = agent
        self._storage = storage
        self._permission_engine = permission_engine  # NEW: injected PermissionEngine
```

---

## 7. Default Seed Rules

On first initialization, the system automatically creates the following rules. They are stored via Git + SQLite (same as user-created rules) and can be modified by admins.

| # | Name | Category | Pattern | Action | Risk | Priority |
|---|------|----------|---------|--------|------|----------|
| 1 | Safe file read | READ | `.*` | ALLOW | safe | 1 |
| 2 | Secret file access | READ | `\.(env\|key\|pem\|credentials)$` | DENY | high | 9 |
| 3 | Config file write | WRITE | `\.(yaml\|yml\|json\|toml\|ini)$` | ALLOW | low | 3 |
| 4 | Delete detection | DELETE | `(rm\|rmdir\|unlink\|DROP\|DELETE FROM)` | DENY | high | 9 |
| 5 | Dangerous bash | EXECUTE | `(rm\s+-rf\|mkfs\|dd\s+if=\|chmod\s+777)` | DENY | critical | 10 |
| 6 | Production access | PRODUCTION | `(prod\|production\|live)` in path context | REQUIRE_APPROVAL | high | 8 |
| 7 | Network allowlist | NETWORK | `^(https?://api\.allowed-domain\.com/)` | ALLOW | low | 2 |
| 8 | Script execution | EXECUTE | `\.(sh\|py\|js\|rb)$` executed via bash | ALLOW | medium | 4 |

Seed logic location: `backend/app/application/permission_rule_service.py`

```python
class PermissionRuleService:
    SEED_RULES = [
        PermissionRule(
            name="Safe file read",
            category=RuleCategory.READ,
            risk_level=RiskLevel.SAFE,
            pattern=".*",
            action=RuleAction.ALLOW,
            priority=1,
        ),
        # ... remaining rules
    ]

    async def seed_default_rules(self) -> int:
        """Create default rules if none exist. Returns count of rules created."""
        existing = await self.list(enabled=True)
        if existing:
            return 0  # Rules already seeded

        created = 0
        for rule in self.SEED_RULES:
            await self.create(rule)
            created += 1
        return created
```

Called during application startup:

```python
# In backend/app/main.py or startup hook:
rule_service = PermissionRuleService(storage)
await rule_service.seed_default_rules()
```

---

## 8. API Endpoints

### 8.1 Permission Rules

Location: `backend/app/api/permission_rules.py`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/permissions/rules` | List all rules (`?employee_id=&enabled=`) |
| `GET` | `/api/permissions/rules/{id}` | Get rule detail |
| `POST` | `/api/permissions/rules` | Create rule |
| `PUT` | `/api/permissions/rules/{id}` | Update rule |
| `DELETE` | `/api/permissions/rules/{id}` | Soft delete (enabled=false) |
| `PUT` | `/api/permissions/rules/{id}/toggle` | Enable/disable rule |
| `GET` | `/api/permissions/rules/{id}/git-log` | Get Git history |

### 8.2 Permission Evaluation

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/permissions/evaluate` | Evaluate an action |

Request body:
```json
{
  "employee_id": "uuid",
  "agent_id": "uuid",
  "tool_name": "bash",
  "tool_input": {"command": "rm -rf /tmp/data"},
  "context": {"working_directory": "/home/user/project"}
}
```

Response:
```json
{
  "allowed": false,
  "risk_level": "high",
  "decision": "DENY",
  "evaluator": "RULE_MATCHER",
  "matched_rule_id": "uuid",
  "reasoning": "Detected recursive deletion pattern matching dangerous rule #42",
  "latency_ms": 12,
  "override_request_id": "uuid"
}
```

### 8.3 Audit Logs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/permissions/audit-logs` | List audit logs (`?employee_id=&decision=&risk_level=&limit=`) |
| `GET` | `/api/permissions/audit-logs/stats` | Get stats (by risk level, decision, time range) |

### 8.4 Override Requests

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/permissions/overrides` | Create override request |
| `GET` | `/api/permissions/overrides` | List overrides (`?status=pending&employee_id=`) |
| `GET` | `/api/permissions/overrides/{id}` | Get override detail |
| `POST` | `/api/permissions/overrides/{id}/approve` | Approve override |
| `POST` | `/api/permissions/overrides/{id}/reject` | Reject override |

### 8.5 API Schemas (Pydantic)

Follow the `employee_profiles.py` pattern with Response / Create / Update schemas:

```python
# PermissionRule schemas
class PermissionRuleResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    risk_level: str
    pattern: str
    action: str
    priority: int
    enabled: bool
    employee_id: str | None
    git_path: str
    created_by: str | None
    created_at: str | None
    updated_at: str | None

class CreatePermissionRule(BaseModel):
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    category: str  # READ, WRITE, DELETE, EXECUTE, NETWORK, PRODUCTION
    risk_level: str  # safe, low, medium, high, critical
    pattern: str = Field(max_length=500)
    action: str  # ALLOW, DENY, REQUIRE_APPROVAL
    priority: int = Field(default=5, ge=1, le=10)
    employee_id: str | None = None

class UpdatePermissionRule(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    pattern: str | None = Field(default=None, max_length=500)
    action: str | None = None
    priority: int | None = Field(default=None, ge=1, le=10)
    employee_id: str | None = None

# PermissionEvaluation schemas
class PermissionEvaluateRequest(BaseModel):
    employee_id: str
    agent_id: str
    tool_name: str
    tool_input: dict | str
    context: dict | None = None

class PermissionEvaluateResponse(BaseModel):
    allowed: bool
    risk_level: str
    decision: str
    evaluator: str
    matched_rule_id: str | None
    reasoning: str
    latency_ms: int
    override_request_id: str | None

# AuditLog schemas
class AuditLogResponse(BaseModel):
    id: str
    employee_id: str
    agent_id: str
    tool_name: str
    tool_input: str
    risk_level: str
    decision: str
    evaluator: str
    matched_rule_id: str | None
    reasoning: str
    latency_ms: int
    timestamp: str

# OverrideRequest schemas
class OverrideRequestResponse(BaseModel):
    id: str
    employee_id: str
    agent_id: str
    tool_name: str
    tool_input: str
    risk_level: str
    reason: str
    requested_by: str
    requested_at: str
    status: str
    approved_by: str | None
    approved_at: str | None
    rejection_reason: str | None
    expires_at: str | None

class CreateOverrideRequest(BaseModel):
    employee_id: str
    agent_id: str
    tool_name: str
    tool_input: str = Field(max_length=2000)
    risk_level: str  # high, critical
    reason: str = Field(max_length=2000)

class ApproveOverrideRequest(BaseModel):
    approved_by: str

class RejectOverrideRequest(BaseModel):
    approved_by: str
    rejection_reason: str = Field(max_length=1000)
```

---

## 9. File Structure

```
backend/app/
├── domain/
│   ├── permission_rule.py              # PermissionRule entity + enums
│   ├── permission_audit_log.py         # PermissionAuditLog entity
│   ├── permission_override_request.py  # PermissionOverrideRequest entity + enums
│   └── permission_result.py            # PermissionEvaluationResult entity
│
├── infrastructure/
│   └── storage/
│       └── sqlite.py                   # +3 models, +new async methods
│
├── application/
│   ├── permission_rule_service.py      # Rule CRUD with Git + SQLite dual persistence
│   ├── override_service.py             # Override request workflow
│   ├── permission_engine.py            # Core 4-layer PermissionEngine
│   └── nudge/
│       ├── rule_matcher.py             # [REUSE] adapted for permission patterns
│       └── reasoning_judge.py          # [REUSE] PermissionReasoningJudge variant
│
├── api/
│   └── permission_rules.py             # API routes (rules, evaluation, audit, overrides)
│
├── deepagents/
│   ├── permission.py                   # [DEPRECATED] PermissionController (keep for reference)
│   ├── skills_middleware.py            # [MODIFY] integrate PermissionEngine in awrap_tool_call
│   └── exceptions.py                   # [MODIFY] enhance PermissionDeniedError
│
└── config.py                           # +permission_rules_root setting
```

---

## 10. Development Checklist

### Phase 2.1: Data Layer

- [ ] Add `PermissionRuleModel`, `PermissionAuditLogModel`, `PermissionOverrideRequestModel` to `sqlite.py`
- [ ] Add `_to_*` converter methods for each model
- [ ] Implement all async CRUD methods in `SQLiteStorage`:
  - [ ] `save_permission_rule`, `get_permission_rule`, `list_permission_rules`, `delete_permission_rule`
  - [ ] `save_audit_log`, `query_audit_logs`, `get_audit_log_stats`
  - [ ] `save_override_request`, `get_override_request`, `list_override_requests`, `update_override_request`, `expire_overdue_overrides`
- [ ] Add `permission_rules_root` to `Settings`

### Phase 2.2: Domain Layer

- [ ] Create `backend/app/domain/permission_rule.py` with `PermissionRule` dataclass + enums
- [ ] Create `backend/app/domain/permission_audit_log.py` with `PermissionAuditLog` dataclass
- [ ] Create `backend/app/domain/permission_override_request.py` with `PermissionOverrideRequest` dataclass + enums
- [ ] Create `backend/app/domain/permission_result.py` with `PermissionEvaluationResult` dataclass
- [ ] Implement `PermissionRule.matches()` method (regex matching)

### Phase 2.3: Service Layer

- [ ] Create `backend/app/application/permission_rule_service.py` with Git + SQLite dual persistence
- [ ] Create `backend/app/application/override_service.py` with approval workflow
- [ ] Implement seed rules initialization
- [ ] Implement rule cache loading logic

### Phase 2.4: Permission Engine

- [ ] Create `backend/app/application/permission_engine.py`
- [ ] Implement `RiskClassifier` with tool map and escalation patterns
- [ ] Implement `PermissionEngine.evaluate_action()` 4-layer pipeline
- [ ] Implement rule matching with employee-specific + global priority
- [ ] Create `PermissionReasoningJudge` with timeout and fallback
- [ ] Implement audit logger (fire-and-forget)
- [ ] Implement override request auto-creation on DENY

### Phase 2.5: API Layer

- [ ] Create `backend/app/api/permission_rules.py` with all endpoints
- [ ] Create Pydantic schemas (Request/Response)
- [ ] Register router in `backend/app/api/__init__.py`
- [ ] Add `POST /api/permissions/evaluate` endpoint
- [ ] Add `GET /api/permissions/audit-logs` and `GET /api/permissions/audit-logs/stats`
- [ ] Add override CRUD endpoints with approve/reject

### Phase 2.6: Middleware Integration

- [ ] Enhance `PermissionDeniedError` with reason, risk_level, override_request_id
- [ ] Modify `SkillEventMiddleware.awrap_tool_call()` to use `PermissionEngine`
- [ ] Remove `_is_builtin_tool()` bypass (all tools go through evaluation)
- [ ] Inject `PermissionEngine` into middleware initialization
- [ ] Update `PermissionController` to mark as deprecated

### Phase 2.7: Startup & Initialization

- [ ] Add seed rules initialization to app startup
- [ ] Add overdue override expiry cron/check
- [ ] Verify database migration creates new tables

### Phase 2.8: Testing

- [ ] Test safe operation fast path (read_file → ALLOW < 50ms)
- [ ] Test `rm -rf /` → critical rule intercept → DENY
- [ ] Test `.env` file access → secret rule intercept → DENY
- [ ] Test complex bash without rule → ReasoningJudge evaluation
- [ ] Test ReasoningJudge timeout → safe fallback DENY
- [ ] Test audit log count equals operation count
- [ ] Test rule CRUD (create/edit/delete via API + Git verification)
- [ ] Test override flow (create → approve → temporary grant → expire)
- [ ] Test rule change immediate effect (no restart needed)
- [ ] Test built-in tools no longer bypass permission check

---

## 11. Migration Notes

### Backward Compatibility

- `PermissionController` in `permission.py` is kept but marked deprecated. It can be removed after Phase 2 is verified.
- `PermissionDeniedError` is extended with optional fields — existing callers that only pass `tool_name` and `agent_id` will continue to work.
- The middleware's `_is_builtin_tool()` method remains but is no longer used for permission bypass — it may be repurposed for logging.

### Database Migration

New tables are created automatically via SQLAlchemy's `Base.metadata.create_all()` during `init_db()`. No manual migration scripts needed since SQLite is used and tables are additive.

### Config

One new config field:
```yaml
permission_rules_root: "~/.claw/permission-rules"
```

---

## 12. Related Documents

| Document | Path |
|----------|------|
| Phase 2 PRD | `docs/phase2-product-design.md` |
| Phase 1 PRD | `docs/phase1-product-design.md` |
| Phase 1 API Reference | `docs/phase1-api.md` |
| Existing Permission Controller | `backend/app/deepagents/permission.py` |
| Existing RuleMatcher | `backend/app/application/nudge/rule_matcher.py` |
| Existing ReasoningJudge | `backend/app/application/nudge/reasoning_judge.py` |
| Skills Middleware | `backend/app/deepagents/skills_middleware.py` |
| Employee Profile Entity | `backend/app/domain/employee_profile.py` |
| Employee Profile Service | `backend/app/application/employee_profile_service.py` |
| Employee Profile API | `backend/app/api/employee_profiles.py` |
| SQLite Storage | `backend/app/infrastructure/storage/sqlite.py` |
| Custom Exceptions | `backend/app/deepagents/exceptions.py` |
