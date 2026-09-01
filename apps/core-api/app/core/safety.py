"""
ShiVi Accidental Data Loss Prevention (ADLP) Safety Guard
Protects against destructive schema operations, un-audited hard deletes, and accidental data wipes.
"""
import os
import sys
from typing import Optional


class ProductionDataLossError(Exception):
    """Raised when a destructive data operation is attempted against a production or protected database."""
    pass


class ADLPSafetyGuard:
    """
    Central safety validator enforcing zero accidental data loss across ShiVi.
    """
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
        url = db_url or os.getenv("DATABASE_URL", "")
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in cls.PROTECTED_HOST_PATTERNS)

    @classmethod
    def verify_safe_for_destructive_operation(cls, operation_name: str, db_url: Optional[str] = None) -> None:
        """
        Guarantees that destructive operations (e.g. drop table, database reset, truncation)
        are blocked on production databases and require explicit environment confirmation.
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
        Creates a structured soft-delete tombstone record for audit tracking.
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
