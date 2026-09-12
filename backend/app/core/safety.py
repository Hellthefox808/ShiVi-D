"""
Briefing: ShiVi Accidental Data Loss Prevention (ADLP) Safety Guard.
Reason: In high-stress emergency response environments, an accidental database wipe, dropped table,
or un-audited hard delete could erase victim distress logs and responder locations. This guard acts
as a fail-safe firewall preventing destructive schema commands on production databases.
"""

import os
import sys
from typing import Optional


class ProductionDataLossError(Exception):
    """
    Briefing: Exception raised when an unsafe or destructive database operation is intercepted.
    Reason: Immediately terminates execution before any irreversible schema or data alteration occurs.
    """
    pass


class ADLPSafetyGuard:
    """
    Briefing: Central safety validator enforcing zero accidental data loss across all ShiVi services.
    Reason: Enforces guardrails preventing hard deletes and blocking reset operations on production clusters.
    """
    # Hostname substrings identifying live cloud databases
    PROTECTED_HOST_PATTERNS = [
        "prod",
        "production",
        "azure.com",
        "postgres.database.azure.com",
        "aws.com",
        "rds.amazonaws.com",
        "google.com",
    ]

    @classmethod
    def is_production_database(cls, db_url: Optional[str] = None) -> bool:
        """
        Briefing: Evaluates whether a database connection string points to a live production database.
        Reason: Matches the URI against [PROTECTED_HOST_PATTERNS] to prevent accidental test runs on production.
        """
        url = db_url or os.getenv("DATABASE_URL", "")
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in cls.PROTECTED_HOST_PATTERNS)

    @classmethod
    def verify_safe_for_destructive_operation(cls, operation_name: str, db_url: Optional[str] = None) -> None:
        """
        Briefing: Validates whether a destructive operation (e.g. drop table, database reset, truncation) is permissible.
        Reason: Guarantees that:
        1. Operations are unconditionally BLOCKED on production environments.
        2. Non-production environments require explicit `ALLOW_DATA_RESET=1` confirmation.
        
        Raises:
            ProductionDataLossError: If the safety criteria are violated.
        """
        url = db_url or os.getenv("DATABASE_URL", "")
        
        # 1. Block unconditionally on production databases
        if cls.is_production_database(url):
            raise ProductionDataLossError(
                f"[CRITICAL SAFETY BLOCK] Operation '{operation_name}' was BLOCKED! "
                f"Destructive operations are strictly forbidden on production databases ({url})."
            )

        # 2. Check explicit environment variable flag
        allow_reset = os.getenv("ALLOW_DATA_RESET", "0")
        if allow_reset != "1":
            raise ProductionDataLossError(
                f"[SAFETY GUARD] Operation '{operation_name}' requires explicit confirmation. "
                "Set ALLOW_DATA_RESET=1 in your environment or supply explicit user confirmation."
            )

    @classmethod
    def audit_soft_delete(cls, entity_name: str, entity_id: str, actor_id: str, reason: str) -> dict:
        """
        Briefing: Constructs an immutable soft-delete tombstone record.
        Reason: Humanitarian records must NEVER be hard-deleted from tables. Instead, they are marked
        as soft-deleted with an audit trail specifying who deleted the record, when, and the rationale.
        """
        from datetime import datetime
        return {
            "action": f"{entity_name.upper()}_SOFT_DELETED",
            "entity_name": entity_name,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "reason": reason,
            "deleted_at": datetime.utcnow().isoformat(),
            "is_recoverable": True,
        }

