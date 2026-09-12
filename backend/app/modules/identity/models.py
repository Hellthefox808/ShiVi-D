"""
ShiVi Multi-Tenant Identity, User & Device Authorization Models
===============================================================

Briefing:
    Defines the identity and access management (IAM) schema for the ShiVi disaster coordination
    platform. Supports multi-tenant organizational segregation (`Tenant`), user credentials
    and hierarchical roles (`User`), and physical hardware device registration (`Device`).

Reason:
    Disaster relief brings together civil defense authorities, NGOs (Red Cross, MSF), municipal
    emergency services, and citizen volunteers.
    The Identity models provide:
    1. Strict Multi-Tenant Isolation: Every record belongs to a specific `Tenant`, guaranteeing
       jurisdictional data boundaries (e.g. District A cannot view or alter District B records).
    2. Role-Based Access Control (RBAC): Enforces role tiers (`CITIZEN`, `RESPONDER`, `SUPERVISOR`,
       `ADMIN`) governing which actions an actor can perform (e.g., only SUPERVISOR or ADMIN can
       adjudicate conflicts or approve task completion).
    3. Hardware Device Fingerprinting: Binds users to specific mobile or edge hardware devices,
       tracking monotonic sequence counters (`last_sequence_number`) to prevent replay attacks
       and detect stolen or compromised field radios.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tenant(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing a jurisdictional organization or emergency agency.

    Reason:
        Provides the multi-tenant isolation boundary. Separates local jurisdictions, disaster
        response sectors (e.g., medical command vs fire service), and administrative domains.
    """
    __tablename__ = "tenants"

    # Explanation: Primary key UUID identifying the tenant organization
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Human-readable agency name (e.g., "City Disaster Management Authority")
    name = Column(String, nullable=False)
    
    # Explanation: Unique URL slug for subdomains or routing (e.g., 'cdma-district-4')
    slug = Column(String, unique=True, nullable=False)
    
    # Explanation: Pre-configured sector profile pack ('disaster_response', 'flood_relief', 'wildfire')
    sector_pack = Column(String, default="disaster_response")
    
    # Explanation: Timestamp when tenant was provisioned
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing an individual human responder, commander, or citizen.

    Reason:
        Stores cryptographic password hashes, multi-tenant link, and authoritative role assignment
        which determines RBAC permissions across the operational lifecycle.
    """
    __tablename__ = "users"

    # Explanation: Primary key UUID of the user
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: Unique login identifier (e.g., 'commander.sarah')
    username = Column(String, unique=True, nullable=False)
    
    # Explanation: Optional contact email
    email = Column(String, nullable=True)
    
    # Explanation: Cryptographically salted and stretched PBKDF2/Argon2 password hash
    hashed_password = Column(String, nullable=False)
    
    # Explanation: Official responder full name
    full_name = Column(String, nullable=False)
    
    # Explanation: Operational role: 'CITIZEN', 'RESPONDER', 'SUPERVISOR', 'ADMIN'
    role = Column(String, nullable=False, default="RESPONDER")
    
    # Explanation: Field contact phone number for tactical SMS dispatch
    phone = Column(String, nullable=True)
    
    # Explanation: Active account flag; if False, tokens are rejected
    is_active = Column(Boolean, default=True)
    
    # Explanation: Account creation timestamp in UTC
    created_at = Column(DateTime, default=datetime.utcnow)


class Device(Base):
    """
    Briefing:
        SQLAlchemy ORM model representing a physical smartphone, radio, or edge terminal.

    Reason:
        Enforces zero-trust hardware device authorization. Tracks monotonically increasing
        sequence numbers generated during offline event sync to detect outbox tampering,
        man-in-the-middle replay attacks, or compromised radio nodes.
    """
    __tablename__ = "devices"

    # Explanation: Primary key UUID of the registered device
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    
    # Explanation: User UUID who registered and operates this physical device
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Explanation: Cryptographic or hardware fingerprint (IMEI/UUID hash or secure enclave public key)
    device_fingerprint = Column(String, nullable=False)
    
    # Explanation: Highest sequence counter accepted from this device for monotonic replay rejection
    last_sequence_number = Column(String, default="0")
    
    # Explanation: Revocation flag; when True, all incoming sync traffic from this device is rejected
    is_revoked = Column(Boolean, default=False)
    
    # Explanation: Initial device registration timestamp
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Explanation: Most recent heartbeat or sync connection timestamp
    last_seen_at = Column(DateTime, default=datetime.utcnow)
