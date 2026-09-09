import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def supervisor_headers():
    token = create_access_token(
        subject="00000000-0000-0000-0000-000000000001",
        role="SUPERVISOR",
        tenant_id="11111111-1111-1111-1111-111111111111",
    )
    return {"Authorization": f"Bearer {token}"}


def test_context_loop_endpoint_success(client, supervisor_headers):
    """
    Validates that /v1/dashboard/context-loop returns the full 14-Phase Continuous
    Verified Context Loop with closed-loop verification and all invariant guarantees.
    """
    res = client.get("/v1/dashboard/context-loop", headers=supervisor_headers)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    
    data = res.json()
    assert data["loop_status"] == "CONTINUOUS_VERIFIED"
    assert data["total_phases"] == 14
    assert data["loop_closure_verified"] is True
    assert "active_cycle_id" in data
    assert data["feedback_latency_ms"] > 0
    
    phases = data["phases"]
    assert len(phases) == 14
    
    expected_codes = [
        "SENSE", "INGEST", "NORMALIZE", "VALIDATE",
        "UNDERSTAND", "ENRICH", "PRIORITIZE", "PLAN",
        "AUTHORIZE", "ACT", "VERIFY", "SYNC",
        "RECONCILE", "AUDIT"
    ]
    
    for i, expected_code in enumerate(expected_codes, start=1):
        phase = phases[i - 1]
        assert phase["phase_number"] == i
        assert phase["code"] == expected_code
        assert phase["status"] in ["ACTIVE", "SYNCHRONIZED", "PROTECTED", "MONITORED"]
        assert phase["latency_ms"] > 0
        assert phase["throughput_events_sec"] > 0
        assert len(phase["invariant"]) > 0
