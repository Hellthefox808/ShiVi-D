"""
ShiVi Conflict Review & Safety Adjudication API Router
======================================================

Briefing:
    Provides REST endpoints for incident commanders, field supervisors, and triage officers
    to inspect active synchronization conflicts and formally adjudicate contradictions.
    When contradictory field reports trigger a Safety Freeze, this router allows commanders
    to review the evidence submitted by conflicting field teams and make an authoritative
    operational determination.

Reason:
    Autonomous resolution algorithms cannot replace human judgment when lives are at risk.
    By exposing explicit adjudication endpoints, the system ensures that:
    1. Every conflict is logged, auditable, and visible to commanders.
    2. Adjudications require a mandatory, written operational justification (`reason`).
    3. Resolving a conflict automatically rematerializes the underlying entity (e.g. routes)
       and safely updates all downstream dependent workflows (e.g. unblocking rescue convoys).
    4. An immutable audit record is committed to the ledger, and tactical dashboard caches
       are invalidated to propagate the new truth across the command center.
"""

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

# Briefing: FastAPI Router for conflict inspection and human-in-the-loop adjudication.
# Reason: Separates safety review workflows into a dedicated, authenticated operational domain.
router = APIRouter(prefix="/conflicts", tags=["Conflict Review & Safety Adjudication"])


class ConflictResolveRequest(BaseModel):
    """
    Briefing:
        Payload submitted by a commander or supervisor to adjudicate an active conflict case.

    Reason:
        Requires both the adjudicated target value and a mandatory written rationale (min 10 chars)
        to prevent accidental or unconsidered clicks during high-stress operations.
    """
    # Explanation: The canonical value chosen by the commander (e.g., 'BLOCKED', 'USABLE', 'SAFE')
    resolved_value: str = Field(..., description="Adjudicated value, e.g. BLOCKED or USABLE")
    # Explanation: Mandatory operational justification explaining why this value was selected
    reason: str = Field(..., min_length=10, description="Mandatory operational justification")


class ConflictCaseResponse(BaseModel):
    """
    Briefing:
        Pydantic response model representing a conflict case and its complete claim history.

    Reason:
        Supplies frontend tactical dashboards and mobile supervisor views with the opposing claims,
        frozen dependencies, resolution status, and audit timestamps.
    """
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
    """
    Briefing:
        Retrieves all conflict cases within the authenticated user's tenant organization.

    Reason:
        Allows field supervisors to view a live queue of open safety freezes requiring adjudication,
        or filter by 'OPEN' / 'RESOLVED' to review historical dispute decisions.

    Parameters:
        status_filter: Optional filter ('OPEN', 'RESOLVED', 'REOPENED').
        db: Asynchronous SQLAlchemy database session.
        current_user: Authenticated JWT claims containing tenant ID and caller role.

    Returns:
        List of `ConflictCaseResponse` objects ordered by creation date descending.
    """
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
    """
    Briefing:
        Fetches the detailed record of an individual conflict case by its unique UUID.

    Reason:
        Provides the full context (including photographic evidence links and opposing claims)
        when a supervisor opens a specific conflict for evaluation in the UI.

    Parameters:
        conflict_id: Primary key UUID of the conflict case.
        db: Database session.
        current_user: Authenticated JWT token payload.

    Returns:
        The matching `ConflictCaseResponse`.

    Raises:
        HTTPException(404): If the conflict case does not exist or belongs to another tenant.
    """
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
    """
    Briefing:
        Formally adjudicates an active conflict case and rematerializes dependent entities.

    Reason:
        This endpoint executes the core safety thaw sequence:
        1. Validates that the case is active ('OPEN') and authorized.
        2. Records the supervisor's verdict, identity, timestamp, and justification reason.
        3. Updates the target entity (e.g. RouteObservation) to the adjudicated value and unfreezes it.
        4. Recalculates all dependent tasks (e.g. unblocking or re-routing rescue convoys).
        5. Writes an immutable `AuditEntry` into the audit ledger.
        6. Invalidates the central dashboard cache so all commander screens update instantly.

    Parameters:
        conflict_id: Primary key UUID of the conflict case to adjudicate.
        req: `ConflictResolveRequest` containing the resolved value and required justification.
        db: Database session.
        current_user: Authenticated JWT token payload.

    Returns:
        Updated `ConflictCaseResponse` showing status 'RESOLVED'.

    Raises:
        HTTPException(404): If the case does not exist in the tenant.
        HTTPException(400): If the case has already been resolved.
    """
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

    # Explanation: Step 1 - Update Conflict Case record with supervisor verdict
    case.status = "RESOLVED"
    case.resolved_by_user_id = current_user.sub
    case.resolved_value = req.resolved_value.upper()
    case.resolution_reason = req.reason
    case.resolved_at = datetime.utcnow()

    # Explanation: Step 2 - Rematerialize target entity state (e.g., RouteObservation)
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

        # Explanation: Step 3 - Recalculate and update dependent rescue tasks
        for task_id in (case.frozen_dependencies or []):
            t_res = await db.execute(select(Task).where(Task.id == task_id))
            t = t_res.scalars().first()
            if t:
                if case.resolved_value == "BLOCKED":
                    # Explanation: Route is verified blocked; task stays blocked
                    t.is_route_blocked = "TRUE"
                    t.status = "BLOCKED"
                else:
                    # Explanation: Route is verified open/usable; thaw task back to OFFERED
                    t.is_route_blocked = "FALSE"
                    if t.status == "BLOCKED":
                        t.status = "OFFERED"

    # Explanation: Step 4 - Commit tamper-evident record into AuditEntry ledger
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

    # Explanation: Step 5 - Invalidate dashboard summary cache so command center displays update immediately
    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return case


