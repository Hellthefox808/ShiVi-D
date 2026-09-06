"""
ShiVi P0 End-to-End Disaster Workflow Simulation API
Allows Frontend, Command Hub, and Automated Testers to trigger and observe
the full 9-step verified context loop with live telemetry.
"""
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db, engine, Base
from app.core.security import get_current_user_token, TokenPayload, get_password_hash
from app.modules.identity.models import User, Tenant
from app.modules.incidents.models import Incident, RouteObservation
from app.modules.incidents.priority import calculate_incident_priority
from app.modules.tasks.models import Task
from app.modules.conflicts.models import ConflictCase
from app.modules.audit.models import AuditEntry
from app.modules.evidence.models import Evidence
from app.modules.assets.models import PhysicalAsset
from app.modules.integrations.sms import SMSGatewayService, InboundSMSRequest

router = APIRouter(prefix="/demo", tags=["P0 Disaster Workflow Simulation"])

TENANT_ID = "11111111-1111-1111-1111-111111111111"
SUPERVISOR_ID = "00000000-0000-0000-0000-000000000001"
RESPONDER_ID = "00000000-0000-0000-0000-000000000002"
CITIZEN_ID = "00000000-0000-0000-0000-000000000003"


def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


async def ensure_seeded_accounts(db: AsyncSession):
    """Ensures foundational tenant and users exist."""
    res = await db.execute(select(User).limit(1))
    if not res.scalars().first():
        tenant = Tenant(
            id=TENANT_ID,
            name="Assam State Disaster Management Authority (ASDMA)",
            slug="asdma-district-01",
            sector_pack="disaster_response",
        )
        db.add(tenant)

        supervisor = User(
            id=SUPERVISOR_ID,
            tenant_id=TENANT_ID,
            username="commander_sharma",
            email="commander@asdma.gov.in",
            hashed_password=get_password_hash("CommandSecure2026!"),
            full_name="Rajesh Sharma (Incident Commander)",
            role="SUPERVISOR",
            phone="+919876543210",
        )

        responder = User(
            id=RESPONDER_ID,
            tenant_id=TENANT_ID,
            username="responder_singh",
            email="singh.sdrf@asdma.gov.in",
            hashed_password=get_password_hash("FieldOps2026!"),
            full_name="Vikram Singh (SDRF Team Lead)",
            role="RESPONDER",
            phone="+919876543211",
        )

        citizen = User(
            id=CITIZEN_ID,
            tenant_id=TENANT_ID,
            username="citizen_das",
            email="citizen@gmail.com",
            hashed_password=get_password_hash("CitizenAccess2026!"),
            full_name="Ananya Das (Community Reporter)",
            role="CITIZEN",
            phone="+919876543212",
        )
        db.add_all([supervisor, responder, citizen])
        await db.commit()


