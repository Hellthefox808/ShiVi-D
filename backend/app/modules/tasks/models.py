"""
ShiVi Tactical Tasks & Field Assignments Data Models
====================================================

Briefing:
    Defines the persistence model for operational rescue tasks and responder assignments (`Task`).
    Tasks represent concrete actionable field assignments generated from triaged incidents
    (e.g., evacuating a vulnerable family, delivering water purification rations, clearing
    debris from a vital corridor, or performing triage on injured victims).

Reason:
    During disaster coordination, dispatching responders without deterministic lifecycle tracking
    leads to duplicated efforts or abandoned casualties.
    The Task model provides:
    1. Incident Parentage: Every task is strongly linked to an originating `Incident`.
    2. Finite State Progression: Enforces a strict status lifecycle:
       `CREATED` -> `OFFERED` -> `ACCEPTED` -> `EN_ROUTE` -> `ON_SITE` -> `COMPLETED` -> `VERIFIED`.
    3. Route Coupling & Safety Freezes: Links tasks to tactical transit corridors via `route_id`
       and stores the `is_route_blocked` flag. If a route observation triggers a safety freeze,
       dependent tasks are automatically locked to prevent responders from heading into blocked areas.
    4. Auditable Timestamps: Captures exact UTC timestamps for creation, acceptance, completion,
       and cryptographic evidence verification.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from app.core.database import Base


class Task(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing an individual emergency task assignment.

    Reason:
        Maintains the complete operational lifecycle of a field mission, tracking who was assigned,
        which team is responsible, transit route dependency status, and verification milestones.
    """
    __tablename__ = "tasks"

    # Explanation: Primary key UUID identifying the task across all edge nodes
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: Foreign key linking this task to its parent disaster incident
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    
    # Explanation: Headline describing the operational assignment
    title = Column(String, nullable=False)
    
    # Explanation: Step-by-step instructions, equipment requirements, or victim notes
    description = Column(Text, nullable=True)
    
    # Explanation: Tactical mission category: 'EVACUATE', 'DELIVER_RATIONS', 'CLEAR_DEBRIS', 'MEDICAL_TRIAGE'
    task_type = Column(String, nullable=False)
    
    # Explanation: Lifecycle status:
    # 'CREATED', 'OFFERED', 'ACCEPTED', 'EN_ROUTE', 'ON_SITE', 'COMPLETED', 'VERIFIED', 'BLOCKED', 'CANCELLED'
    status = Column(String, default="CREATED")
    
    # Explanation: User UUID of the primary individual responder assigned
    assigned_to_user_id = Column(String, nullable=True)
    
    # Explanation: Team or unit identifier assigned to execute this task
    assigned_team_id = Column(String, nullable=True)
    
    # Explanation: JSON array of required responder competencies (e.g., ['SWIFT_WATER_RESCUE', 'EMT_PARAMEDIC'])
    required_skills = Column(JSON, default=list)
    
    # Explanation: Identifier of the primary transit corridor required to reach the task site
    route_id = Column(String, nullable=True)
    
    # Explanation: String boolean ('TRUE'/'FALSE') indicating if the access route is currently blocked or frozen
    is_route_blocked = Column(String, default="FALSE")
    
    # Explanation: Timestamp when the task was initially created
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Explanation: Timestamp when a responder formally accepted the dispatch
    accepted_at = Column(DateTime, nullable=True)
    
    # Explanation: Timestamp when the responder marked the assignment completed on the ground
    completed_at = Column(DateTime, nullable=True)
    
    # Explanation: Timestamp when supervisor or photographic cryptographic proof verified completion
    verified_at = Column(DateTime, nullable=True)
    
    # Explanation: Optimistic concurrency version counter
    version = Column(Integer, default=1)
