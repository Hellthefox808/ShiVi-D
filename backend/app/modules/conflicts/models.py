import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from app.core.database import Base


class ConflictCase(Base):
    __tablename__ = "conflict_cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    entity_type = Column(String, nullable=False)  # route_observation, task, incident
    entity_id = Column(String, nullable=False)
    conflicting_field = Column(String, nullable=False)  # e.g. status
    
    status = Column(String, default="OPEN")  # OPEN, RESOLVED, REOPENED
    claims = Column(JSON, default=list)  # List of claims: [{actor_id, device_id, value, evidence_ids, occurred_at}]
    
    frozen_dependencies = Column(JSON, default=list)  # List of task IDs frozen due to this conflict
    
    resolved_by_user_id = Column(String, nullable=True)
    resolved_value = Column(String, nullable=True)
    resolution_reason = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
