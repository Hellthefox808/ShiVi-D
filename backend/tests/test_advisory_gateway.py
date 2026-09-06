"""
Tests for Advisory AI Gateway
"""
import pytest
from app.modules.intelligence.gateway import IntelligenceGateway


def test_extract_incident_flood_rescue():
    transcript = "We are 5 people trapped on the roof near Sector 4 Bridge, water is rising fast please send boat!"
    res = IntelligenceGateway.extract_structured_incident(transcript)

    assert res.category == "RESCUE"
    assert res.severity == "CRITICAL"
    assert res.estimated_people == 5
    assert "FLOOD_INUNDATION" in res.extracted_hazards
    assert res.confidence >= 0.8


def test_extract_medical_emergency():
    transcript = "Need immediate doctor, elderly patient having severe chest pain and bleeding."
    res = IntelligenceGateway.extract_structured_incident(transcript)

    assert res.category == "MEDICAL"
    assert res.severity == "CRITICAL"
    assert "MEDICAL_EMERGENCY" in res.extracted_hazards


def test_retrieve_sop_rescue():
    sop = IntelligenceGateway.retrieve_sop("RESCUE", "CRITICAL")
    assert sop.sop_code == "NDMA-SOP-FL-04"
    assert "Inflatable Rescue Boat" in sop.mandatory_checklist[2] or "Inflatable Boat (IRB)" in sop.required_equipment
    assert "NDMA" in sop.issuing_body
