"""
Tests for ShiVi Causal Sync & Idempotency Filter
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import create_access_token


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_sync_push_idempotency_replay():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Generate valid token
        tenant_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        token = create_access_token({"sub": user_id, "role": "RESPONDER", "tenant_id": tenant_id})
        headers = {"Authorization": f"Bearer {token}"}

        event_id = f"EVT-IDEMP-{uuid.uuid4().hex[:8]}"
        payload = {
            "device_id": "test-device-alpha",
            "events": [
                {
                    "event_id": event_id,
                    "tenant_id": tenant_id,
                    "entity_type": "incident",
                    "entity_id": f"INC-{uuid.uuid4().hex[:6]}",
                    "event_type": "INCIDENT_CREATED",
                    "changes": {"status": {"base": "DRAFT", "new": "REPORTED"}},
                    "actor_id": user_id,
                    "device_id": "test-device-alpha",
                    "device_sequence": 1,
                    "occurred_at": "2026-09-01T21:00:00Z",
                    "version_vector": {"test-device-alpha": 1},
                    "integrity_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                }
            ],
        }

        # 1. First push: Should be accepted
        res1 = await client.post("/v1/sync/push", json=payload, headers=headers)
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["processed_count"] == 1
        assert event_id in data1["accepted_event_ids"]
        assert len(data1["duplicate_event_ids"]) == 0

        # 2. Replay 5 times: Should return duplicate acknowledgment with 0 errors
        for _ in range(5):
            res_replay = await client.post("/v1/sync/push", json=payload, headers=headers)
            assert res_replay.status_code == 200
            data_replay = res_replay.json()
            assert data_replay["processed_count"] == 1
            assert event_id in data_replay["duplicate_event_ids"]
            assert len(data_replay["accepted_event_ids"]) == 0
