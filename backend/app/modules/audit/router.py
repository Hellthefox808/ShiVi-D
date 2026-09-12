"""
ShiVi Audit Ledger & Traceability API Router
============================================

Briefing:
    Provides REST endpoints for querying the high-level compliance and administrative audit timeline.
    Enables commanders, public oversight officials, and post-disaster review boards to inspect
    all operational adjudications, triage adjustments, task verifications, and safety freezes.

Reason:
    Transparency and legal defensibility are critical in emergency response.
    This router exposes:
    1. Chronological Timeline: Retrieves recent audit actions ordered by timestamp descending.
    2. Tenant Partitioning: Strictly scopes audit logs to the caller's authorized tenant organization.
    3. State Reconstruction: Exposes previous state, new state, actor roles, and operational reasons.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.audit.models import AuditEntry, OperationalEvent

# Briefing: FastAPI Router mounted under `/audit` for administrative compliance inspection.
# Reason: Provides isolated read-only queries for audit ledger inspection.
router = APIRouter(prefix="/audit", tags=["Audit Ledger & Traceability"])


class AuditEntryResponse(BaseModel):
    """
    Briefing:
        Pydantic response model representing a single historical audit log entry.
    """
    id: str
    action: str
    actor_id: str
    actor_role: str
    target_entity_type: str
    target_entity_id: str
    previous_state: Optional[Dict[str, Any]]
    new_state: Optional[Dict[str, Any]]
    reason: Optional[str]
    timestamp: datetime


@router.get("/timeline", response_model=List[AuditEntryResponse])
async def get_audit_timeline(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Retrieves the chronological audit log timeline for the active tenant organization.

    Reason:
        Allows the tactical dashboard's Audit Inspector view to display a live feed of all
        commander decisions, conflict resolutions, and status overrides.

    Parameters:
        limit: Maximum number of audit records to retrieve (default 100).
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        List of `AuditEntryResponse` records ordered by `timestamp.desc()`.
    """
    result = await db.execute(
        select(AuditEntry)
        .where(AuditEntry.tenant_id == current_user.tenant_id)
        .order_by(AuditEntry.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()
