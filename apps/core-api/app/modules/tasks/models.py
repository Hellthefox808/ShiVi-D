import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String, nullable=False)  # EVACUATE, DELIVER_RATIONS, CLEAR_DEBRIS, MEDICAL_TRIAGE
    status = Column(String, default="CREATED")  # CREATED, OFFERED, ACCEPTED, EN_ROUTE, ON_SITE, COMPLETED, VERIFIED, BLOCKED, CANCELLED
    
    assigned_to_user_id = Column(String, nullable=True)
    assigned_team_id = Column(String, nullable=True)
    required_skills = Column(JSON, default=list)
    
    route_id = Column(String, nullable=True)  # Associated route if applicable
    is_route_blocked = Column(String, default="FALSE")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)
