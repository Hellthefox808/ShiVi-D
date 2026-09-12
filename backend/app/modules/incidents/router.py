"""
ShiVi Incidents & Common Operational Picture (COP) API Router
============================================================

Briefing:
    Provides REST endpoints for reporting, retrieving, and triaging emergency incidents
    across the operational theater. Powers the tactical dashboard Common Operational Picture (COP)
    and mobile field dispatch feeds.

Reason:
    During a disaster, rapid and accurate incident logging is paramount:
    1. Standardized creation: Calculates multi-factor explainable priority scores on ingestion.
    2. Ranked visibility: Sorts incident feeds dynamically by priority score so commanders
       allocate limited rescue teams to the most critical life-safety threats first.
    3. Human-in-the-loop triage: Allows dispatch supervisors to review and override automated
       scores with mandatory rationale, recording an unalterable audit log for accountability.
    4. Real-time tactical sync: Invalids the dashboard aggregate cache on every state mutation
       to keep command displays updated in sub-second intervals.
"""

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

# Briefing: FastAPI Router mounted at `/incidents` for disaster incident operations.
# Reason: Provides isolated, authenticated endpoints for incident lifecycle and COP mapping.
router = APIRouter(prefix="/incidents", tags=["Incidents & COP"])


class IncidentCreateRequest(BaseModel):
    """
    Briefing:
        Inbound request payload for reporting a new disaster incident.

    Reason:
        Gathers critical situational parameters: category, severity, estimated people at risk,
        GPS coordinates for map plotting, and photo evidence indicators for priority calculation.
    """
    # Explanation: Optional client-generated local reference code (e.g. 'INC-A1B2C3')
    local_reference: Optional[str] = None
    # Explanation: Operational category ('RESCUE', 'MEDICAL', 'FLOOD_HAZARD', 'SHELTER', 'SUPPLY')
    category: str
    # Explanation: Short descriptive headline for radio dispatch
    title: str
    # Explanation: Comprehensive narrative description or eyewitness details
    description: Optional[str] = None
    # Explanation: Subjective field severity rating ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    severity: str = "MEDIUM"
    # Explanation: Non-negative estimate of affected or threatened individuals
    people_at_risk: int = 0
    # Explanation: WGS84 Latitude decimal coordinate
    latitude: float
    # Explanation: WGS84 Longitude decimal coordinate
    longitude: float
    # Explanation: Descriptive landmark or address (e.g., "North Levee Breach, Sector 3")
    location_name: Optional[str] = None
    # Explanation: Indicates whether authenticated photo proof accompanies the report
    has_photo_evidence: bool = False


class IncidentTriageRequest(BaseModel):
    """
    Briefing:
        Payload submitted by a dispatch officer or supervisor during incident triage.

    Reason:
        Supports manual priority or severity overrides when field conditions evolve or
        when human commanders possess ground intelligence not captured by automated sensors.
    """
    # Explanation: Manual numerical priority override in range [0.0, 100.0]
    priority_override: Optional[float] = None
    # Explanation: Updated severity classification
    severity_override: Optional[str] = None
    # Explanation: Mandatory written justification for overriding automated triage
    override_reason: Optional[str] = None


class IncidentResponse(BaseModel):
    """
    Briefing:
        Comprehensive response model representing a disaster incident.

    Reason:
        Supplies frontend web dashboards and mobile tactical clients with complete incident state,
        including calculated priority score, mathematical breakdown dictionary, and timestamps.
    """
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
    """
    Briefing:
        Registers a new emergency incident and calculates its multi-factor priority score.

    Reason:
        1. Assigns a standardized local reference code (e.g. `INC-F4E291`) if omitted.
        2. Executes `calculate_incident_priority()` to derive the objective 0-100 priority score
           and generate an explainable breakdown dictionary.
        3. Persists the `Incident` entity within the authenticated user's tenant organization.
        4. Invalidates the central dashboard cache to ensure the incident immediately appears
           on commander radar screens.

    Parameters:
        req: `IncidentCreateRequest` containing incident details and coordinates.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        The newly created `IncidentResponse`.
    """
    local_ref = req.local_reference or f"INC-{uuid.uuid4().hex[:6].upper()}"
    
    # Explanation: Calculate explainable multi-factor priority score
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
    
    # Explanation: Invalidate tactical dashboard summary cache for real-time COP refresh
    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)
    
    return incident


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Retrieves all incidents for the active tenant, ordered by priority score descending.

    Reason:
        Guarantees that commanders and automated dispatch engines view the highest-risk,
        most time-critical life-safety emergencies at the top of their tactical queues.

    Parameters:
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        List of `IncidentResponse` records ordered by `priority_score.desc()`.
    """
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
    """
    Briefing:
        Retrieves an individual incident by its primary key UUID.

    Reason:
        Provides full operational and GIS context when viewing a single incident detail card.

    Parameters:
        incident_id: UUID of target incident.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        The requested `IncidentResponse`.

    Raises:
        HTTPException(404): If the incident does not exist in the tenant.
    """
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
    """
    Briefing:
        Executes formal commander triage, applying overrides and recording an immutable audit entry.

    Reason:
        When commanders identify special circumstances (e.g. elderly residents in shelter, toxic fumes),
        they can adjust severity or force a priority override. To prevent rogue modifications,
        the action:
        1. Updates incident status from 'REPORTED' to 'TRIAGED'.
        2. Recalculates mathematical priority or records manual override flags with reason.
        3. Appends an unalterable `AuditEntry` into the audit ledger documenting previous vs new scores.
        4. Invalidates dashboard cache to reflect the new triage status.

    Parameters:
        incident_id: UUID of the incident to triage.
        req: `IncidentTriageRequest` specifying overrides and justification.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        The updated `IncidentResponse`.

    Raises:
        HTTPException(404): If incident is not found.
    """
    result = await db.execute(
        select(Incident).where(
            Incident.id == incident_id, Incident.tenant_id == current_user.tenant_id
        )
    )
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    prev_score = incident.priority_score
    # Explanation: If severity was modified, re-run algorithmic priority calculator
    if req.severity_override:
        incident.severity = req.severity_override
        score, breakdown = calculate_incident_priority(
            severity=incident.severity,
            people_at_risk=incident.people_at_risk,
            category=incident.category,
        )
        incident.priority_score = score
        incident.priority_breakdown = breakdown
        
    # Explanation: If direct priority override was specified, apply and tag metadata
    if req.priority_override is not None:
        incident.priority_score = req.priority_override
        incident.priority_breakdown["manual_override"] = True
        incident.priority_breakdown["override_reason"] = req.override_reason or "Manual supervisor adjustment"

    incident.status = "TRIAGED"
    
    # Explanation: Record tamper-evident AuditEntry documenting who triaged and why
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

    # Explanation: Invalidate dashboard summary cache
    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return incident
