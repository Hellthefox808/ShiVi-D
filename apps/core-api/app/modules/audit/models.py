import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text
from app.core.database import Base


class OperationalEvent(Base):
    __tablename__ = "operational_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    event_id = Column(String, unique=True, nullable=False, index=True)
    
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    
    changes = Column(JSON, nullable=False)
    actor_id = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    device_sequence = Column(Integer, nullable=False)
    
    occurred_at = Column(DateTime, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    version_vector = Column(JSON, default=dict)
    evidence_ids = Column(JSON, default=list)
    
    integrity_hash = Column(String, nullable=False)


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    action = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    actor_role = Column(String, nullable=False)
    
    target_entity_type = Column(String, nullable=False)
    target_entity_id = Column(String, nullable=False)
    
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
