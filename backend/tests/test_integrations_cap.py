"""
Tests for NDMA SACHET / CAP v1.2 Integration Parser
"""
import pytest
from datetime import datetime
from app.modules.integrations.sachet_cap import parse_cap_alert


def test_parse_valid_sachet_cap_alert():
    sample_payload = {
        "identifier": "NDMA-SACHET-2026-09-0012",
        "sender": "India Meteorological Department (IMD)",
        "sent": "2026-09-01T20:30:00Z",
        "status": "Actual",
        "msgType": "Alert",
        "scope": "Public",
        "info": [
            {
                "category": "Met",
                "event": "Severe Flash Flood and Inundation Warning",
                "urgency": "Immediate",
                "severity": "Extreme",
                "certainty": "Observed",
                "headline": "Brahmaputra River Overflows Bank - Red Alert for Kamrup Metropolitan",
                "description": "Rapid water level rise exceeding danger mark by 1.8 meters. High risk of embankment breach.",
                "instruction": "Evacuate low-lying riverbank zones immediately to designated SDRF relief shelters.",
                "area": [
                    {
                        "areaDesc": "Kamrup Metropolitan Sector 4",
                        "polygon": "26.1856,91.7483 26.1950,91.7580 26.1750,91.7650 26.1856,91.7483",
                    }
                ],
            }
        ],
    }

    result = parse_cap_alert(sample_payload)

    assert result.alert_id == "NDMA-SACHET-2026-09-0012"
    assert result.issuing_authority == "India Meteorological Department (IMD)"
    assert result.hazard_event == "Severe Flash Flood and Inundation Warning"
    assert result.severity == "EXTREME"
    assert result.urgency == "IMMEDIATE"
    assert result.certainty == "OBSERVED"
    assert result.coordinates_polygon is not None
    assert len(result.coordinates_polygon) == 4
    assert result.coordinates_polygon[0] == [26.1856, 91.7483]
    assert len(result.raw_payload_hash) == 64
    assert result.is_official is True