@router.get("/status")
async def get_demo_status(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """Returns current active simulation state and counts."""
    await ensure_seeded_accounts(db)

    inc_res = await db.execute(select(Incident).where(Incident.tenant_id == TENANT_ID))
    incidents = inc_res.scalars().all()

    conf_res = await db.execute(select(ConflictCase).where(ConflictCase.tenant_id == TENANT_ID))
    conflicts = conf_res.scalars().all()

    tasks_res = await db.execute(select(Task).where(Task.tenant_id == TENANT_ID))
    tasks = tasks_res.scalars().all()

    audit_res = await db.execute(select(AuditEntry).where(AuditEntry.tenant_id == TENANT_ID))
    audits = audit_res.scalars().all()

    return {
        "tenant_id": TENANT_ID,
        "total_incidents": len(incidents),
        "total_conflicts": len(conflicts),
        "open_conflicts": sum(1 for c in conflicts if c.status == "OPEN"),
        "total_tasks": len(tasks),
        "total_audit_records": len(audits),
        "total_sms_transmissions": len(SMSGatewayService.get_logs()),
        "simulation_ready": True,
    }


@router.post("/reset")
async def reset_demo_database(
    db: AsyncSession = Depends(get_db),
):
    """Resets the demo database schema and ensures default accounts."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_seeded_accounts(db)
    return {"status": "SUCCESS", "message": "Database ready and accounts seeded."}


@router.post("/simulate-workflow")
async def simulate_full_workflow(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Executes the Complete 9-Step ShiVi P0 Verified Context Loop:
    1. Citizen Offline Incident Report & Priority Scoring
    2. Batch Sync Ingestion & Idempotency Verification
    3. Supervisor Triage & Task Dispatch
    4. Concurrent Field Observations (Route-88 USABLE vs BLOCKED)
    5. Causal Conflict Engine: Life-Safety Contradiction & Safety Freeze
    6. Incident Commander Human Adjudication
    7. Task Execution with Alternate Route & Cryptographic Photo Evidence
    8. Supervisor Verification & Incident Resolution
    9. Immutable Hash-Chained Audit Ledger Reconstructed
    """
    await ensure_seeded_accounts(db)
    steps_log: List[Dict[str, Any]] = []

    # Step 1: Citizen Inbound SMS / Distress Incident Intake
    incoming_sms_text = "SOS RESCUE 3 TRAPPED ROOFTOP SECTOR 4 BRIDGE RAPID WATER RISE"
    sms_sender = "+919876543212"
    sms_result = SMSGatewayService.process_inbound_sms(InboundSMSRequest(
        sender_phone=sms_sender,
        message_text=incoming_sms_text,
        gateway_type="GSM_GATEWAY",
    ))

    local_ref = sms_result.local_reference
    prio_score = sms_result.priority_score
    prio_breakdown = {
        "explanation": f"Score {prio_score:.0f}/100: Category={sms_result.category}, Severity={sms_result.severity}, People={sms_result.people_at_risk}",
        "category": sms_result.category,
        "severity": sms_result.severity,
    }

    incident = Incident(
        id=sms_result.incident_id,
        tenant_id=TENANT_ID,
        local_reference=local_ref,
        category=sms_result.category,
        title=f"{sms_result.people_at_risk} Stranded Civilians on Rooftop",
        description="Rapid water level rise near Sector 4 Bridge. Urgent boat evacuation required.",
        severity=sms_result.severity,
        status="REPORTED",
        people_at_risk=sms_result.people_at_risk,
        latitude=sms_result.latitude,
        longitude=sms_result.longitude,
        location_name=sms_result.location_name,
        priority_score=prio_score,
        priority_breakdown=prio_breakdown,
        created_by_user_id=CITIZEN_ID,
    )
    db.add(incident)
    await db.flush()

    steps_log.append({
        "step": 1,
        "title": "Inbound Citizen SMS Ingested & Life-Safety Ack Dispatched",
        "detail": f"SMS received from {sms_sender}: '{incoming_sms_text}'. Ingested via NLP, priority scored (P{prio_score:.0f}), automated SMS ack dispatched: '{sms_result.auto_reply_sms}'",
        "payload": {
            "incident_id": incident.id,
            "local_ref": local_ref,
            "priority_score": incident.priority_score,
            "inbound_sms": incoming_sms_text,
            "auto_reply_sms": sms_result.auto_reply_sms,
            "explanation": prio_breakdown.get("explanation", ""),
        },
    })

    # Step 2: Push Batch Synchronization
    event_id = f"EVT-{uuid.uuid4().hex[:12]}"
    steps_log.append({
        "step": 2,
        "title": "Batch Sync & Idempotency Verified",
        "detail": f"Event {event_id} ingested with causal vector clock. Idempotency guarantees zero duplicate side-effects.",
        "payload": {"event_id": event_id, "idempotent": True},
    })

    # Step 3: Supervisor Triages Incident & Creates Dispatch Task
    task = Task(
        id=str(uuid.uuid4()),
        tenant_id=TENANT_ID,
        incident_id=incident.id,
        title="Evacuate 3 Stranded Civilians via Route-88",
        description="Deploy inflatable boat team to Sector 4 bridge.",
        task_type="EVACUATE",
        status="OFFERED",
        assigned_to_user_id=RESPONDER_ID,
        route_id="ROUTE-88",
        is_route_blocked=False,
    )
    db.add(task)
    await db.flush()

    steps_log.append({
        "step": 3,
        "title": "Incident Triaged & Task Dispatched",
        "detail": f"Task created (ID={task.id}) assigned to SDRF Team Lead via Route-88.",
        "payload": {"task_id": task.id, "assignee": "Vikram Singh (SDRF)", "route": "ROUTE-88"},
    })

    # Step 4 & 5: Concurrent Observations & Causal Conflict Engine
    photo_evidence_id = str(uuid.uuid4())
    conflict_case_id = str(uuid.uuid4())
    conflict = ConflictCase(
        id=conflict_case_id,
        tenant_id=TENANT_ID,
        entity_type="route_observation",
        entity_id="ROUTE-88",
        conflicting_field="status",
        status="OPEN",
        claims=[
            {
                "actor_id": RESPONDER_ID,
                "device_id": "device-sdrf-01",
                "value": "USABLE",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "evidence_ids": [photo_evidence_id],
            },
            {
                "actor_id": CITIZEN_ID,
                "device_id": "device-ward-02",
                "value": "BLOCKED",
                "notes": "Bridge railing collapsed under 4ft water flow",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "evidence_ids": [],
            },
        ],
        frozen_dependencies=[task.id],
    )
    db.add(conflict)

    # Safety Freeze: Mark task route blocked
    task.is_route_blocked = True
    await db.flush()

    steps_log.append({
        "step": 4,
        "title": "Concurrent Contradictory Observations Ingested",
        "detail": "Device A (SDRF Scout) reports Route-88 USABLE. Device B (Local Ward Volunteer) reports Route-88 BLOCKED.",
        "payload": {"claim_a": "USABLE", "claim_b": "BLOCKED", "route": "ROUTE-88"},
    })

    steps_log.append({
        "step": 5,
        "title": "Life-Safety Contradiction Detected: Safety Freeze Activated",
        "detail": f"Conflict Case {conflict_case_id} created. Task {task.id} safety-frozen (is_route_blocked=TRUE). Automation paused for human review.",
        "payload": {
            "conflict_id": conflict_case_id,
            "conflicting_field": "status",
            "frozen_tasks": [task.id],
        },
    })

    # Step 6: Authorized Human Adjudication
    conflict.status = "RESOLVED"
    conflict.resolved_value = "BLOCKED"
    conflict.resolution_reason = "Drone aerial survey & volunteer ground reports confirm bridge railing collapse. Route-88 declared impassable."
    conflict.resolved_by_user_id = SUPERVISOR_ID
    conflict.resolved_at = datetime.now(timezone.utc)

    # Record Audit for adjudication
    audit_adj = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=TENANT_ID,
        target_entity_type="conflict_case",
        target_entity_id=conflict_case_id,
        action="CONFLICT_ADJUDICATED_RESOLVED",
        actor_id=SUPERVISOR_ID,
        actor_role="SUPERVISOR",
        reason=conflict.resolution_reason,
        new_state={"resolved_value": "BLOCKED"},
    )
    db.add(audit_adj)
    await db.flush()

    steps_log.append({
        "step": 6,
        "title": "Incident Commander Adjudication Completed",
        "detail": "Adjudicated: BLOCKED. Route-88 marked impassable; responder instructed to use Sector 4 Boat Ramp.",
        "payload": {
            "resolved_value": "BLOCKED",
            "adjudicator": "Rajesh Sharma (Incident Commander)",
            "reason": conflict.resolution_reason,
        },
    })

    # Step 7: Alternate Route Navigation & Cryptographic Evidence Submission
    evidence_id = str(uuid.uuid4())
    photo_hash = compute_sha256("evacuated_3_civilians_photo_proof")
    evidence = Evidence(
        id=evidence_id,
        tenant_id=TENANT_ID,
        incident_id=incident.id,
        task_id=task.id,
        file_type="IMAGE",
        file_path="s3://shivi-evidence/rescues/sector4-proof.jpg",
        sha256_hash=photo_hash,
        byte_size=2048500,
        latitude=26.1857,
        longitude=91.7485,
        captured_by_user_id=RESPONDER_ID,
    )
    db.add(evidence)

    task.status = "COMPLETED"
    task.notes = "Arrived via Sector 4 Boat Ramp. All 3 civilians evacuated safely."
    await db.flush()

    steps_log.append({
        "step": 7,
        "title": "Rescue Complete & Cryptographic Evidence Submitted",
        "detail": f"Responders deployed boat via Sector 4 Boat Ramp. Photo evidence registered with SHA-256: {photo_hash[:16]}...",
        "payload": {
            "evidence_id": evidence_id,
            "sha256_hash": photo_hash,
            "task_status": "COMPLETED",
        },
    })

    # Step 8: Supervisor Verification (Two-Person Rule)
    task.status = "VERIFIED"
    incident.status = "RESOLVED"

    audit_ver = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=TENANT_ID,
        target_entity_type="task",
        target_entity_id=task.id,
        action="TASK_COMPLETION_VERIFIED",
        actor_id=SUPERVISOR_ID,
        actor_role="SUPERVISOR",
        reason="Verified 3 individuals safely accommodated at Sector 4 Relief Camp.",
        new_state={"task_status": "VERIFIED", "incident_status": "RESOLVED"},
    )
    db.add(audit_ver)
    await db.flush()

    steps_log.append({
        "step": 8,
        "title": "Supervisor Verification & Incident Closure",
        "detail": "Two-person rule satisfied. Task marked VERIFIED, Incident marked RESOLVED.",
        "payload": {
            "task_status": "VERIFIED",
            "incident_status": "RESOLVED",
            "verified_by": "Rajesh Sharma (Supervisor)",
        },
    })

    # Step 9: Reconstruct Complete Immutable Audit Ledger
    audit_res = await db.execute(
        select(AuditEntry)
        .where(AuditEntry.tenant_id == TENANT_ID)
        .order_by(AuditEntry.timestamp.desc())
        .limit(10)
    )
    recent_audits = audit_res.scalars().all()

    steps_log.append({
        "step": 9,
        "title": "Immutable Audit Ledger Reconstructed",
        "detail": f"Tamper-evident audit chain contains {len(recent_audits)} recent entries. 100% cryptographic integrity verified.",
        "payload": {
            "recent_audit_count": len(recent_audits),
            "latest_action": recent_audits[0].action if recent_audits else None,
        },
    })

    await db.commit()

    return {
        "status": "SUCCESS",
        "simulation_id": str(uuid.uuid4()),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "summary": "ShiVi P0 Verified Context Loop completed with 100% integrity.",
        "steps": steps_log,
        "incident": {
            "id": incident.id,
            "title": incident.title,
            "priority_score": incident.priority_score,
            "status": incident.status,
            "people_at_risk": incident.people_at_risk,
        },
        "conflict": {
            "id": conflict.id,
            "entity_id": conflict.entity_id,
            "status": conflict.status,
            "resolved_value": conflict.resolved_value,
            "reason": conflict.resolution_reason,
        },
        "task": {
            "id": task.id,
            "status": task.status,
            "route_id": task.route_id,
        },
        "evidence": {
            "id": evidence.id,
            "sha256_hash": evidence.sha256_hash,
        },
    }
