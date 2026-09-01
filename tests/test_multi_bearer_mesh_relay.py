"""
Tests for Multi-Bearer Mesh Relay & Peer Synchronization
Verifies peer relay provenance (Bluetooth Mesh, Wi-Fi Direct) and loop prevention.
"""
import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine
from app.core.security import create_access_token
from app.core.resilience import LoopGuard, LoopDetectedException


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_bluetooth_mesh_relayed_event_ingestion():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tenant_id = str(uuid.uuid4())
        origin_user = str(uuid.uuid4())
        carrier_user = str(uuid.uuid4())

        carrier_token = create_access_token({"sub": carrier_user, "role": "RESPONDER", "tenant_id": tenant_id})
        headers = {"Authorization": f"Bearer {carrier_token}"}

        # Event was generated offline by origin_node, carried via BLE mesh to carrier_node
        event_id = f"EVT-BLE-{uuid.uuid4().hex[:6]}"
        incident_id = str(uuid.uuid4())

        mesh_batch = {
            "device_id": "carrier-device-sdrf-09",
            "events": [
                {
                    "event_id": event_id,
                    "tenant_id": tenant_id,
                    "entity_type": "incident",
                    "entity_id": incident_id,
                    "event_type": "INCIDENT_REPORTED",
                    "changes": {
                        "category": {"base": None, "new": "MEDICAL"},
                        "severity": {"base": None, "new": "CRITICAL"},
                        "title": {"base": None, "new": "Elderly patient insulin shortage"},
                    },
                    "actor_id": origin_user,
                    "device_id": "isolated-scout-phone-01",
                    "device_sequence": 1,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "relay_hops": 2,
                    "relayed_by_devices": ["scout-phone-01", "carrier-device-sdrf-09"],
                    "initial_bearer": "BLUETOOTH_MESH",
                    "integrity_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                }
            ],
        }

        res = await client.post("/v1/sync/push", json=mesh_batch, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert event_id in data["accepted_event_ids"]


def test_mesh_relay_loop_prevention():
    """LoopGuard catches cyclic transmissions across mesh nodes."""
    # Safe 1-hop transmission
    assert LoopGuard.check_event_loop(
        event_id="EVT-01",
        origin_device_id="node-A",
        target_device_id="node-B",
        hop_count=1,
        traversed_nodes=["node-A"],
    ) is True

    # Causal cycle: Looping back to origin
    with pytest.raises(LoopDetectedException) as exc_info:
        LoopGuard.check_event_loop(
            event_id="EVT-01",
            origin_device_id="node-A",
            target_device_id="node-A",
            hop_count=2,
            traversed_nodes=["node-A", "node-B"],
        )
    assert "looped back to origin node" in str(exc_info.value)

    # Exceeding max allowable hops (5)
    with pytest.raises(LoopDetectedException) as exc_info_hops:
        LoopGuard.check_event_loop(
            event_id="EVT-01",
            origin_device_id="node-A",
            target_device_id="node-F",
            hop_count=6,
            traversed_nodes=["node-A", "node-B", "node-C", "node-D", "node-E"],
        )
    assert "exceeded maximum allowed causal sync hops" in str(exc_info_hops.value)
