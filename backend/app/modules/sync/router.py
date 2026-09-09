import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.audit.models import OperationalEvent, AuditEntry
from app.modules.incidents.models import Incident, RouteObservation
from app.modules.tasks.models import Task
from app.modules.conflicts.models import ConflictCase

router = APIRouter(prefix="/sync", tags=["Offline Sync & Causal Engine"])


class EventChange(BaseModel):
    base: Optional[Any] = None
    new: Any


class EventEnvelopeIn(BaseModel):
    event_id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    event_type: str
    changes: Dict[str, EventChange]
    actor_id: str
    device_id: str
    device_sequence: int
    occurred_at: datetime
    version_vector: Dict[str, int] = {}
    evidence_ids: List[str] = []
    relay_hops: int = 0
    relayed_by_devices: List[str] = []
    initial_bearer: Optional[str] = "DIRECT"
    schema_version: int = 1
    integrity_hash: str


class SyncPushBatch(BaseModel):
    device_id: str
    events: List[EventEnvelopeIn]


class SyncPushResult(BaseModel):
    status: str = "success"
    processed_count: int
    accepted_event_ids: List[str]
    duplicate_event_ids: List[str]
    conflicts_detected: int
    server_cursor: str


class SyncPullResult(BaseModel):
    events: List[Dict[str, Any]]
    next_cursor: str
    has_more: bool


