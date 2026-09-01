from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.audit.models import AuditEntry, OperationalEvent

router = APIRouter(prefix="/audit", tags=["Audit Ledger & Traceability"])


class AuditEntryResponse(BaseModel):
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
    result = await db.execute(
        select(AuditEntry)
        .where(AuditEntry.tenant_id == current_user.tenant_id)
        .order_by(AuditEntry.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()
