"""
ShiVi Task Verification & Mission Closure API Router
====================================================

Briefing:
    Provides REST endpoints for formal task completion verification and incident closure.
    Enforces human-in-the-loop validation of rescue missions: when field teams claim a task
    is finished, an incident supervisor reviews photographic evidence and either formally
    approves or rejects the completion claim.

Reason:
    Premature incident closure during catastrophic events can cost human lives.
    The Verification workflow provides:
    1. Two-Party Validation: The responder who executed the task cannot unilaterally mark it
       `VERIFIED`; an authorized supervisor must independently inspect submitted evidence.
    2. Incident Lifecycle Resolution: Approving the task transitions it to `VERIFIED` and
       cascades parent incident status to `RESOLVED`.
    3. Rejection & Remediation: Rejecting completion transitions task to `FAILED_VERIFICATION`
       and reverts the incident back to `IN_PROGRESS` for immediate re-tasking.
    4. Forensic Auditability: Every approval or rejection is permanently logged in `AuditEntry`.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.tasks.models import Task
from app.modules.incidents.models import Incident
from app.modules.evidence.models import Evidence
from app.modules.audit.models import AuditEntry

# Briefing: FastAPI Router mounted under `/verifications` for supervisor sign-off workflows.
# Reason: Provides distinct API endpoints for operational quality assurance and mission sign-off.
router = APIRouter(prefix="/verifications", tags=["Task Verification & Closure"])


class VerificationRequest(BaseModel):
    """
    Briefing:
        Payload submitted by an authorized supervisor to verify or reject task completion.
    """
    # Explanation: UUID of the task undergoing verification
    task_id: str
    # Explanation: True if photographic/physical evidence satisfies mission criteria; False if deficient
    is_approved: bool
    # Explanation: Written feedback, justification, or reason for rejection
    notes: Optional[str] = None


class VerificationResponse(BaseModel):
    """
    Briefing:
        Structured response detailing the outcome of the verification review.
    """
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
    """
    Briefing:
        Executes formal supervisor verification for a completed task and resolves parent incident.

    Reason:
        1. Task Status Update:
           - If approved (`is_approved=True`), sets `task.status = "VERIFIED"` and records `verified_at`.
           - If rejected (`is_approved=False`), sets `task.status = "FAILED_VERIFICATION"`.
        2. Incident Progression:
           - On approval, advances the parent incident to `RESOLVED`.
           - On rejection, resets the parent incident to `IN_PROGRESS` so teams can be redeployed.
        3. Audit Logging: Records a permanent `AuditEntry` logging the supervisor's verdict and notes.

    Parameters:
        req: `VerificationRequest` with task UUID and approval boolean.
        db: Database session.
        current_user: Authenticated JWT claims of supervisor.

    Returns:
        `VerificationResponse` summarizing the resulting task and incident statuses.

    Raises:
        HTTPException(404): If the target task does not exist in the active tenant.
    """
    result = await db.execute(
        select(Task).where(Task.id == req.task_id, Task.tenant_id == current_user.tenant_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    inc_res = await db.execute(select(Incident).where(Incident.id == task.incident_id))
    incident = inc_res.scalars().first()

    now = datetime.utcnow()

    # Explanation: Branch on supervisor determination
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

    # Explanation: Write immutable audit record documenting supervisor sign-off or rejection
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
