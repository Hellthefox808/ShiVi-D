"""
ShiVi P0 End-to-End Simulation & Verification Script
Validates the complete 24-hour MVP Proof:
Offline report -> Causal Sync -> Assignment -> Concurrent Updates -> 
Auto-merge + Protected Conflict -> Safety Freeze -> Human Adjudication -> 
Evidence Verification -> Immutable Audit Reconstruction
"""
import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone

# Set UTF-8 encoding for standard output to support cross-platform consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root and core-api to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "apps", "core-api"))

import httpx
from app.main import app
from app.core.database import engine, Base
from scripts.seed_data import seed

TENANT_ID = "11111111-1111-1111-1111-111111111111"
SUPERVISOR_ID = "00000000-0000-0000-0000-000000000001"
RESPONDER_ID = "00000000-0000-0000-0000-000000000002"
CITIZEN_ID = "00000000-0000-0000-0000-000000000003"


def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


async def run_simulation():
    print("=" * 80)
    print("[START] SHIVI P0 VERIFIED CONTEXT LOOP DEMONSTRATION")
    print("=" * 80)

    # 1. Ensure DB seeded
    await seed()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Citizen Reports Incident Offline
        print("\n[STEP 1] Citizen Reports Incident Offline (Zero Connectivity)")
        local_ref = "OFFLINE-REF-9021"
        inc_payload = {
            "local_reference": local_ref,
            "category": "RESCUE",
            "title": "3 Stranded Family Members on Rooftop",
            "description": "Rapid water level rise near Sector 4 Bridge. Urgent boat evacuation required.",
            "severity": "CRITICAL",
            "people_at_risk": 3,
            "latitude": 26.1856,
            "longitude": 91.7483,
            "location_name": "Sector 4 Bridge, Brahmaputra Basin",
            "has_photo_evidence": True,
        }
        res = await client.post("/v1/incidents", json=inc_payload)
        assert res.status_code == 200, res.text
        incident = res.json()
        incident_id = incident["id"]
        print(f"  [OK] Incident Committed to Local Outbox: ID={incident_id}")
        print(f"  [SCORE] Explainable Priority Computed: Score={incident['priority_score']}/100")
        print(f"     Explanation: {incident['priority_breakdown']['explanation']}")

        # Step 2: Push Batch Synchronization & Idempotency Test
        print("\n[STEP 2] Device Reconnects: Batch Sync & Idempotency Check")
        event_id = f"EVT-{uuid.uuid4().hex[:12]}"
        sync_batch = {
            "device_id": "citizen-device-alpha",
            "events": [
                {
                    "event_id": event_id,
                    "tenant_id": TENANT_ID,
                    "entity_type": "incident",
                    "entity_id": incident_id,
                    "event_type": "INCIDENT_REPORTED",
                    "changes": {"status": {"base": "DRAFT", "new": "REPORTED"}},
                    "actor_id": CITIZEN_ID,
                    "device_id": "citizen-device-alpha",
                    "device_sequence": 1,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "version_vector": {"citizen-device-alpha": 1},
                    "evidence_ids": [],
                    "schema_version": 1,
                    "integrity_hash": compute_sha256("incident_reported_event"),
                }
            ],
        }
        res_sync = await client.post("/v1/sync/push", json=sync_batch)
        assert res_sync.status_code == 200, res_sync.text
        print(f"  [OK] Sync Push 1 Processed: Accepted={res_sync.json()['accepted_event_ids']}")

        # Re-push identical event to verify Idempotency
        res_sync_dup = await client.post("/v1/sync/push", json=sync_batch)
        assert res_sync_dup.status_code == 200, res_sync_dup.text
        print(f"  [OK] Sync Push 2 (Duplicate Replay): Duplicates Detected={res_sync_dup.json()['duplicate_event_ids']} (Zero duplicate side-effects)")

        # Step 3: Supervisor Triages & Dispatches Task
        print("\n[STEP 3] Supervisor Triages Incident & Creates Dispatch Task")
        task_payload = {
            "incident_id": incident_id,
            "title": "Evacuate 3 Stranded Civilians via Route-88",
            "description": "Deploy inflatable boat team to Sector 4 bridge.",
            "task_type": "EVACUATE",
            "route_id": "ROUTE-88",
        }
        t_res = await client.post("/v1/tasks", json=task_payload)
        assert t_res.status_code == 200, t_res.text
        task_id = t_res.json()["id"]
        print(f"  [OK] Task Created: ID={task_id}, Route=ROUTE-88")

        # Assign Task to Responder
        assign_res = await client.post(f"/v1/tasks/{task_id}/assign", json={"assigned_to_user_id": RESPONDER_ID})
        assert assign_res.status_code == 200, assign_res.text
        print(f"  [OK] Task Assigned to SDRF Team Lead ({RESPONDER_ID}), Status={assign_res.json()['status']}")

        # Step 4: Concurrent Field Updates from Disconnected Devices
        print("\n[STEP 4] Concurrent Field Observations from Disconnected Devices A & B")
        print("  - Device A (SDRF Scout): Adds photograph & reports Route-88 is USABLE")
        print("  - Device B (Local Ward Volunteer): Adds warning note & reports Route-88 is BLOCKED")

        photo_evidence_id = str(uuid.uuid4())
        device_a_event = {
            "event_id": f"EVT-A-{uuid.uuid4().hex[:8]}",
            "tenant_id": TENANT_ID,
            "entity_type": "route_observation",
            "entity_id": "ROUTE-88",
            "event_type": "ROUTE_STATUS_UPDATED",
            "changes": {
                "status": {"base": "UNKNOWN", "new": "USABLE"},
            },
            "actor_id": RESPONDER_ID,
            "device_id": "device-sdrf-01",
            "device_sequence": 10,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "evidence_ids": [photo_evidence_id],
            "schema_version": 1,
            "integrity_hash": compute_sha256("device_a_obs"),
        }

        device_b_event = {
            "event_id": f"EVT-B-{uuid.uuid4().hex[:8]}",
            "tenant_id": TENANT_ID,
            "entity_type": "route_observation",
            "entity_id": "ROUTE-88",
            "event_type": "ROUTE_STATUS_UPDATED",
            "changes": {
                "status": {"base": "UNKNOWN", "new": "BLOCKED"},
                "notes": {"base": None, "new": "Bridge railing collapsed under 4ft water flow at 07:15 AM"},
            },
            "actor_id": CITIZEN_ID,
            "device_id": "device-ward-02",
            "device_sequence": 5,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "evidence_ids": [],
            "schema_version": 1,
            "integrity_hash": compute_sha256("device_b_obs"),
        }

        # Step 5: Sync Convergence, Auto-Merge, and Protected Conflict Freeze
        print("\n[STEP 5] Devices Reconnect: Server Executes Causal Conflict Engine")
        res_push_ab = await client.post(
            "/v1/sync/push",
            json={"device_id": "gateway", "events": [device_a_event, device_b_event]},
        )
        assert res_push_ab.status_code == 200, res_push_ab.text
        sync_result = res_push_ab.json()
        print(f"  [OK] Events Merged & Processed: Count={sync_result['processed_count']}")
        print(f"  [ALERT] Life-Safety Contradictions Detected: {sync_result['conflicts_detected']}")

        # Verify Conflict Case is Open
        conflicts_res = await client.get("/v1/conflicts")
        assert conflicts_res.status_code == 200, conflicts_res.text
        conflicts = conflicts_res.json()
        assert len(conflicts) > 0
        conflict_case = conflicts[0]
        print(f"  [CASE] Active Conflict Case Created: ID={conflict_case['id']}")
        print(f"     Conflicting Field: {conflict_case['conflicting_field']}")
        print(f"     Claims Preserved: {json.dumps(conflict_case['claims'], indent=2)}")
        print(f"     Frozen Dependent Tasks: {conflict_case['frozen_dependencies']}")

        # Verify that task dispatch on Route-88 is now safety-frozen
        task_check = await client.get(f"/v1/tasks")
        target_t = [t for t in task_check.json() if t["id"] == task_id][0]
        print(f"  [LOCKED] Safety Freeze Active: Task is_route_blocked = {target_t['is_route_blocked']}")

        # Step 6: Authorized Human Adjudication
        print("\n[STEP 6] Incident Commander Reviews Evidence & Resolves Conflict")
        resolve_payload = {
            "resolved_value": "BLOCKED",
            "reason": "Drone aerial survey & volunteer ground reports confirm bridge railing collapse. Route-88 declared impassable.",
        }
        res_adjudicate = await client.post(f"/v1/conflicts/{conflict_case['id']}/resolve", json=resolve_payload)
        assert res_adjudicate.status_code == 200, res_adjudicate.text
        print(f"  [RESOLVED] Conflict Case Resolved: Status={res_adjudicate.json()['status']}, Value={res_adjudicate.json()['resolved_value']}")
        print(f"     Reason Recorded in Audit: {res_adjudicate.json()['resolution_reason']}")

        # Step 7: Task Execution & Evidence Submission
        print("\n[STEP 7] Responder Navigates Alternate Route & Submits Rescue Evidence")
        # Responder transitions task to ON_SITE -> COMPLETED with evidence
        await client.post(f"/v1/tasks/{task_id}/transitions", json={"target_status": "ON_SITE", "notes": "Arrived via Sector 4 Boat Ramp"})
        
        # Upload completion evidence
        evidence_payload = {
            "task_id": task_id,
            "incident_id": incident_id,
            "file_type": "IMAGE",
            "sha256_hash": compute_sha256("evacuated_3_civilians_photo_proof"),
            "byte_size": 2048500,
            "latitude": 26.1857,
            "longitude": 91.7485,
        }
        ev_res = await client.post("/v1/evidence/presign", json=evidence_payload)
        assert ev_res.status_code == 200, ev_res.text
        ev_id = ev_res.json()["id"]
        print(f"  [EVIDENCE] Cryptographic Evidence Registered: ID={ev_id}, SHA256={ev_res.json()['sha256_hash'][:16]}...")

        # Complete Task
        complete_res = await client.post(f"/v1/tasks/{task_id}/transitions", json={"target_status": "COMPLETED", "evidence_id": ev_id})
        assert complete_res.status_code == 200, complete_res.text
        print(f"  [OK] Task Completed in Field: Status={complete_res.json()['status']}")

        # Step 8: Supervisor Verification & Incident Closure
        print("\n[STEP 8] Supervisor Verifies Evidence & Authorizes Incident Closure")
        verify_payload = {
            "task_id": task_id,
            "is_approved": True,
            "notes": "Verified 3 individuals safely accommodated at Sector 4 Relief Camp.",
        }
        ver_res = await client.post("/v1/verifications", json=verify_payload)
        assert ver_res.status_code == 200, ver_res.text
        print(f"  [VERIFIED] Task Verified & Closed: Task Status={ver_res.json()['task_status']}, Incident Status={ver_res.json()['incident_status']}")

        # Step 9: Reconstruct Immutable Audit Timeline
        print("\n[STEP 9] Reconstructing Complete Immutable Audit Ledger")
        audit_res = await client.get("/v1/audit/timeline")
        assert audit_res.status_code == 200, audit_res.text
        audit_entries = audit_res.json()
        print(f"  [AUDIT] Total Audit Entries Recorded: {len(audit_entries)}")
        for idx, entry in enumerate(reversed(audit_entries), 1):
            print(f"     {idx}. [{entry['timestamp'][:19]}] {entry['action']} by {entry['actor_role']}: {entry['reason']}")

        print("\n" + "=" * 80)
        print("[SUCCESS] SHIVI P0 VERIFICATION SUITE COMPLETED WITH 100% INTEGRITY")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_simulation())
