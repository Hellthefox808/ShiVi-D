"""
ShiVi Conflict Resolution Data Models
=====================================

Briefing:
    Defines the database schema and persistence model for tracking and adjudicating
    distributed synchronization conflicts (`ConflictCase`). When two or more field
    responders submit contradictory mutations regarding critical physical reality
    (e.g., Responder A marks a bridge as USABLE while Responder B marks it as BLOCKED),
    ShiVi creates an immutable `ConflictCase` record.

Reason:
    Standard distributed systems employ Last-Write-Wins (LWW) or CRDTs. However, in
    disaster operations, blind LWW can send rescue convoys into collapsed bridges or
    flooded ravines. ShiVi halts automated reconciliation for life-safety fields, creates
    a `ConflictCase` holding both opposing claims, freezes dependent operational workflows,
    and requires an authorized Incident Commander or Supervisor to explicitly review
    evidence and adjudicate a resolution.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from app.core.database import Base


class ConflictCase(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing an active or historical operational conflict case.

    Reason:
        Maintains an auditable record of concurrent field contradictions. Captures opposing
        claims (with timestamps, actor IDs, device IDs, and evidence photo links), records
        which dependent rescue tasks have been locked in safety freeze, and stores the human
        supervisor's formal adjudication rationale.
    """
    __tablename__ = "conflict_cases"

    # Explanation: Primary key UUID identifying the conflict case across all mesh nodes
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: Target entity category undergoing contradiction ('route_observation', 'task', 'incident')
    entity_type = Column(String, nullable=False)  # route_observation, task, incident
    
    # Explanation: Unique identifier of the specific entity under conflict (e.g. route segment ID)
    entity_id = Column(String, nullable=False)
    
    # Explanation: The specific field attribute exhibiting contradictory states (e.g., 'status', 'hazard_level')
    conflicting_field = Column(String, nullable=False)  # e.g. status
    
    # Explanation: Workflow lifecycle status: 'OPEN' (active freeze), 'RESOLVED' (adjudicated), 'REOPENED'
    status = Column(String, default="OPEN")  # OPEN, RESOLVED, REOPENED
    
    # Explanation: JSON array preserving all competing assertions from field responders:
    # [{actor_id, device_id, value, evidence_ids, occurred_at}]
    claims = Column(JSON, default=list)
    
    # Explanation: Array of dependent Task UUIDs currently locked/frozen until this conflict is resolved
    frozen_dependencies = Column(JSON, default=list)
    
    # Explanation: User UUID of the Commander/Supervisor who adjudicated this conflict
    resolved_by_user_id = Column(String, nullable=True)
    
    # Explanation: Final adjudicated canonical value selected by the human supervisor (e.g. 'BLOCKED')
    resolved_value = Column(String, nullable=True)
    
    # Explanation: Mandatory operational justification and rationale entered during human resolution
    resolution_reason = Column(Text, nullable=True)
    
    # Explanation: Timestamp when human adjudication occurred
    resolved_at = Column(DateTime, nullable=True)
    
    # Explanation: System creation timestamp in UTC
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Explanation: Last updated timestamp in UTC
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
