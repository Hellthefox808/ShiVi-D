"""
ShiVi Incidents & Route Observations Data Models
================================================

Briefing:
    Defines the persistence schema for physical disaster incidents (`Incident`) and
    tactical road/access corridor assessments (`RouteObservation`). Incidents represent
    real-world emergency events (e.g., collapsed buildings, flash floods, medical emergencies),
    while RouteObservations track the physical traversability of critical rescue transit routes.

Reason:
    During a disaster, field units report incidents and road conditions from diverse edge
    radios. Maintaining strongly-typed SQLAlchemy schemas with multi-tenant partitioning,
    explainable priority score breakdowns, GPS coordinates, and route freeze markers guarantees:
    1. Incident Commanders maintain a real-time Common Operational Picture (COP).
    2. Route traversability updates dynamically link to active rescue convoys.
    3. Conflicting reports on road blocks trigger an explicit `is_frozen = 'TRUE'` safety lock,
       preventing emergency teams from being dispatched along compromised routes.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Incident(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing a verified or reported disaster incident.

    Reason:
        Central entity for emergency operations. Stores multi-factor algorithmic priority scores,
        people-at-risk counts, geospatial coordinates for tactical map rendering, and full
        audit lifecycle status progression (REPORTED -> TRIAGED -> ASSIGNED -> IN_PROGRESS ->
        AWAITING_VERIFICATION -> RESOLVED).
    """
    __tablename__ = "incidents"

    # Explanation: Primary key UUID identifying the incident across all nodes
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: Human-readable reference code for radio dispatch (e.g., 'INC-4A7F9B')
    local_reference = Column(String, nullable=False, index=True)
    
    # Explanation: Emergency category: 'RESCUE', 'MEDICAL', 'FLOOD_HAZARD', 'SHELTER', 'SUPPLY'
    category = Column(String, nullable=False)
    
    # Explanation: Short operational title of the incident
    title = Column(String, nullable=False)
    
    # Explanation: Detailed situational notes, descriptions, or witness testimony
    description = Column(Text, nullable=True)
    
    # Explanation: Field severity rating: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    severity = Column(String, default="MEDIUM")
    
    # Explanation: Workflow progression state:
    # 'DRAFT', 'REPORTED', 'TRIAGED', 'ASSIGNED', 'IN_PROGRESS', 'AWAITING_VERIFICATION', 'RESOLVED', 'CLOSED'
    status = Column(String, default="REPORTED")
    
    # Explanation: Estimated number of trapped, injured, or vulnerable individuals
    people_at_risk = Column(Integer, default=0)
    
    # Explanation: Multi-factor explainable priority score in range [0.0, 100.0]
    priority_score = Column(Float, default=0.0)
    
    # Explanation: Detailed JSON dictionary explaining each mathematical contribution to priority_score
    priority_breakdown = Column(JSON, default=dict)
    
    # Explanation: WGS84 Latitude coordinate for GIS mapping
    latitude = Column(Float, nullable=False)
    
    # Explanation: WGS84 Longitude coordinate for GIS mapping
    longitude = Column(Float, nullable=False)
    
    # Explanation: Human-readable landmark or address (e.g. "Sector 4 Bridge Overpass")
    location_name = Column(String, nullable=True)
    
    # Explanation: User UUID who originally created or reported this incident
    created_by_user_id = Column(String, nullable=True)
    
    # Explanation: System creation timestamp in UTC
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Explanation: Last updated timestamp in UTC
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Explanation: Optimistic concurrency version counter
    version = Column(Integer, default=1)


class RouteObservation(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing physical road and corridor observations.

    Reason:
        Ground transport of medical supplies, boats, and rescue teams depends on accurate
        road traversability data. RouteObservation records whether a path is USABLE, BLOCKED,
        or FLOODED, accumulates field photos and notes, and holds the `is_frozen` flag when
        conflicting reports are undergoing supervisor adjudication.
    """
    __tablename__ = "route_observations"

    # Explanation: Primary key UUID of the observation record
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: Tactical route identifier or corridor tag (e.g., 'ROUTE-88', 'HWY-101-KM24')
    route_identifier = Column(String, nullable=False, index=True)
    
    # Explanation: Physical status: 'USABLE', 'BLOCKED', 'FLOODED', 'UNCERTAIN'
    status = Column(String, default="UNKNOWN")
    
    # Explanation: JSON array of textual observations submitted by field teams
    notes = Column(JSON, default=list)
    
    # Explanation: JSON array of photographic evidence UUIDs verifying physical road conditions
    photos = Column(JSON, default=list)
    
    # Explanation: User UUID of the responder who last submitted a report on this route
    last_reported_by = Column(String, nullable=True)
    
    # Explanation: Timestamp of the most recent field report
    last_reported_at = Column(DateTime, default=datetime.utcnow)
    
    # Explanation: Flag indicating life-safety freeze ('TRUE' or 'FALSE').
    # When TRUE, no rescue tasks may be routed across this corridor.
    is_frozen = Column(String, default="FALSE")
    
    # Explanation: Foreign key to `conflict_cases.id` if an active contradiction is pending review
    active_conflict_id = Column(String, nullable=True)
    
    # Explanation: Last updated timestamp in UTC
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
