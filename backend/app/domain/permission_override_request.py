"""Permission override request domain entity."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.domain.base import EntityId


class OverrideStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class PermissionOverrideRequest:
    """Permission override request entity."""
    employee_id: EntityId
    agent_id: EntityId
    tool_name: str
    tool_input: str
    risk_level: str
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
    def is_expired(self) -> bool:
        """Check if this override has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if this override is currently valid (approved and not expired)."""
        return (
            self.status == OverrideStatus.APPROVED
            and not self.is_expired
        )
