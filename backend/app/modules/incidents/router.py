import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.incidents.models import Incident, RouteObservation
from app.modules.incidents.priority import calculate_incident_priority
from app.modules.audit.models import AuditEntry

router = APIRouter(prefix="/incidents", tags=["Incidents & COP"])


class IncidentCreateRequest(BaseModel):
    local_reference: Optional[str] = None
    category: str
    title: str
    description: Optional[str] = None
    severity: str = "MEDIUM"
    people_at_risk: int = 0
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    has_photo_evidence: bool = False


class IncidentTriageRequest(BaseModel):
    priority_override: Optional[float] = None
    severity_override: Optional[str] = None
    override_reason: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    tenant_id: str
    local_reference: str
    category: str
    title: str
    description: Optional[str]
    severity: str
    status: str
    people_at_risk: int
    priority_score: float
    priority_breakdown: Dict[str, Any]
    latitude: float
    longitude: float
    location_name: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.post("", response_model=IncidentResponse)
async def create_incident(
    req: IncidentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    local_ref = req.local_reference or f"INC-{uuid.uuid4().hex[:6].upper()}"
    
    score, breakdown = calculate_incident_priority(
        severity=req.severity,
        people_at_risk=req.people_at_risk,
        category=req.category,
        has_photo_evidence=req.has_photo_evidence,
    )
    
    incident = Incident(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        local_reference=local_ref,
        category=req.category,
        title=req.title,
        description=req.description,
        severity=req.severity,
        status="REPORTED",
        people_at_risk=req.people_at_risk,
        priority_score=score,
        priority_breakdown=breakdown,
        latitude=req.latitude,
        longitude=req.longitude,
        location_name=req.location_name,
        created_by_user_id=current_user.sub,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    
    return incident


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    result = await db.execute(
        select(Incident)
        .where(Incident.tenant_id == current_user.tenant_id)
        .order_by(Incident.priority_score.desc())
    )
    return result.scalars().all()


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    result = await db.execute(
        select(Incident).where(
            Incident.id == incident_id, Incident.tenant_id == current_user.tenant_id
        )
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/triage", response_model=IncidentResponse)
async def triage_incident(
    incident_id: str,
    req: IncidentTriageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    result = await db.execute(
        select(Incident).where(
            Incident.id == incident_id, Incident.tenant_id == current_user.tenant_id
        )
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    prev_score = incident.priority_score
    if req.severity_override:
        incident.severity = req.severity_override
        score, breakdown = calculate_incident_priority(
            severity=incident.severity,
            people_at_risk=incident.people_at_risk,
            category=incident.category,
        )
        incident.priority_score = score
        incident.priority_breakdown = breakdown
        
    if req.priority_override is not None:
        incident.priority_score = req.priority_override
        incident.priority_breakdown["manual_override"] = True
        incident.priority_breakdown["override_reason"] = req.override_reason or "Manual supervisor adjustment"

    incident.status = "TRIAGED"
    
    # Record protected audit entry
    audit = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        action="INCIDENT_TRIAGED",
        actor_id=current_user.sub,
        actor_role=current_user.role,
        target_entity_type="incident",
        target_entity_id=incident.id,
        previous_state={"priority_score": prev_score, "status": "REPORTED"},
        new_state={"priority_score": incident.priority_score, "status": "TRIAGED"},
        reason=req.override_reason or "Standard supervisor triage",
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(incident)
    return incident
