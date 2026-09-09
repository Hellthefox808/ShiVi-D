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


def test_simulation_scenarios_catalog(client, supervisor_headers):
    """Verifies that GET /v1/demo/scenarios lists all 4 operational drills."""
    res = client.get("/v1/demo/scenarios", headers=supervisor_headers)
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 4
    scenario_ids = [s["id"] for s in scenarios]
    assert "scenario-flood-contradiction" in scenario_ids
    assert "scenario-asset-contention" in scenario_ids
    assert "scenario-replay-attack" in scenario_ids
    assert "scenario-sms-triage" in scenario_ids


def test_simulate_flood_contradiction(client, supervisor_headers):
    """Verifies Scenario 1: Flash Flood Surge & Route-88 Safety Freeze."""
    res = client.post(
        "/v1/demo/simulate-workflow?scenario_id=scenario-flood-contradiction",
        headers=supervisor_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["scenario_id"] == "scenario-flood-contradiction"
    assert len(data["steps"]) == 9
    assert data["incident"]["status"] == "RESOLVED"
    assert data["conflict"]["status"] == "RESOLVED"
    assert data["task"]["status"] == "VERIFIED"


def test_simulate_asset_contention(client, supervisor_headers):
    """Verifies Scenario 2: Distributed Asset Contention & NFC Lease Resolution."""
    res = client.post(
        "/v1/demo/simulate-workflow?scenario_id=scenario-asset-contention",
        headers=supervisor_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["scenario_id"] == "scenario-asset-contention"
    assert len(data["steps"]) == 9
    assert "Invariant 4" in data["summary"]
    # Verify dynamic substitution
    assert any("Substitution" in s["title"] for s in data["steps"])
    assert any("Physical Possession" in s["title"] for s in data["steps"])


def test_simulate_replay_attack(client, supervisor_headers):
    """Verifies Scenario 3: Adversarial Poison Packet & Anti-Replay Mitigation."""
    res = client.post(
        "/v1/demo/simulate-workflow?scenario_id=scenario-replay-attack",
        headers=supervisor_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["scenario_id"] == "scenario-replay-attack"
    assert len(data["steps"]) == 9
    assert "Poison Packet Dropped" in [s["title"] for s in data["steps"]][4]


def test_simulate_sms_triage(client, supervisor_headers):
    """Verifies Scenario 4: Multilingual Low-Bandwidth SMS Emergency Triage."""
    res = client.post(
        "/v1/demo/simulate-workflow?scenario_id=scenario-sms-triage",
        headers=supervisor_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["scenario_id"] == "scenario-sms-triage"
    assert len(data["steps"]) == 9
    assert data["incident"]["people_at_risk"] == 4
    assert any("NDMA SOP-03" in s["title"] for s in data["steps"])