@router.post("/push", response_model=SyncPushResult)
async def push_sync_events(
    batch: SyncPushBatch,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    accepted_ids = []
    duplicate_ids = []
    conflicts_count = 0

    for ev in batch.events:
        # 1. Idempotency Check
        existing_res = await db.execute(
            select(OperationalEvent).where(
                OperationalEvent.event_id == ev.event_id,
                OperationalEvent.tenant_id == current_user.tenant_id,
            )
        )
        if existing_res.scalars().first():
            duplicate_ids.append(ev.event_id)
            continue

        # 2. Append Immutable Operational Event
        op_event = OperationalEvent(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            event_id=ev.event_id,
            entity_type=ev.entity_type,
            entity_id=ev.entity_id,
            event_type=ev.event_type,
            changes={k: {"base": v.base, "new": v.new} for k, v in ev.changes.items()},
            actor_id=ev.actor_id,
            device_id=ev.device_id,
            device_sequence=ev.device_sequence,
            occurred_at=ev.occurred_at,
            received_at=datetime.now(timezone.utc),
            version_vector=ev.version_vector,
            evidence_ids=ev.evidence_ids,
            integrity_hash=ev.integrity_hash,
        )
        db.add(op_event)
        accepted_ids.append(ev.event_id)

        # 3. Domain Event Application & Conflict Engine
        if ev.entity_type == "route_observation":
            route_id = ev.entity_id
            r_res = await db.execute(
                select(RouteObservation).where(
                    RouteObservation.route_identifier == route_id,
                    RouteObservation.tenant_id == current_user.tenant_id,
                )
            )
            route = r_res.scalars().first()
            if not route:
                route = RouteObservation(
                    id=str(uuid.uuid4()),
                    tenant_id=current_user.tenant_id,
                    route_identifier=route_id,
                    status="UNKNOWN",
                    notes=[],
                    photos=[],
                )
                db.add(route)

            # Auto-Merge Safe Additive Metadata
            if "notes" in ev.changes:
                new_note = ev.changes["notes"].new
                current_notes = list(route.notes or [])
                if isinstance(new_note, list):
                    current_notes.extend(new_note)
                elif new_note and new_note not in current_notes:
                    current_notes.append(new_note)
                route.notes = current_notes

            if "photos" in ev.changes or ev.evidence_ids:
                current_photos = list(route.photos or [])
                for pid in ev.evidence_ids:
                    if pid not in current_photos:
                        current_photos.append(pid)
                route.photos = current_photos

            # Protected Status Contradiction Handling
            if "status" in ev.changes:
                new_status = str(ev.changes["status"].new).upper()
                old_status = str(route.status).upper()

                if old_status not in ["UNKNOWN", "UNCERTAIN"] and old_status != new_status:
                    # Concurrency contradiction detected! (e.g. USABLE vs BLOCKED)
                    conflicts_count += 1
                    
                    # Create Conflict Case
                    conflict_case = ConflictCase(
                        id=str(uuid.uuid4()),
                        tenant_id=current_user.tenant_id,
                        entity_type="route_observation",
                        entity_id=route_id,
                        conflicting_field="status",
                        status="OPEN",
                        claims=[
                            {
                                "actor_id": route.last_reported_by or "prior_responder",
                                "device_id": "prior_device",
                                "value": old_status,
                                "occurred_at": route.last_reported_at.isoformat() if route.last_reported_at else datetime.utcnow().isoformat(),
                            },
                            {
                                "actor_id": ev.actor_id,
                                "device_id": ev.device_id,
                                "value": new_status,
                                "occurred_at": ev.occurred_at.isoformat(),
                                "evidence_ids": ev.evidence_ids,
                            },
                        ],
                        frozen_dependencies=[],
                    )
                    
                    # Set Route to UNCERTAIN and Freeze
                    route.status = "UNCERTAIN"
                    route.is_frozen = "TRUE"
                    route.active_conflict_id = conflict_case.id

                    # Freeze dependent tasks
                    t_res = await db.execute(
                        select(Task).where(
                            Task.route_id == route_id,
                            Task.tenant_id == current_user.tenant_id,
                        )
                    )
                    frozen_task_ids = []
                    for t in t_res.scalars().all():
                        t.is_route_blocked = "TRUE"
                        frozen_task_ids.append(t.id)
                    conflict_case.frozen_dependencies = frozen_task_ids
                    
                    db.add(conflict_case)

                    # Protected audit log
                    audit = AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_id=current_user.tenant_id,
                        action="CONFLICT_DETECTED_FREEZE",
                        actor_id="system_conflict_engine",
                        actor_role="SYSTEM",
                        target_entity_type="route_observation",
                        target_entity_id=route_id,
                        previous_state={"status": old_status},
                        new_state={"status": "UNCERTAIN", "conflict_id": conflict_case.id},
                        reason=f"Life-safety contradiction: {old_status} vs {new_status}. Automation frozen.",
                    )
                    db.add(audit)
                else:
                    route.status = new_status
                    route.last_reported_by = ev.actor_id
                    route.last_reported_at = ev.occurred_at

            await db.flush()

    await db.commit()

    # Invalidate dashboard cache for current tenant on sync mutations
    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return SyncPushResult(
        status="success",
        processed_count=len(batch.events),
        accepted_event_ids=accepted_ids,
        duplicate_event_ids=duplicate_ids,
        conflicts_detected=conflicts_count,
        server_cursor=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/pull", response_model=SyncPullResult)
async def pull_sync_events(
    cursor: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    query = select(OperationalEvent).where(
        OperationalEvent.tenant_id == current_user.tenant_id
    )
    if cursor:
        try:
            dt = datetime.fromisoformat(cursor)
            query = query.where(OperationalEvent.received_at > dt)
        except Exception:
            pass

    query = query.order_by(OperationalEvent.received_at.asc()).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    formatted = [
        {
            "event_id": e.event_id,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "event_type": e.event_type,
            "changes": e.changes,
            "actor_id": e.actor_id,
            "device_id": e.device_id,
            "occurred_at": e.occurred_at.isoformat(),
            "received_at": e.received_at.isoformat(),
            "evidence_ids": e.evidence_ids,
            "integrity_hash": e.integrity_hash,
        }
        for e in events
    ]

    next_cur = events[-1].received_at.isoformat() if events else (cursor or datetime.now(timezone.utc).isoformat())

    return SyncPullResult(
        events=formatted,
        next_cursor=next_cur,
        has_more=len(events) == limit,
    )


# ---------------------------------------------------------------------------
# Omni-Bearer Mesh Protocol: BLE 5.0 GATT MTU Packet Framing & Reassembly
# (Spec: docs/30_MULTI_BEARER_BLUETOOTH_WIFI_CELLULAR_MESH_SPEC.md)
# ---------------------------------------------------------------------------
import zlib
import base64
import json


class MeshFrame(BaseModel):
    packet_id: str
    chunk_index: int
    total_chunks: int
    chunk_payload_base64: str
    chunk_payload_text: str
    chunk_bytes: int
    crc32: str
    hop_count: int = 1


class MeshPacketizeRequest(BaseModel):
    payload: Any
    max_mtu_bytes: int = 496  # BLE 5.0 ATT MTU safe limit
    bearer: str = "BLE_5.0_GATT"
    source_device_id: str = "node-citizen-01"
    target_device_id: str = "hub-command-00"


class MeshPacketizeResponse(BaseModel):
    packet_id: str
    total_original_bytes: int
    total_frames: int
    max_frame_bytes: int
    bearer: str
    frames: List[MeshFrame]


class MeshReassembleRequest(BaseModel):
    frames: List[MeshFrame]


class MeshReassembleResponse(BaseModel):
    packet_id: str
    status: str
    received_frames: int
    total_frames: int
    reassembled_payload: str
    integrity_hash_sha256: str
    crc32_verified: bool


@router.post("/mesh/packetize", response_model=MeshPacketizeResponse)
async def packetize_mesh_payload(
    req: MeshPacketizeRequest,
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Slices an arbitrary JSON/text operational payload into ≤496-byte BLE GATT MTU frames
    with CRC32 integrity verification tags and chunk sequencing headers.
    Enforces Omni-Bearer Framing invariant for Zero-Connectivity BLE gossip relays.
    """
    if isinstance(req.payload, (dict, list)):
        raw_bytes = json.dumps(req.payload, separators=(",", ":")).encode("utf-8")
    else:
        raw_bytes = str(req.payload).encode("utf-8")

    packet_id = f"pkt-{uuid.uuid4().hex[:12]}"
    max_chunk_size = max(64, min(req.max_mtu_bytes, 496))

    chunks = [raw_bytes[i : i + max_chunk_size] for i in range(0, len(raw_bytes), max_chunk_size)]
    if not chunks:
        chunks = [b""]

    total_chunks = len(chunks)
    frames = []

    for idx, chunk in enumerate(chunks):
        crc = f"{zlib.crc32(chunk) & 0xFFFFFFFF:08x}"
        chunk_b64 = base64.b64encode(chunk).decode("ascii")
        try:
            chunk_text = chunk.decode("utf-8", errors="replace")
        except Exception:
            chunk_text = "<binary>"

        frames.append(
            MeshFrame(
                packet_id=packet_id,
                chunk_index=idx,
                total_chunks=total_chunks,
                chunk_payload_base64=chunk_b64,
                chunk_payload_text=chunk_text,
                chunk_bytes=len(chunk),
                crc32=crc,
                hop_count=1,
            )
        )

    return MeshPacketizeResponse(
        packet_id=packet_id,
        total_original_bytes=len(raw_bytes),
        total_frames=total_chunks,
        max_frame_bytes=max_chunk_size,
        bearer=req.bearer,
        frames=frames,
    )


@router.post("/mesh/reassemble", response_model=MeshReassembleResponse)
async def reassemble_mesh_payload(
    req: MeshReassembleRequest,
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Reassembles unordered BLE GATT MTU frames into original payload,
    validating CRC32 integrity per frame and calculating overall SHA-256 payload digest.
    """
    import hashlib

    if not req.frames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reassemble empty frame list",
        )

    packet_id = req.frames[0].packet_id
    total_expected = req.frames[0].total_chunks

    # Group by chunk_index to handle possible duplicates and out-of-order arrival
    seen_indices = {}
    crc_all_valid = True

    for frame in req.frames:
        if frame.packet_id != packet_id:
            continue
        try:
            chunk_bytes = base64.b64decode(frame.chunk_payload_base64)
            computed_crc = f"{zlib.crc32(chunk_bytes) & 0xFFFFFFFF:08x}"
            if computed_crc.lower() != frame.crc32.lower():
                crc_all_valid = False
            seen_indices[frame.chunk_index] = chunk_bytes
        except Exception:
            crc_all_valid = False

    received_count = len(seen_indices)
    if received_count < total_expected or not crc_all_valid:
        status_str = "CORRUPTED" if not crc_all_valid else "INCOMPLETE"
        return MeshReassembleResponse(
            packet_id=packet_id,
            status=status_str,
            received_frames=received_count,
            total_frames=total_expected,
            reassembled_payload="",
            integrity_hash_sha256="",
            crc32_verified=crc_all_valid,
        )

    # Assemble in sequential order 0..total_expected-1
    assembled_bytes = bytearray()
    for i in range(total_expected):
        if i in seen_indices:
            assembled_bytes.extend(seen_indices[i])
        else:
            return MeshReassembleResponse(
                packet_id=packet_id,
                status="MISSING_CHUNKS",
                received_frames=received_count,
                total_frames=total_expected,
                reassembled_payload="",
                integrity_hash_sha256="",
                crc32_verified=False,
            )

    payload_str = assembled_bytes.decode("utf-8", errors="replace")
    sha256_hash = hashlib.sha256(assembled_bytes).hexdigest()

    return MeshReassembleResponse(
        packet_id=packet_id,
        status="REASSEMBLED_VERIFIED",
        received_frames=received_count,
        total_frames=total_expected,
        reassembled_payload=payload_str,
        integrity_hash_sha256=sha256_hash,
        crc32_verified=True,
    )

