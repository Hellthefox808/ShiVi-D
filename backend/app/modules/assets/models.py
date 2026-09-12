"""
ShiVi Physical Assets & Custody Leases Data Models
==================================================

Briefing:
    Defines the persistence schemas for tracking physical emergency equipment (`PhysicalAsset`)
    and custody allocation claims (`AssetAllocationClaim`). Manages mission-critical resources
    such as de-watering pumps, inflatable rescue boats, emergency generators, ambulances,
    drones, and trauma supplies across field depots and incident sites.

Reason:
    Physical equipment cannot be duplicated digitally. In disconnected operations, if two
    teams record claims on the same boat, a digital reconciliation model is needed:
    1. Physical Proof Tracking: Flags whether custody is confirmed by hardware sensors
       (`has_physical_proof`), recording proof types (NFC tap, QR code, GPS proximity).
    2. Dynamic Status Progression: Tracks resource availability (`AVAILABLE`, `IN_USE`,
       `IN_TRANSIT`, `CONTENTION_WARNING`, `MAINTENANCE`).
    3. Custody Leases: Records active and historical allocation claims, capturing priority
       scores and linking substitute equipment assignments when contention occurs.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float, Boolean, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class PhysicalAsset(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing a physical piece of emergency equipment.

    Reason:
        Maintains current geospatial location, custody holder, and proof of physical possession.
        Provides the source of truth for equipment availability across all tactical depots.
    """
    __tablename__ = "physical_assets"

    # Explanation: Primary key UUID of the asset record
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: Human-readable asset code stenciled on equipment (e.g. 'PUMP-75HP-01', 'BOAT-ZODIAC-03')
    asset_code = Column(String, nullable=False, index=True)
    
    # Explanation: Descriptive name of the asset
    name = Column(String, nullable=False)
    
    # Explanation: Equipment category: 'GENERATOR', 'PUMP', 'VEHICLE', 'BOAT', 'DRONE', 'MEDICAL'
    category = Column(String, nullable=False)
    
    # Explanation: Operational status: 'AVAILABLE', 'IN_USE', 'IN_TRANSIT', 'CONTENTION_WARNING', 'MAINTENANCE'
    status = Column(String, default="AVAILABLE")
    
    # Explanation: Current depot or field staging area name (e.g., 'Sector 3 Staging Depot')
    current_location_name = Column(String, nullable=True)
    
    # Explanation: WGS84 Latitude of current position
    latitude = Column(Float, nullable=True)
    
    # Explanation: WGS84 Longitude of current position
    longitude = Column(Float, nullable=True)
    
    # Custody Holder Information
    # Explanation: User UUID or Team ID currently possessing or operating the equipment
    current_holder_id = Column(String, nullable=True)
    # Explanation: Task UUID for which the equipment is currently deployed
    current_task_id = Column(String, nullable=True)
    # Explanation: Incident UUID this equipment is actively serving
    current_incident_id = Column(String, nullable=True)
    
    # Physical Possession Verification
    # Explanation: True if custody was physically verified via hardware sensor at the equipment
    has_physical_proof = Column(Boolean, default=False)
    # Explanation: Verification method: 'NFC_TAP', 'QR_SCAN', 'GPS_PROXIMITY_15M', 'PHOTO_EVIDENCE'
    physical_proof_type = Column(String, nullable=True)
    # Explanation: UTC timestamp when physical proof was recorded
    physical_proof_timestamp = Column(DateTime, nullable=True)
    
    # Explanation: Creation timestamp in UTC
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Explanation: Last updated timestamp in UTC
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AssetAllocationClaim(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing a formal reservation or custody claim on an asset.

    Reason:
        Records every checkout attempt, storing the claim type, priority score of the requesting
        incident, sensor proof data, and substitute equipment linkage if contention occurred.
    """
    __tablename__ = "asset_allocation_claims"

    # Explanation: Primary key UUID of the claim
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: Foreign key linking to the requested `PhysicalAsset`
    asset_id = Column(String, ForeignKey("physical_assets.id"), nullable=False)
    
    # Explanation: User UUID of the responder or commander submitting the claim
    claimant_id = Column(String, nullable=False)
    
    # Explanation: Optional team identifier
    team_id = Column(String, nullable=True)
    
    # Explanation: Incident UUID that requires the asset
    incident_id = Column(String, nullable=False)
    
    # Explanation: Specific task UUID the asset will perform
    task_id = Column(String, nullable=False)
    
    # Explanation: Claim category: 'PHYSICAL_POSSESSION' (verified on-site) or 'VIRTUAL_RESERVATION'
    claim_type = Column(String, default="VIRTUAL_RESERVATION")
    
    # Explanation: Telemetry supporting claim (e.g. NFC UID, GPS coordinates, photo hash)
    proof_data = Column(JSON, default=dict)
    
    # Explanation: Multi-factor priority score (0.0 - 100.0) of the requesting incident
    priority_score = Column(Float, default=50.0)
    
    # Explanation: Claim status: 'ACTIVE', 'REPLACED_WITH_SUBSTITUTE', 'SUPERSEDED', 'RELEASED'
    claim_status = Column(String, default="ACTIVE")
    
    # Explanation: Foreign UUID of substitute equipment assigned if primary was contended
    substitute_asset_id = Column(String, nullable=True)
    # Explanation: Asset code of substitute equipment
    substitute_asset_code = Column(String, nullable=True)
    
    # Explanation: Timestamp when claim was initiated
    claimed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Explanation: Timestamp when claim was resolved or released
    resolved_at = Column(DateTime, nullable=True)