class TriggerDisputeRequest(BaseModel):
    """
    Briefing: Request payload to simulate or trigger a live operational conflict between field nodes.
    """
    entity_id: str = "ROUTE-88"
    route_name: str = "Sector 4 Main Bridge"
    claim_a_value: str = "USABLE"
    claim_a_notes: str = "Scout SDRF Team Alpha reports route passable with minor debris."
    claim_b_value: str = "BLOCKED"
    claim_b_notes: str = "Local Ward Volunteer reports bridge railing collapse under 4ft surge flow."


@router.post("/trigger-dispute", response_model=ConflictCaseResponse)
async def trigger_dispute(
    req: TriggerDisputeRequest = TriggerDisputeRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Triggers an active operational conflict on a route or entity.
        Freezes dependent tasks, marks the route under safety freeze, and logs to the audit ledger.
    """
    conflict_id = str(uuid.uuid4())
    photo_ev_id = str(uuid.uuid4())

    case = ConflictCase(
        id=conflict_id,
        tenant_id=current_user.tenant_id,
        entity_type="route_observation",
        entity_id=req.entity_id,
        conflicting_field="status",
        status="OPEN",
        claims=[
            {
                "actor_id": "00000000-0000-0000-0000-000000000002",
                "device_id": "device-sdrf-01",
                "value": req.claim_a_value.upper(),
                "notes": req.claim_a_notes,
                "occurred_at": datetime.utcnow().isoformat(),
                "evidence_ids": [photo_ev_id],
            },
            {
                "actor_id": "00000000-0000-0000-0000-000000000003",
                "device_id": "device-ward-02",
                "value": req.claim_b_value.upper(),
                "notes": req.claim_b_notes,
                "occurred_at": datetime.utcnow().isoformat(),
                "evidence_ids": [],
            },
        ],
        frozen_dependencies=["task-rescue-88"],
    )
    db.add(case)

    # Freeze the route
    r_res = await db.execute(
        select(RouteObservation).where(
            RouteObservation.route_identifier == req.entity_id,
            RouteObservation.tenant_id == current_user.tenant_id,
        )
    )
    route = r_res.scalars().first()
    if route:
        route.status = "BLOCKED"
        route.is_frozen = "TRUE"
        route.active_conflict_id = conflict_id
        route.updated_at = datetime.utcnow()

    # Log audit entry
    audit = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        action="CONFLICT_DETECTED_FREEZE",
        actor_id=current_user.sub,
        actor_role=current_user.role,
        target_entity_type="route_observation",
        target_entity_id=req.entity_id,
        previous_state={"status": "USABLE"},
        new_state={"status": "CONFLICT_FROZEN", "conflict_id": conflict_id},
        reason=f"Life-safety contradiction on {req.entity_id}: {req.claim_a_value} vs {req.claim_b_value}. Automation frozen.",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(case)

    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return case

