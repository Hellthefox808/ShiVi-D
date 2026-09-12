"""
ShiVi Cryptographic Evidence & Binary Attachments Data Models
============================================================

Briefing:
    Defines the persistence model for physical evidence records (`Evidence`), including
    field reconnaissance photos, voice memos, GPS track logs, and environmental sensor readings.
    Provides verifiable proof for completed tasks, road blockages, and casualty reports.

Reason:
    In disaster zones, unverified reports cause misdirection of scarce resources.
    The Evidence model enforces:
    1. Cryptographic Tamper-Evidence: Stores the SHA-256 hash of the binary file calculated
       locally on the capturing device at the moment of capture, ensuring image data has not
       been altered or corrupted in transit.
    2. Physical Provenance: Records capturing user UUID, hardware device ID, GPS coordinates,
       GPS accuracy in meters, and physical capture timestamp.
    3. Verification Lifecycle: Tracks supervisor sign-off (`is_verified = 'TRUE'`) required
       before high-consequence rescue tasks can be marked closed.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from app.core.database import Base


class Evidence(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing a verified multimedia or telemetry attachment.

    Reason:
        Serves as immutable proof supporting task completion claims, route obstruction reports,
        and incident triage assessments. Links directly to tasks and incidents while preserving
        full cryptographic integrity and spatial provenance.
    """
    __tablename__ = "evidence"

    # Explanation: Primary key UUID identifying the evidence attachment
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: Optional foreign UUID of the task this evidence proves completed
    task_id = Column(String, nullable=True)
    
    # Explanation: Optional foreign UUID of the incident this evidence documents
    incident_id = Column(String, nullable=True)
    
    # Explanation: Media category: 'IMAGE', 'AUDIO', 'GPS_TRACK', 'SENSOR'
    file_type = Column(String, nullable=False)
    
    # Explanation: Canonical filesystem or object storage path (e.g. 'uploads/tenant_1/ev_123.jpg')
    file_path = Column(String, nullable=False)
    
    # Explanation: SHA-256 cryptographic digest of the raw binary data computed at capture
    sha256_hash = Column(String, nullable=False)
    
    # Explanation: Total binary size in bytes
    byte_size = Column(Integer, default=0)
    
    # Explanation: WGS84 Latitude where media was captured
    latitude = Column(Float, nullable=True)
    
    # Explanation: WGS84 Longitude where media was captured
    longitude = Column(Float, nullable=True)
    
    # Explanation: GPS receiver horizontal dilution/accuracy in meters
    gps_accuracy_meters = Column(Float, nullable=True)
    
    # Explanation: User UUID of the field responder who captured the evidence
    captured_by_user_id = Column(String, nullable=True)
    
    # Explanation: Physical hardware device identifier that took the photo or reading
    device_id = Column(String, nullable=True)
    
    # Explanation: Physical timestamp recorded at moment of capture in the field
    captured_at = Column(DateTime, default=datetime.utcnow)
    
    # Explanation: Server timestamp when binary was received across network
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Explanation: Verification flag: 'TRUE' if approved by supervisor, 'FALSE' if unverified
    is_verified = Column(String, default="FALSE")
    
    # Explanation: User UUID of the supervisor who reviewed and approved the evidence
    verified_by_user_id = Column(String, nullable=True)
    
    # Explanation: Written notes or comments from supervisor review
    verification_notes = Column(Text, nullable=True)
