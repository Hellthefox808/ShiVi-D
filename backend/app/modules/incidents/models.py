import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    local_reference = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False)  # RESCUE, MEDICAL, FLOOD_HAZARD, SHELTER, SUPPLY
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String, default="REPORTED")  # DRAFT, REPORTED, TRIAGED, ASSIGNED, IN_PROGRESS, AWAITING_VERIFICATION, RESOLVED, CLOSED
    
    people_at_risk = Column(Integer, default=0)
    priority_score = Column(Float, default=0.0)
    priority_breakdown = Column(JSON, default=dict)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String, nullable=True)
    
    created_by_user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)


class RouteObservation(Base):
    __tablename__ = "route_observations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    route_identifier = Column(String, nullable=False, index=True)  # e.g. "ROUTE-88"
    status = Column(String, default="UNKNOWN")  # USABLE, BLOCKED, FLOODED, UNCERTAIN
    
    notes = Column(JSON, default=list)  # List of accumulated notes
    photos = Column(JSON, default=list)  # List of photo evidence IDs
    
    last_reported_by = Column(String, nullable=True)
    last_reported_at = Column(DateTime, default=datetime.utcnow)
    is_frozen = Column(String, default="FALSE")  # TRUE if life-safety conflict is pending review
    active_conflict_id = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
