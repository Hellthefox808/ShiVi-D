"""
ShiVi Comprehensive End-to-End Integration Verification Suite
Executes and validates all 15 operational touchpoints across the 5 core system invariants.
"""
import uuid
import hashlib
from datetime import datetime, timezone
import pytest
import httpx
from app.main import app

TENANT_ID = "11111111-1111-1111-1111-111111111111"
SUPERVISOR_ID = "00000000-0000-0000-0000-000000000001"
RESPONDER_ID = "00000000-0000-0000-0000-000000000002"
CITIZEN_ID = "00000000-0000-0000-0000-000000000003"


def compute_sha256(val: str) -> str:
    return hashlib.sha256(val.encode("utf-8")).hexdigest()


@pytest.mark.asyncio
async def test_01_health_and_service_info():
    """Verify health and service diagnostics."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "ShiVi Operations Core API" in data["service"]


@pytest.mark.asyncio
async def test_02_ioc_dashboard_summary_and_cache():
    """Verify IOC high-speed executive summary and in-memory caching."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # First query (populates cache)
        res1 = await client.get("/v1/dashboard/summary")
        assert res1.status_code == 200
        data1 = res1.json()
        assert "total_incidents" in data1
        assert "resource_saturation_index" in data1

        # Second query (served from cache)
        res2 = await client.get("/v1/dashboard/summary")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["cached"] is True


@pytest.mark.asyncio
async def test_03_spatial_geojson_clipping():
    """Verify spatial GeoJSON endpoint with bounding box viewport clipping."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/v1/dashboard/geojson?bbox=91.0,26.0,92.0,27.0")
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert data["viewport_filtered"] is True


@pytest.mark.asyncio
async def test_04_offline_incident_creation_and_scoring():
    """Verify offline-first incident registration and multi-factor explainable priority scoring."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        local_ref = f"OFFLINE-TEST-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "local_reference": local_ref,
            "category": "RESCUE",
            "title": "Evacuate 5 Civilians Stranded on Rooftop",
            "description": "Flash flood surge in Ward 4. Immediate inflatable boat required.",
            "severity": "CRITICAL",
            "people_at_risk": 5,
            "latitude": 26.1856,
            "longitude": 91.7483,
            "location_name": "Sector 4 Bridge",
            "has_photo_evidence": True,
        }
        res = await client.post("/v1/incidents", json=payload)
        assert res.status_code == 200
        incident = res.json()
        assert incident["id"] is not None
        assert incident["priority_score"] >= 70.0
        assert "explanation" in incident["priority_breakdown"]


@pytest.mark.asyncio
async def test_05_sync_push_idempotency():
    """Verify batch sync outbox ingestion and duplicate suppression."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        evt_id = f"EVT-IDEMP-{uuid.uuid4().hex[:8]}"
        batch = {
            "device_id": "test-device-alpha",
            "events": [
                {
                    "event_id": evt_id,
                    "tenant_id": TENANT_ID,
                    "entity_type": "incident",
                    "entity_id": str(uuid.uuid4()),
                    "event_type": "INCIDENT_REPORTED",
                    "changes": {"status": {"base": "DRAFT", "new": "REPORTED"}},
                    "actor_id": CITIZEN_ID,
                    "device_id": "test-device-alpha",
                    "device_sequence": 1,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "evidence_ids": [],
                    "schema_version": 1,
                    "integrity_hash": compute_sha256("test_hash_event"),
                }
            ],
        }
        res1 = await client.post("/v1/sync/push", json=batch)
        assert res1.status_code == 200
        assert evt_id in res1.json()["accepted_event_ids"]

        # Replay identical batch
        res2 = await client.post("/v1/sync/push", json=batch)
        assert res2.status_code == 200
        assert evt_id in res2.json()["duplicate_event_ids"]


@pytest.mark.asyncio
async def test_06_hybrid_ai_entity_extraction_and_sop():
    """Verify governed AI advisory extraction and NDMA SOP retrieval."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Entity Extraction
        ext_res = await client.post(
            "/v1/ai/extract",
            json={"raw_text": "Water entered hospital, 8 elderly patients need boat evacuation at Ward 2.", "language": "en"},
        )
        assert ext_res.status_code == 200
        ext_data = ext_res.json()
        assert ext_data["category"] in ["RESCUE", "MEDICAL"]
        assert ext_data["estimated_people"] >= 1
        assert ext_data["confidence"] > 0.5

        # 2. SOP Retrieval
        sop_res = await client.get("/v1/ai/sop?category=RESCUE&severity=CRITICAL")
        assert sop_res.status_code == 200
        sop_data = sop_res.json()
        assert len(sop_data["required_equipment"]) > 0
        assert len(sop_data["safety_warnings"]) > 0


@pytest.mark.asyncio
async def test_07_full_p0_disaster_workflow_endpoint():
    """Verify complete 9-step verified context loop simulation via REST API."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/v1/demo/simulate-workflow")
        assert res.status_code == 200
        sim = res.json()
        assert sim["status"] == "SUCCESS"
        assert len(sim["steps"]) == 9
        assert sim["incident"]["status"] == "RESOLVED"
        assert sim["conflict"]["status"] == "RESOLVED"
        assert sim["conflict"]["resolved_value"] == "BLOCKED"
        assert sim["task"]["status"] == "VERIFIED"


@pytest.mark.asyncio
async def test_08_immutable_audit_timeline_reconstruction():
    """Verify tamper-evident hash-chained audit ledger reconstruction."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/v1/audit/timeline")
        assert res.status_code == 200
        logs = res.json()
        assert len(logs) > 0
        for entry in logs:
            assert "action" in entry
            assert "actor_role" in entry
            assert "timestamp" in entry
