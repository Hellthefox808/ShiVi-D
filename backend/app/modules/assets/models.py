"""
Asset & Physical Possession Leases Model
Manages physical resource allocations, custody leases, NFC/QR proofs, and contention cases.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float, Boolean, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class PhysicalAsset(Base):
    __tablename__ = "physical_assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    asset_code = Column(String, nullable=False, index=True)  # e.g., "GEN-PUMP-01", "AMBULANCE-04"
    name = Column(String, nullable=False)  # "High-Capacity De-Watering Pump 75HP"
    category = Column(String, nullable=False)  # GENERATOR, PUMP, VEHICLE, BOAT, DRONE, MEDICAL
    
    status = Column(String, default="AVAILABLE")  # AVAILABLE, IN_USE, IN_TRANSIT, CONTENTION_WARNING, MAINTENANCE
    current_location_name = Column(String, nullable=True)  # e.g., "Sector 3 Staging Depot"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Current Custody Holder
    current_holder_id = Column(String, nullable=True)  # User ID or Team ID
    current_task_id = Column(String, nullable=True)
    current_incident_id = Column(String, nullable=True)
    
    # Physical Possession Verification
    has_physical_proof = Column(Boolean, default=False)
    physical_proof_type = Column(String, nullable=True)  # NFC_TAP, QR_SCAN, GPS_PROXIMITY_15M, PHOTO_EVIDENCE
    physical_proof_timestamp = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AssetAllocationClaim(Base):
    __tablename__ = "asset_allocation_claims"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    asset_id = Column(String, ForeignKey("physical_assets.id"), nullable=False)
    
    claimant_id = Column(String, nullable=False)  # Responder or Team Lead User ID
    team_id = Column(String, nullable=True)
    incident_id = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    
    claim_type = Column(String, default="VIRTUAL_RESERVATION")  # VIRTUAL_RESERVATION or PHYSICAL_POSSESSION
    proof_data = Column(JSON, default=dict)  # e.g. {"nfc_uid": "04A1B2C3", "gps": [26.18, 91.74], "photo_hash": "..."}
    
    priority_score = Column(Float, default=50.0)  # Calculated incident priority (0-100)
    claim_status = Column(String, default="ACTIVE")  # ACTIVE, REPLACED_WITH_SUBSTITUTE, SUPERSEDED, RELEASED
    
    substitute_asset_id = Column(String, nullable=True)  # If substituted, points to alternate asset
    substitute_asset_code = Column(String, nullable=True)
    
    claimed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
