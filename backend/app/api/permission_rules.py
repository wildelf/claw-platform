"""Permission API routes: rules, evaluation, audit logs, and overrides."""

import logging
from typing import List, Optional

import re as _re
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import Storage, UserId
from app.application.override_service import OverrideService
from app.application.permission_engine import PermissionEngine
from app.application.permission_rule_service import PermissionRuleService
from app.domain.permission_override_request import OverrideStatus
from app.domain.permission_rule import PermissionRule

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/permissions", tags=["permissions"])

# --- Lazy service helpers ---

def _get_rule_service(storage):
    return PermissionRuleService(storage)


def _get_override_service(storage):
    return OverrideService(storage)


def _get_permission_engine(storage):
    rule_service = _get_rule_service(storage)
    override_service = _get_override_service(storage)
    return PermissionEngine(
        storage=storage,
        rule_service=rule_service,
        override_service=override_service,
    )


# --- Pydantic schemas ---

class PermissionRuleResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    category: str
    risk_level: str
    pattern: str
    action: str
    priority: int
    enabled: bool
    employee_id: str | None = None
    git_path: str = ""
    created_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CreatePermissionRule(BaseModel):
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    category: str  # READ, WRITE, DELETE, EXECUTE, NETWORK, PRODUCTION
    risk_level: str  # safe, low, medium, high, critical
    pattern: str = Field(max_length=500)
    action: str  # ALLOW, DENY, REQUIRE_APPROVAL
    priority: int = Field(default=5, ge=1, le=10)
    enabled: bool = True
    employee_id: str | None = None


