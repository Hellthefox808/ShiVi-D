import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.tasks.models import Task
from app.modules.incidents.models import Incident, RouteObservation
from app.modules.audit.models import AuditEntry

router = APIRouter(prefix="/tasks", tags=["Tasks & Assignments"])


class TaskCreateRequest(BaseModel):
    incident_id: str
    title: str
    description: Optional[str] = None
    task_type: str  # EVACUATE, DELIVER_RATIONS, CLEAR_DEBRIS, MEDICAL_TRIAGE
    route_id: Optional[str] = None


class TaskAssignRequest(BaseModel):
    assigned_to_user_id: str
    assigned_team_id: Optional[str] = None


class TaskTransitionRequest(BaseModel):
    target_status: str  # ACCEPTED, EN_ROUTE, ON_SITE, COMPLETED, BLOCKED, DECLINED
    notes: Optional[str] = None
    evidence_id: Optional[str] = None


class TaskResponse(BaseModel):
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
    return task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    result = await db.execute(select(Task).where(Task.tenant_id == current_user.tenant_id))
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
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
    result = await db.execute(select(Task).where(Task.id == task_id, Task.tenant_id == current_user.tenant_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # If task has a route that is frozen or uncertain, warn supervisor
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

    # Also update incident status to ASSIGNED
    inc_res = await db.execute(select(Incident).where(Incident.id == task.incident_id))
    inc = inc_res.scalars().first()
    if inc:
        inc.status = "ASSIGNED"

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
    return task


@router.post("/{task_id}/transitions", response_model=TaskResponse)
async def transition_task(
    task_id: str,
    req: TaskTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
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

    # Update incident progress
    inc_res = await db.execute(select(Incident).where(Incident.id == task.incident_id))
    inc = inc_res.scalars().first()
    if inc:
        if target in ["ACCEPTED", "EN_ROUTE", "ON_SITE"]:
            inc.status = "IN_PROGRESS"
        elif target == "COMPLETED":
            inc.status = "AWAITING_VERIFICATION"

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
    return task
