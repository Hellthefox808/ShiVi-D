"""
Tests for ShiVi Domain Conflict Engine & Operational Safety Freeze
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine
from app.core.security import create_access_token


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_route_conflict_freezes_tasks_and_resolves():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tenant_id = str(uuid.uuid4())
        sup_id = str(uuid.uuid4())
        dev_a_user = str(uuid.uuid4())
        dev_b_user = str(uuid.uuid4())

        sup_token = create_access_token({"sub": sup_id, "role": "SUPERVISOR", "tenant_id": tenant_id})
        dev_a_token = create_access_token({"sub": dev_a_user, "role": "RESPONDER", "tenant_id": tenant_id})
        dev_b_token = create_access_token({"sub": dev_b_user, "role": "RESPONDER", "tenant_id": tenant_id})

        sup_headers = {"Authorization": f"Bearer {sup_token}"}
        dev_a_headers = {"Authorization": f"Bearer {dev_a_token}"}
        dev_b_headers = {"Authorization": f"Bearer {dev_b_token}"}

        route_id = f"ROUTE-TEST-{uuid.uuid4().hex[:4]}"

        # Step 1: Create an incident and dependent task on route_id
        inc_res = await client.post(
            "/v1/incidents",
            json={
                "local_reference": f"LOC-TEST-{uuid.uuid4().hex[:4]}",
                "category": "RESCUE",
                "title": "Evacuation Mission Test",
                "description": "Family needing boat rescue",
                "severity": "CRITICAL",
                "people_at_risk": 4,
                "latitude": 26.18,
                "longitude": 91.74,
            },
            headers=sup_headers,
        )
        assert inc_res.status_code == 200
        incident_id = inc_res.json()["id"]

        task_res = await client.post(
            "/v1/tasks",
            json={
                "incident_id": incident_id,
                "title": "Dispatch Boat Team",
                "description": "Travel via test route to location",
                "task_type": "EVACUATION",
                "route_id": route_id,
            },
            headers=sup_headers,
        )
        assert task_res.status_code == 200
        task_id = task_res.json()["id"]
        assert task_res.json()["is_route_blocked"] == "FALSE"

        # Step 2: Device A pushes ROUTE = USABLE
        evt_a = {
            "device_id": "device-A",
            "events": [
                {
                    "event_id": f"EVT-A-{uuid.uuid4().hex[:6]}",
                    "tenant_id": tenant_id,
                    "entity_type": "route_observation",
                    "entity_id": route_id,
                    "event_type": "ROUTE_STATUS_UPDATED",
                    "changes": {
                        "status": {"base": "UNKNOWN", "new": "USABLE"},
                        "notes": {"base": [], "new": ["Device A: Road clear at km 4"]},
                    },
                    "actor_id": dev_a_user,
                    "device_id": "device-A",
                    "device_sequence": 1,
                    "occurred_at": "2026-09-01T21:10:00Z",
                    "integrity_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                }
            ],
        }
        res_a = await client.post("/v1/sync/push", json=evt_a, headers=dev_a_headers)
        assert res_a.status_code == 200

        # Step 3: Device B concurrently pushes ROUTE = BLOCKED
        evt_b = {
            "device_id": "device-B",
            "events": [
                {
                    "event_id": f"EVT-B-{uuid.uuid4().hex[:6]}",
                    "tenant_id": tenant_id,
                    "entity_type": "route_observation",
                    "entity_id": route_id,
                    "event_type": "ROUTE_STATUS_UPDATED",
                    "changes": {
                        "status": {"base": "UNKNOWN", "new": "BLOCKED"},
                        "notes": {"base": [], "new": ["Device B: Bridge submerged 4ft water"]},
                    },
                    "actor_id": dev_b_user,
                    "device_id": "device-B",
                    "device_sequence": 1,
                    "occurred_at": "2026-09-01T21:12:00Z",
                    "integrity_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                }
            ],
        }
        res_b = await client.post("/v1/sync/push", json=evt_b, headers=dev_b_headers)
        assert res_b.status_code == 200
        assert res_b.json()["conflicts_detected"] == 1

        # Step 4: Verify task is FROZEN
        task_check = await client.get(f"/v1/tasks/{task_id}", headers=sup_headers)
        assert task_check.status_code == 200
        assert task_check.json()["is_route_blocked"] == "TRUE"

        # Step 5: Verify Conflict Case exists
        conflicts_list = await client.get("/v1/conflicts", headers=sup_headers)
        assert conflicts_list.status_code == 200
        matching = [c for c in conflicts_list.json() if c["entity_id"] == route_id and c["status"] == "OPEN"]
        assert len(matching) == 1
        conflict_id = matching[0]["id"]

        # Step 6: Supervisor Adjudicates with mandatory justification
        resolve_res = await client.post(
            f"/v1/conflicts/{conflict_id}/resolve",
            json={
                "resolved_value": "BLOCKED",
                "reason": "Drone imagery confirms bridge railing failure under 4ft water. Declared impassable.",
            },
            headers=sup_headers,
        )
        assert resolve_res.status_code == 200
        assert resolve_res.json()["status"] == "RESOLVED"