class UpdatePermissionRule(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    pattern: str | None = Field(default=None, max_length=500)
    action: str | None = None
    priority: int | None = Field(default=None, ge=1, le=10)
    enabled: bool | None = None
    employee_id: str | None = None


class ToggleRuleRequest(BaseModel):
    enabled: bool


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


class AuditStatsResponse(BaseModel):
    period: str
    total_evaluations: int
    by_decision: dict
    by_risk_level: dict
    by_evaluator: dict
    avg_latency_ms: int
    p95_latency_ms: int
    override_requests: dict | None = None


class CreateOverrideRequest(BaseModel):
    employee_id: str
    agent_id: str
    tool_name: str
    tool_input: str = Field(max_length=2000)
    risk_level: str  # high, critical
    reason: str = Field(max_length=2000)


class OverrideRequestResponse(BaseModel):
    id: str
    employee_id: str
    agent_id: str
    tool_name: str
    tool_input: str
    risk_level: str
    reason: str
    requested_by: str
    requested_at: str | None = None
    status: str
    approved_by: str | None = None
    approved_at: str | None = None
    rejection_reason: str | None = None
    expires_at: str | None = None


class ApproveOverrideRequest(BaseModel):
    comment: str = Field(default="", max_length=1000)


class RejectOverrideRequest(BaseModel):
    reason: str = Field(max_length=1000)


# --- Helpers ---

def _rule_to_response(rule: PermissionRule) -> PermissionRuleResponse:
    return PermissionRuleResponse(
        id=str(rule.id),
        name=rule.name,
        description=rule.description,
        category=rule.category.value if hasattr(rule.category, 'value') else str(rule.category),
        risk_level=rule.risk_level.value if hasattr(rule.risk_level, 'value') else str(rule.risk_level),
        pattern=rule.pattern,
        action=rule.action.value if hasattr(rule.action, 'value') else str(rule.action),
        priority=rule.priority,
        enabled=rule.enabled,
        employee_id=str(rule.employee_id) if rule.employee_id else None,
        git_path=rule.git_path,
        created_by=str(rule.created_by) if rule.created_by else None,
        created_at=rule.created_at.isoformat() if rule.created_at else None,
        updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
    )


def _override_to_response(req) -> OverrideRequestResponse:
    return OverrideRequestResponse(
        id=str(req.id),
        employee_id=str(req.employee_id),
        agent_id=str(req.agent_id),
        tool_name=req.tool_name,
        tool_input=req.tool_input,
        risk_level=req.risk_level if isinstance(req.risk_level, str) else req.risk_level.value,
        reason=req.reason,
        requested_by=str(req.requested_by),
        requested_at=req.requested_at.isoformat() if req.requested_at else None,
        status=req.status.value if hasattr(req.status, 'value') else str(req.status),
        approved_by=str(req.approved_by) if req.approved_by else None,
        approved_at=req.approved_at.isoformat() if req.approved_at else None,
        rejection_reason=req.rejection_reason,
        expires_at=req.expires_at.isoformat() if req.expires_at else None,
    )


# --- Permission Rules ---

@router.post("/rules", response_model=PermissionRuleResponse, status_code=201)
async def create_permission_rule(
    data: CreatePermissionRule,
    storage: Storage,
    user_id: UserId,
):
    # Validate regex pattern
    try:
        _re.compile(data.pattern)
    except _re.error as e:
        raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {e}")

    service = _get_rule_service(storage)
    from app.domain.permission_rule import RuleCategory, RiskLevel, RuleAction, PermissionRule
    rule = PermissionRule(
        name=data.name,
        description=data.description,
        category=RuleCategory(data.category),
        risk_level=RiskLevel(data.risk_level),
        pattern=data.pattern,
        action=RuleAction(data.action),
        priority=data.priority,
        enabled=data.enabled,
        employee_id=user_id if data.employee_id is None else None,  # use user_id as created_by
        created_by=user_id,
    )
    # Override employee_id if explicitly provided
    if data.employee_id:
        from app.domain.base import EntityId
        rule.employee_id = EntityId(data.employee_id)

    created = await service.create(rule)
    return _rule_to_response(created)


@router.get("/rules", response_model=List[PermissionRuleResponse])
async def list_permission_rules(
    employee_id: str | None = Query(None),
    enabled: bool | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    storage: Storage = None,
):
    service = _get_rule_service(storage)
    rules = await service.list(employee_id=employee_id, enabled=enabled, category=category)
    return [_rule_to_response(r) for r in rules]


@router.get("/rules/{rule_id}", response_model=PermissionRuleResponse)
async def get_permission_rule(rule_id: str, storage: Storage = None):
    service = _get_rule_service(storage)
    rule = await service.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Permission rule not found")
    return _rule_to_response(rule)


@router.put("/rules/{rule_id}", response_model=PermissionRuleResponse)
async def update_permission_rule(rule_id: str, data: UpdatePermissionRule, storage: Storage = None):
    # Validate regex if pattern is provided
    if data.pattern is not None:
        try:
            _re.compile(data.pattern)
        except _re.error as e:
            raise HTTPException(status_code=400, detail=f"Invalid regex pattern: {e}")

    service = _get_rule_service(storage)
    rule = await service.update(rule_id, data.model_dump(exclude_unset=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Permission rule not found")
    return _rule_to_response(rule)


@router.delete("/rules/{rule_id}")
async def delete_permission_rule(rule_id: str, storage: Storage = None):
    service = _get_rule_service(storage)
    deleted = await service.delete(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Permission rule not found")
    return {"deleted": True, "message": "Permission rule disabled (soft delete)"}


@router.put("/rules/{rule_id}/toggle")
async def toggle_permission_rule(rule_id: str, data: ToggleRuleRequest, storage: Storage = None):
    service = _get_rule_service(storage)
    rule = await service.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Permission rule not found")

    rule.enabled = data.enabled
    rule = await service.update(rule_id, {"enabled": data.enabled})
    return {
        "id": str(rule.id),
        "enabled": rule.enabled,
        "message": f"Rule {'enabled' if rule.enabled else 'disabled'}",
    }


@router.get("/rules/{rule_id}/git-log")
async def get_rule_git_log(rule_id: str, limit: int = Query(20, ge=1, le=100), storage: Storage = None):
    """Get Git history for a rule. Returns mock data since Git integration is file-based."""
    service = _get_rule_service(storage)
    rule = await service.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Permission rule not found")

    # Return basic file info as Git log (actual Git commits would require GitPython integration)
    return {
        "rule_id": rule_id,
        "git_path": rule.git_path,
        "commits": [
            {
                "hash": "initial",
                "author": str(rule.created_by) if rule.created_by else "system",
                "message": "Rule creation" + (f" - {rule.name}" if rule.name else ""),
                "timestamp": rule.created_at.isoformat() if rule.created_at else None,
            }
        ],
    }


# --- Permission Evaluation ---

@router.post("/evaluate", response_model=PermissionEvaluateResponse)
async def evaluate_permission(
    data: PermissionEvaluateRequest,
    storage: Storage,
):
    engine = _get_permission_engine(storage)
    result = await engine.evaluate_action(
        tool_name=data.tool_name,
        tool_input=data.tool_input,
        employee_id=data.employee_id,
        agent_id=data.agent_id,
        context=data.context,
    )
    return PermissionEvaluateResponse(
        allowed=result.allowed,
        risk_level=result.risk_level.value if hasattr(result.risk_level, 'value') else str(result.risk_level),
        decision=result.decision.value if hasattr(result.decision, 'value') else str(result.decision),
        evaluator=result.evaluator.value if hasattr(result.evaluator, 'value') else str(result.evaluator),
        matched_rule_id=str(result.matched_rule_id) if result.matched_rule_id else None,
        reasoning=result.reasoning,
        latency_ms=result.latency_ms,
        override_request_id=str(result.override_request_id) if result.override_request_id else None,
    )


# --- Audit Logs ---

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    employee_id: str | None = Query(None),
    decision: str | None = Query(None),
    risk_level: str | None = Query(None),
    evaluator: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    storage: Storage = None,
):
    logs = await storage.query_audit_logs(
        employee_id=employee_id,
        decision=decision,
        risk_level=risk_level,
        evaluator=evaluator,
        offset=offset,
        limit=limit,
    )
    return [
        AuditLogResponse(
            id=str(log.id),
            employee_id=str(log.employee_id),
            agent_id=str(log.agent_id),
            tool_name=log.tool_name,
            tool_input=log.tool_input,
            risk_level=log.risk_level if isinstance(log.risk_level, str) else log.risk_level.value,
            decision=log.decision.value if hasattr(log.decision, 'value') else str(log.decision),
            evaluator=log.evaluator.value if hasattr(log.evaluator, 'value') else str(log.evaluator),
            matched_rule_id=str(log.matched_rule_id) if log.matched_rule_id else None,
            reasoning=log.reasoning,
            latency_ms=log.latency_ms,
            timestamp=log.timestamp.isoformat() if log.timestamp else None,
        )
        for log in logs
    ]


@router.get("/audit-logs/stats", response_model=AuditStatsResponse)
async def get_audit_log_stats(
    employee_id: str | None = Query(None),
    period: str = Query("7d"),
    storage: Storage = None,
):
    period_map = {"1h": 1/24, "6h": 6/24, "24h": 1, "7d": 7, "30d": 30}
    days = period_map.get(period, 7)

    stats = await storage.get_audit_log_stats(days=days, employee_id=employee_id)
    return AuditStatsResponse(**stats)


# --- Override Requests ---

@router.post("/overrides", response_model=OverrideRequestResponse, status_code=201)
async def create_override_request(
    data: CreateOverrideRequest,
    storage: Storage,
    user_id: UserId,
):
    service = _get_override_service(storage)
    req = await service.create_request(
        employee_id=data.employee_id,
        agent_id=data.agent_id,
        tool_name=data.tool_name,
        tool_input=data.tool_input,
        risk_level=data.risk_level,
        reason=data.reason,
        requested_by=str(user_id),
    )
    return _override_to_response(req)


@router.get("/overrides", response_model=List[OverrideRequestResponse])
async def list_override_requests(
    status: str | None = Query(None),
    employee_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    storage: Storage = None,
):
    service = _get_override_service(storage)
    reqs = await service.list(employee_id=employee_id, status=status)
    return [_override_to_response(r) for r in reqs]


@router.get("/overrides/{override_id}", response_model=OverrideRequestResponse)
async def get_override_request(override_id: str, storage: Storage = None):
    service = _get_override_service(storage)
    req = await service.get(override_id)
    if not req:
        raise HTTPException(status_code=404, detail="Override request not found")
    return _override_to_response(req)


@router.post("/overrides/{override_id}/approve")
async def approve_override_request(
    override_id: str,
    data: ApproveOverrideRequest,
    storage: Storage,
    user_id: UserId,
):
    service = _get_override_service(storage)
    req = await service.approve(override_id, str(user_id))
    if not req:
        # Check if not found or already resolved
        existing = await service.get(override_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Override request not found")
        raise HTTPException(status_code=400, detail="Request already resolved (APPROVED/REJECTED/EXPIRED)")
    return {
        "id": str(req.id),
        "status": req.status.value if hasattr(req.status, 'value') else str(req.status),
        "approved_by": str(req.approved_by) if req.approved_by else None,
        "approved_at": req.approved_at.isoformat() if req.approved_at else None,
        "expires_at": req.expires_at.isoformat() if req.expires_at else None,
        "message": "Override approved. Temporary authorization valid for 24 hours.",
    }


@router.post("/overrides/{override_id}/reject")
async def reject_override_request(
    override_id: str,
    data: RejectOverrideRequest,
    storage: Storage,
    user_id: UserId,
):
    service = _get_override_service(storage)
    req = await service.reject(override_id, str(user_id), data.reason)
    if not req:
        existing = await service.get(override_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Override request not found")
        raise HTTPException(status_code=400, detail="Request already resolved (APPROVED/REJECTED/EXPIRED)")
    return {
        "id": str(req.id),
        "status": req.status.value if hasattr(req.status, 'value') else str(req.status),
        "rejection_reason": req.rejection_reason,
        "approved_by": str(req.approved_by) if req.approved_by else None,
        "approved_at": req.approved_at.isoformat() if req.approved_at else None,
        "expires_at": None,
        "message": "Override request rejected",
    }
