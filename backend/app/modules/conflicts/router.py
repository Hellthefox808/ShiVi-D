import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.conflicts.models import ConflictCase
from app.modules.incidents.models import RouteObservation
from app.modules.tasks.models import Task
from app.modules.audit.models import AuditEntry, OperationalEvent

router = APIRouter(prefix="/conflicts", tags=["Conflict Review & Safety Adjudication"])


class ConflictResolveRequest(BaseModel):
    resolved_value: str = Field(..., description="Adjudicated value, e.g. BLOCKED or USABLE")
    reason: str = Field(..., min_length=10, description="Mandatory operational justification")


class ConflictCaseResponse(BaseModel):
    id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    conflicting_field: str
    status: str
    claims: List[Dict[str, Any]]
    frozen_dependencies: List[str]
    resolved_by_user_id: Optional[str]
    resolved_value: Optional[str]
    resolution_reason: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime


@router.get("", response_model=List[ConflictCaseResponse])
async def list_conflicts(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    query = select(ConflictCase).where(ConflictCase.tenant_id == current_user.tenant_id)
    if status_filter:
        query = query.where(ConflictCase.status == status_filter.upper())
    query = query.order_by(ConflictCase.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{conflict_id}", response_model=ConflictCaseResponse)
async def get_conflict(
    conflict_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    result = await db.execute(
        select(ConflictCase).where(
            ConflictCase.id == conflict_id,
            ConflictCase.tenant_id == current_user.tenant_id,
        )
    )
    case = result.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Conflict case not found")
    return case


@router.post("/{conflict_id}/resolve", response_model=ConflictCaseResponse)
async def resolve_conflict(
    conflict_id: str,
    req: ConflictResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    result = await db.execute(
        select(ConflictCase).where(
            ConflictCase.id == conflict_id,
            ConflictCase.tenant_id == current_user.tenant_id,
        )
    )
    case = result.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Conflict case not found")

    if case.status == "RESOLVED":
        raise HTTPException(status_code=400, detail="Conflict case already resolved")

    # Update Conflict Case
    case.status = "RESOLVED"
    case.resolved_by_user_id = current_user.sub
    case.resolved_value = req.resolved_value.upper()
    case.resolution_reason = req.reason
    case.resolved_at = datetime.utcnow()

    # Rematerialize the target entity state
    if case.entity_type == "route_observation":
        r_res = await db.execute(
            select(RouteObservation).where(
                RouteObservation.route_identifier == case.entity_id,
                RouteObservation.tenant_id == current_user.tenant_id,
            )
        )
        route = r_res.scalars().first()
        if route:
            route.status = case.resolved_value
            route.is_frozen = "FALSE"
            route.active_conflict_id = None
            route.updated_at = datetime.utcnow()

        # Recalculate dependent tasks
        for task_id in (case.frozen_dependencies or []):
            t_res = await db.execute(select(Task).where(Task.id == task_id))
            t = t_res.scalars().first()
            if t:
                if case.resolved_value == "BLOCKED":
                    t.is_route_blocked = "TRUE"
                    t.status = "BLOCKED"
                else:
                    t.is_route_blocked = "FALSE"
                    if t.status == "BLOCKED":
                        t.status = "OFFERED"

    # Record Audit Entry
    audit = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        action="CONFLICT_ADJUDICATED_RESOLVED",
        actor_id=current_user.sub,
        actor_role=current_user.role,
        target_entity_type=case.entity_type,
        target_entity_id=case.entity_id,
        previous_state={"conflict_id": case.id, "status": "UNCERTAIN"},
        new_state={"status": case.resolved_value},
        reason=req.reason,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(case)
    return case
