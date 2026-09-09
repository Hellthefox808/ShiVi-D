import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        role="SUPERVISOR",
        tenant_id="11111111-1111-1111-1111-111111111111",
    )
    return {"Authorization": f"Bearer {token}"}


def test_mesh_packetize_small_payload(client, auth_headers):
    """Verifies that payloads under MTU produce exactly one BLE frame with valid CRC32."""
    payload = {"status": "USABLE", "route_id": "ROUTE-88", "notes": "Clear road"}
    res = client.post(
        "/v1/sync/mesh/packetize",
        json={"payload": payload, "max_mtu_bytes": 496, "bearer": "BLE_5.0_GATT"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_frames"] == 1
    assert len(data["frames"]) == 1
    assert data["frames"][0]["chunk_index"] == 0
    assert len(data["frames"][0]["crc32"]) == 8


def test_mesh_packetize_and_reassemble_large_payload(client, auth_headers):
    """Verifies that large payloads (>496 bytes) slice into multiple frames and reassemble perfectly."""
    # Create a 2KB operational payload
    large_payload = {
        "event_id": "EVT-TEST-LARGE-001",
        "description": "Severe flooding across Ward 4. " * 50,
        "coordinates": [{"lat": 26.185 + (i * 0.001), "lng": 91.748 + (i * 0.001)} for i in range(25)],
    }
    
    # 1. Packetize into 256-byte chunks to force multiple chunks
    res_pack = client.post(
        "/v1/sync/mesh/packetize",
        json={"payload": large_payload, "max_mtu_bytes": 256, "bearer": "BLE_5.0_GATT"},
        headers=auth_headers,
    )
    assert res_pack.status_code == 200
    pack_data = res_pack.json()
    assert pack_data["total_frames"] > 3
    frames = pack_data["frames"]

    # 2. Reassemble with out-of-order frames
    shuffled_frames = list(reversed(frames))
    res_reassemble = client.post(
        "/v1/sync/mesh/reassemble",
        json={"frames": shuffled_frames},
        headers=auth_headers,
    )
    assert res_reassemble.status_code == 200
    reassemble_data = res_reassemble.json()
    assert reassemble_data["status"] == "REASSEMBLED_VERIFIED"
    assert reassemble_data["crc32_verified"] is True
    assert len(reassemble_data["integrity_hash_sha256"]) == 64
    assert "Severe flooding across Ward 4." in reassemble_data["reassembled_payload"]


def test_mesh_reassemble_detects_corruption(client, auth_headers):
    """Verifies that tampering with a frame payload triggers corruption detection."""
    payload = {"test": "Tamper resistance verification"}
    res_pack = client.post(
        "/v1/sync/mesh/packetize",
        json={"payload": payload, "max_mtu_bytes": 496},
        headers=auth_headers,
    )
    frames = res_pack.json()["frames"]

    # Deliberately corrupt the CRC
    frames[0]["crc32"] = "deadbeef"
    res_reassemble = client.post(
        "/v1/sync/mesh/reassemble",
        json={"frames": frames},
        headers=auth_headers,
    )
    assert res_reassemble.status_code == 200
    data = res_reassemble.json()
    assert data["status"] == "CORRUPTED"
    assert data["crc32_verified"] is False
