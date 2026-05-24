"""Override request application service."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.domain.base import EntityId
from app.domain.permission_override_request import (
    PermissionOverrideRequest,
    OverrideStatus,
)
from app.infrastructure.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class OverrideService:
    """Service for managing permission override requests."""

    OVERRIDE_TTL_HOURS = 24  # approved overrides valid for 24h

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    async def create_request(
        self,
        employee_id: str,
        agent_id: str,
        tool_name: str,
        tool_input: str,
        risk_level: str,
        reason: str,
        requested_by: str,
    ) -> PermissionOverrideRequest:
        """Create a new override request."""
        req = PermissionOverrideRequest(
            employee_id=EntityId(employee_id),
            agent_id=EntityId(agent_id),
            tool_name=tool_name,
            tool_input=tool_input[:2000],
            risk_level=risk_level,
            reason=reason,
            requested_by=EntityId(requested_by),
        )
        await self.storage.save_override_request(req)
        logger.info(f"Created override request {req.id} for tool '{tool_name}'")
        return req

    async def approve(self, request_id: str, approved_by: str) -> Optional[PermissionOverrideRequest]:
        """Approve an override request. Sets expires_at = now + 24h."""
        req = await self.get(request_id)
        if not req:
            return None
        if req.status not in (OverrideStatus.PENDING,):
            return None

        now = datetime.now(timezone.utc)
        req.status = OverrideStatus.APPROVED
        req.approved_by = EntityId(approved_by)
        req.approved_at = now
        req.expires_at = now + timedelta(hours=self.OVERRIDE_TTL_HOURS)

        await self.storage.save_override_request(req)
        logger.info(f"Approved override request {request_id}, expires at {req.expires_at}")
        return req

    async def reject(self, request_id: str, approved_by: str,
                     rejection_reason: str) -> Optional[PermissionOverrideRequest]:
        """Reject an override request."""
        req = await self.get(request_id)
        if not req:
            return None
        if req.status not in (OverrideStatus.PENDING,):
            return None

        now = datetime.now(timezone.utc)
        req.status = OverrideStatus.REJECTED
        req.approved_by = EntityId(approved_by)
        req.approved_at = now
        req.rejection_reason = rejection_reason

        await self.storage.save_override_request(req)
        logger.info(f"Rejected override request {request_id}")
        return req

    async def get(self, request_id: str) -> Optional[PermissionOverrideRequest]:
        """Get override request by ID."""
        return await self.storage.get_override_request(request_id)

    async def list(self, employee_id: str | None = None,
                   status: str | None = None) -> List[PermissionOverrideRequest]:
        """List override requests with optional filters."""
        return await self.storage.list_override_requests(
            employee_id=employee_id,
            status=status,
        )

    async def is_override_active(self, employee_id: str, agent_id: str,
                                  tool_name: str) -> bool:
        """Check if there is an active (approved, not expired) override for this tool."""
        active = await self.storage.get_active_override(employee_id, agent_id, tool_name)
        return active is not None

    async def expire_overdue(self) -> int:
        """Batch expire all overrides past their expires_at."""
        return await self.storage.expire_overdue_overrides()
