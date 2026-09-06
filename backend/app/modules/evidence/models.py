import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from app.core.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    task_id = Column(String, nullable=True)
    incident_id = Column(String, nullable=True)
    
    file_type = Column(String, nullable=False)  # IMAGE, AUDIO, GPS_TRACK, SENSOR
    file_path = Column(String, nullable=False)
    sha256_hash = Column(String, nullable=False)
    byte_size = Column(Integer, default=0)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    gps_accuracy_meters = Column(Float, nullable=True)
    
    captured_by_user_id = Column(String, nullable=True)
    device_id = Column(String, nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    is_verified = Column(String, default="FALSE")
    verified_by_user_id = Column(String, nullable=True)
    verification_notes = Column(Text, nullable=True)
