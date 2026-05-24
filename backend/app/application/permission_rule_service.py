"""Permission rule application service with Git + SQLite dual persistence."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.domain.base import EntityId
from app.domain.permission_rule import (
    PermissionRule,
    RuleAction,
    RuleCategory,
    RiskLevel,
)
from app.infrastructure.storage.sqlite import SQLiteStorage

logger = logging.getLogger(__name__)


class PermissionRuleService:
    """Service for managing permission rules with dual persistence (Git + SQLite)."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    def _get_rule_dir(self, rule: PermissionRule) -> Path:
        """Get the git-managed directory for a rule."""
        rules_root = Path(getattr(settings, 'permission_rules_root', '~/.claw/permission-rules')).expanduser()
        return rules_root / str(rule.id)

    def _ensure_rule_dir(self, rule: PermissionRule) -> Path:
        """Create and return the rule directory."""
        rule_dir = self._get_rule_dir(rule)
        rule_dir.mkdir(parents=True, exist_ok=True)
        rule.git_path = str(rule_dir / "rule.json")
        return rule_dir

    def _generate_rule_json(self, rule: PermissionRule) -> str:
        """Generate rule.json content for Git storage."""
        return json.dumps(
            {
                "id": str(rule.id),
                "name": rule.name,
                "description": rule.description,
                "category": rule.category.value if hasattr(rule.category, 'value') else str(rule.category),
                "risk_level": rule.risk_level.value if hasattr(rule.risk_level, 'value') else str(rule.risk_level),
                "pattern": rule.pattern,
                "action": rule.action.value if hasattr(rule.action, 'value') else str(rule.action),
                "priority": rule.priority,
                "enabled": rule.enabled,
                "employee_id": str(rule.employee_id) if rule.employee_id else None,
                "created_by": str(rule.created_by) if rule.created_by else None,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
            },
            ensure_ascii=False,
            indent=2,
        )

    async def create(self, rule: PermissionRule) -> PermissionRule:
        """Create rule: write to Git (rule.json) + sync to SQLite."""
        rule_dir = self._ensure_rule_dir(rule)
        rule_json = rule_dir / "rule.json"
        rule_json.write_text(self._generate_rule_json(rule), encoding="utf-8")

        await self.storage.save_permission_rule(rule)
        return rule

    async def get(self, rule_id: str) -> Optional[PermissionRule]:
        """Get rule by ID."""
        return await self.storage.get_permission_rule(rule_id)

    async def list(self, employee_id: str | None = None,
                   enabled: bool | None = None,
                   category: str | None = None) -> List[PermissionRule]:
        """List rules with optional filters."""
        return await self.storage.list_permission_rules(
            employee_id=employee_id,
            enabled=enabled,
            category=category,
        )

    async def update(self, rule_id: str, data: dict) -> Optional[PermissionRule]:
        """Update rule: write to Git + sync to SQLite."""
        rule = await self.get(rule_id)
        if not rule:
            return None

        for key, value in data.items():
            if hasattr(rule, key) and key not in ("id", "created_at", "created_by"):
                setattr(rule, key, value)

        rule.updated_at = datetime.now(timezone.utc)

        # Update Git file
        rule_dir = self._ensure_rule_dir(rule)
        rule_json = rule_dir / "rule.json"
        rule_json.write_text(self._generate_rule_json(rule), encoding="utf-8")

        await self.storage.save_permission_rule(rule)
        return rule

    async def delete(self, rule_id: str) -> bool:
        """Soft delete: set enabled=false."""
        rule = await self.get(rule_id)
        if not rule:
            return False
        rule.enabled = False
        rule.updated_at = datetime.now(timezone.utc)

        # Update Git file
        rule_dir = self._ensure_rule_dir(rule)
        rule_json = rule_dir / "rule.json"
        rule_json.write_text(self._generate_rule_json(rule), encoding="utf-8")

        await self.storage.save_permission_rule(rule)
        return True

    async def toggle(self, rule_id: str) -> Optional[PermissionRule]:
        """Toggle rule enabled/disabled."""
        rule = await self.get(rule_id)
        if not rule:
            return None
        rule.enabled = not rule.enabled
        rule.updated_at = datetime.now(timezone.utc)

        rule_dir = self._ensure_rule_dir(rule)
        rule_json = rule_dir / "rule.json"
        rule_json.write_text(self._generate_rule_json(rule), encoding="utf-8")

        await self.storage.save_permission_rule(rule)
        return rule

    async def load_active_rules(self) -> List[PermissionRule]:
        """Load all enabled rules, sorted by priority (highest first)."""
        rules = await self.list(enabled=True)
        return sorted(rules, key=lambda r: r.priority, reverse=True)

    # --- Seed rules ---

    SEED_RULES = [
        PermissionRule(
            name="Safe file read",
            category=RuleCategory.READ,
            risk_level=RiskLevel.SAFE,
            pattern=".*",
            action=RuleAction.ALLOW,
            priority=1,
        ),
        PermissionRule(
            name="Secret file access",
            category=RuleCategory.READ,
            risk_level=RiskLevel.HIGH,
            pattern=r"\.(env|key|pem|credentials)$",
            action=RuleAction.DENY,
            priority=9,
        ),
        PermissionRule(
            name="Config file write",
            category=RuleCategory.WRITE,
            risk_level=RiskLevel.LOW,
            pattern=r"\.(yaml|yml|json|toml|ini)$",
            action=RuleAction.ALLOW,
            priority=3,
        ),
        PermissionRule(
            name="Delete detection",
            category=RuleCategory.DELETE,
            risk_level=RiskLevel.HIGH,
            pattern=r"(rm|rmdir|unlink|DROP|DELETE FROM)",
            action=RuleAction.DENY,
            priority=9,
        ),
        PermissionRule(
            name="Dangerous bash",
            category=RuleCategory.EXECUTE,
            risk_level=RiskLevel.CRITICAL,
            pattern=r"(rm\s+-rf|mkfs|dd\s+if=|chmod\s+777)",
            action=RuleAction.DENY,
            priority=10,
        ),
        PermissionRule(
            name="Production access",
            category=RuleCategory.PRODUCTION,
            risk_level=RiskLevel.HIGH,
            pattern=r"(prod|production|live)",
            action=RuleAction.REQUIRE_APPROVAL,
            priority=8,
        ),
        PermissionRule(
            name="Network allowlist",
            category=RuleCategory.NETWORK,
            risk_level=RiskLevel.LOW,
            pattern=r"^(https?://api\.allowed-domain\.com/)",
            action=RuleAction.ALLOW,
            priority=2,
        ),
        PermissionRule(
            name="Script execution",
            category=RuleCategory.EXECUTE,
            risk_level=RiskLevel.MEDIUM,
            pattern=r"\.(sh|py|js|rb)$",
            action=RuleAction.ALLOW,
            priority=4,
        ),
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
        logger.info(f"Seeded {created} default permission rules")
        return created
