"""
ShiVi Operational Event Contracts & Pydantic Models
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    INCIDENT = "incident"
    TASK = "task"
    ASSIGNMENT = "assignment"
    RESOURCE = "resource"
    ROUTE_OBSERVATION = "route_observation"
    CONFLICT_CASE = "conflict_case"
    VERIFICATION = "verification"


class ChangeDetail(BaseModel):
    base: Optional[Any] = None
    new: Any


class OperationalEventEnvelope(BaseModel):
    event_id: str = Field(..., description="Unique client-generated ULID / UUID")
    tenant_id: UUID = Field(..., description="Tenant isolation boundary")
    entity_type: EntityType
    entity_id: str
    event_type: str
    changes: Dict[str, ChangeDetail]
    actor_id: UUID
    device_id: str
    device_sequence: int = Field(..., ge=1)
    occurred_at: datetime
    version_vector: Dict[str, int] = Field(default_factory=dict)
    evidence_ids: List[UUID] = Field(default_factory=list)
    schema_version: int = 1
    integrity_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")


class SyncPushRequest(BaseModel):
    device_id: str
    events: List[OperationalEventEnvelope]


class SyncPushResponse(BaseModel):
    status: str = "success"
    processed_count: int
    accepted_event_ids: List[str]
    rejected_event_ids: List[str] = Field(default_factory=list)
    conflicts_detected: int = 0
    server_cursor: str


class SyncPullResponse(BaseModel):
    events: List[OperationalEventEnvelope]
    next_cursor: str
    has_more: bool
