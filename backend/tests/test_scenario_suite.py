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


def test_list_simulation_scenarios(client):
    """Verifies that all 4 operational drills are cataloged."""
    res = client.get("/v1/demo/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 4
    scenario_ids = [s["id"] for s in scenarios]
    assert "scenario-flood-contradiction" in scenario_ids
    assert "scenario-asset-contention" in scenario_ids
    assert "scenario-replay-attack" in scenario_ids
    assert "scenario-sms-triage" in scenario_ids


def test_tactical_map_layers_endpoint(client, supervisor_headers):
    """Verifies that the tactical COP map layers endpoint returns flood zones, corridors, and units."""
    res = client.get("/v1/dashboard/map-layers", headers=supervisor_headers)
    assert res.status_code == 200
    data = res.json()
    assert "zone" in data
    assert "inundation_polygon" in data
    assert len(data["inundation_polygon"]) >= 4
    assert "corridors" in data
    corridor_ids = [c["id"] for c in data["corridors"]]
    assert "ROUTE-88" in corridor_ids
    assert "ROUTE-4B" in corridor_ids
    assert len(data["infrastructure"]) >= 3
    assert len(data["active_units"]) >= 3


def test_multilingual_voice_triage(client, supervisor_headers):
    """Verifies multilingual voice emergency intake in Hindi and English."""
    # Hindi test
    res_hi = client.post(
        "/v1/ai/voice-triage",
        json={"simulated_transcript": "बाढ़ में 4 लोग फंसे हैं, तुरंत सहायता भेजो", "language_hint": "hi"},
        headers=supervisor_headers,
    )
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert data_hi["detected_language"] == "hi"
    assert data_hi["extraction"]["category"] == "RESCUE"
    assert data_hi["urgency_score"] > 60.0
    assert "NDMA" in data_hi["recommended_sop"]["issuing_body"] or "SDMA" in data_hi["recommended_sop"]["issuing_body"]

    # English test
    res_en = client.post(
        "/v1/ai/voice-triage",
        json={"simulated_transcript": "Critical flood water rising, 3 people trapped on roof near Sector 4 Bridge", "language_hint": "en"},
        headers=supervisor_headers,
    )
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert data_en["extraction"]["severity"] == "CRITICAL"
    assert data_en["urgency_score"] >= 70.0
