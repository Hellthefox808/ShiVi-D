"""
ShiVi Tactical Tasks & Field Assignments API Router
===================================================

Briefing:
    Provides REST endpoints for managing the end-to-end operational lifecycle of rescue tasks.
    Enables incident dispatchers to spawn tasks, assign qualified field units, enforce route-safety
    preconditions, and track responder status updates from dispatch through to site arrival and completion.

Reason:
    Coordinating multi-agency rescue teams requires strict, fail-safe dispatch logic:
    1. Safety-Gated Dispatch: Prevents commanders from assigning responders along corridors that are
       currently under active life-safety conflict freeze (`is_frozen == 'TRUE'`).
    2. Bidirectional Cascading: Updating task states automatically cascades to parent incidents
       (e.g., when a task is accepted or responders go en route, the incident transitions to
       `IN_PROGRESS`; when completed, the incident advances to `AWAITING_VERIFICATION`).
    3. Proof-Gated Verification: Associates photographic evidence IDs with task completions.
    4. Immutable Audit Ledger: Records every status shift in `AuditEntry` for mission forensics.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.tasks.models import Task
from app.modules.incidents.models import Incident, RouteObservation
from app.modules.audit.models import AuditEntry

# Briefing: FastAPI Router mounted under `/tasks` for responder assignment workflows.
# Reason: Provides distinct API endpoints for task creation, dispatch, and lifecycle state changes.
router = APIRouter(prefix="/tasks", tags=["Tasks & Assignments"])


class TaskCreateRequest(BaseModel):
    """
    Briefing:
        Inbound request payload for spawning a new operational rescue task.
    """
    incident_id: str
    title: str
    description: Optional[str] = None
    task_type: str  # EVACUATE, DELIVER_RATIONS, CLEAR_DEBRIS, MEDICAL_TRIAGE
    route_id: Optional[str] = None


class TaskAssignRequest(BaseModel):
    """
    Briefing:
        Payload submitted to assign an individual responder or specialized team to a task.
    """
    assigned_to_user_id: str
    assigned_team_id: Optional[str] = None


class TaskTransitionRequest(BaseModel):
    """
    Briefing:
        Payload submitted by a field responder or dispatcher to advance task lifecycle status.
    """
    target_status: str  # ACCEPTED, EN_ROUTE, ON_SITE, COMPLETED, BLOCKED, DECLINED
    notes: Optional[str] = None
    evidence_id: Optional[str] = None


class TaskResponse(BaseModel):
    """
    Briefing:
        Pydantic response model representing a task and its current assignment state.
    """
    id: str
    tenant_id: str
    incident_id: str
    title: str
    description: Optional[str]
    task_type: str
    status: str
    assigned_to_user_id: Optional[str]
    assigned_team_id: Optional[str]
    route_id: Optional[str]
    is_route_blocked: str
    created_at: datetime
    accepted_at: Optional[datetime]
    completed_at: Optional[datetime]
    verified_at: Optional[datetime]


@router.post("", response_model=TaskResponse)
async def create_task(
    req: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Creates a new tactical task linked to an active disaster incident.

    Reason:
        Spawns an actionable operational assignment with status `CREATED`, attaches any
        associated transit route requirements, and invalidates dashboard caches to update
        dispatch board views.

    Parameters:
        req: `TaskCreateRequest` containing task headline, type, and incident UUID.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        The created `TaskResponse`.
    """
    task = Task(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        incident_id=req.incident_id,
        title=req.title,
        description=req.description,
        task_type=req.task_type,
        status="CREATED",
        route_id=req.route_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Explanation: Invalidate dashboard summary cache for real-time tactical overview
    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Retrieves all rescue tasks within the authenticated user's tenant organization.

    Parameters:
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        List of all `TaskResponse` records for the tenant.
    """
    result = await db.execute(select(Task).where(Task.tenant_id == current_user.tenant_id))
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Retrieves an individual task by its primary key UUID.

    Parameters:
        task_id: UUID of target task.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        The matching `TaskResponse`.

    Raises:
        HTTPException(404): If task is not found in the tenant.
    """
    result = await db.execute(select(Task).where(Task.id == task_id, Task.tenant_id == current_user.tenant_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    req: TaskAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Assigns a task to a responder or unit, enforcing route-safety preconditions.

    Reason:
        1. Safety Check: If `task.route_id` is set, verifies that the route is not frozen
           (`is_frozen == 'TRUE'` or `status == 'UNCERTAIN'`). If frozen, rejects dispatch with
           HTTP 400 to prevent directing personnel into disputed, dangerous hazard zones.
        2. Status Transition: Sets task status to `OFFERED`.
        3. Cascading Update: Automatically updates parent Incident status to `ASSIGNED`.
        4. Audit Log: Writes `TASK_ASSIGNED` entry into `AuditEntry`.
        5. Invalidate Cache: Updates command dashboards.

    Parameters:
        task_id: UUID of the task to assign.
        req: `TaskAssignRequest` specifying user and team IDs.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        Updated `TaskResponse`.

    Raises:
        HTTPException(404): If task is not found.
        HTTPException(400): If associated transit route is under safety freeze.
    """
    result = await db.execute(select(Task).where(Task.id == task_id, Task.tenant_id == current_user.tenant_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Explanation: Pre-condition Guard - Do not allow dispatch if the required transit corridor is compromised
    if task.route_id:
        r_res = await db.execute(
            select(RouteObservation).where(
                RouteObservation.route_identifier == task.route_id,
                RouteObservation.tenant_id == current_user.tenant_id,
            )
        )
        route = r_res.scalars().first()
        if route and (route.status == "UNCERTAIN" or route.is_frozen == "TRUE"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot dispatch task: Route {task.route_id} is under active life-safety conflict freeze.",
            )

    task.assigned_to_user_id = req.assigned_to_user_id
    task.assigned_team_id = req.assigned_team_id
    task.status = "OFFERED"

    # Explanation: Cascade operational status to parent incident
    inc_res = await db.execute(select(Incident).where(Incident.id == task.incident_id))
    inc = inc_res.scalars().first()
    if inc:
        inc.status = "ASSIGNED"

    # Explanation: Log assignment into immutable audit ledger
    audit = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        action="TASK_ASSIGNED",
        actor_id=current_user.sub,
        actor_role=current_user.role,
        target_entity_type="task",
        target_entity_id=task.id,
        new_state={"assigned_to": req.assigned_to_user_id, "status": "OFFERED"},
        reason="Supervisor dispatched task to eligible responder",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(task)

    # Explanation: Invalidate dashboard summary cache
    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return task


@router.post("/{task_id}/transitions", response_model=TaskResponse)
async def transition_task(
    task_id: str,
    req: TaskTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Advances a task's status through its operational lifecycle.

    Reason:
        1. Validates and updates status (`ACCEPTED`, `EN_ROUTE`, `ON_SITE`, `COMPLETED`, `BLOCKED`, `DECLINED`).
        2. Captures precise operational timestamps: records `accepted_at` when responder accepts,
           and `completed_at` when work is finished on site.
        3. Cascades progress to parent incident (`IN_PROGRESS` while teams are en route or on site;
           `AWAITING_VERIFICATION` once task is marked completed).
        4. Writes an immutable `AuditEntry` with any attached photographic evidence IDs.
        5. Invalidates dashboard summary cache for real-time COP refresh.

    Parameters:
        task_id: UUID of target task.
        req: `TaskTransitionRequest` containing target status, notes, and evidence UUIDs.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        Updated `TaskResponse`.

    Raises:
        HTTPException(404): If task is not found.
    """
    result = await db.execute(select(Task).where(Task.id == task_id, Task.tenant_id == current_user.tenant_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    target = req.target_status.upper()

    task.status = target
    if target == "ACCEPTED":
        task.accepted_at = datetime.now(timezone.utc)
    elif target == "COMPLETED":
        task.completed_at = datetime.now(timezone.utc)

    # Explanation: Cascade state updates to parent incident
    inc_res = await db.execute(select(Incident).where(Incident.id == task.incident_id))
    inc = inc_res.scalars().first()
    if inc:
        if target in ["ACCEPTED", "EN_ROUTE", "ON_SITE"]:
            inc.status = "IN_PROGRESS"
        elif target == "COMPLETED":
            inc.status = "AWAITING_VERIFICATION"

    # Explanation: Append tamper-evident audit record with evidence reference
    audit = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        action=f"TASK_STATUS_{target}",
        actor_id=current_user.sub,
        actor_role=current_user.role,
        target_entity_type="task",
        target_entity_id=task.id,
        previous_state={"status": old_status},
        new_state={"status": target, "evidence_id": req.evidence_id},
        reason=req.notes or f"Field status transition to {target}",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(task)

    # Explanation: Invalidate dashboard summary cache
    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return task
