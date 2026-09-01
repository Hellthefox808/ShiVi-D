import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.tasks.models import Task
from app.modules.incidents.models import Incident
from app.modules.evidence.models import Evidence
from app.modules.audit.models import AuditEntry

router = APIRouter(prefix="/verifications", tags=["Task Verification & Closure"])


class VerificationRequest(BaseModel):
    task_id: str
    is_approved: bool
    notes: Optional[str] = None


class VerificationResponse(BaseModel):
    status: str
    task_id: str
    task_status: str
    incident_status: str
    verified_at: datetime


@router.post("", response_model=VerificationResponse)
async def verify_task_completion(
    req: VerificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    result = await db.execute(
        select(Task).where(Task.id == req.task_id, Task.tenant_id == current_user.tenant_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    inc_res = await db.execute(select(Incident).where(Incident.id == task.incident_id))
    incident = inc_res.scalars().first()

    now = datetime.utcnow()

    if req.is_approved:
        task.status = "VERIFIED"
        task.verified_at = now
        if incident:
            incident.status = "RESOLVED"
            incident.updated_at = now
    else:
        task.status = "FAILED_VERIFICATION"
        if incident:
            incident.status = "IN_PROGRESS"

    audit = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        action="TASK_COMPLETION_VERIFIED" if req.is_approved else "TASK_VERIFICATION_REJECTED",
        actor_id=current_user.sub,
        actor_role=current_user.role,
        target_entity_type="task",
        target_entity_id=task.id,
        previous_state={"status": "COMPLETED"},
        new_state={"status": task.status, "verified": req.is_approved},
        reason=req.notes or "Supervisor verified task completion evidence",
    )
    db.add(audit)

    await db.commit()
    await db.refresh(task)

    return VerificationResponse(
        status="success",
        task_id=task.id,
        task_status=task.status,
        incident_status=incident.status if incident else "RESOLVED",
        verified_at=now,
    )
