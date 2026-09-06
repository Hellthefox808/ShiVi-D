import pytest
from app.modules.integrations.sms import (
    SMSGatewayService,
    InboundSMSRequest,
    BroadcastSMSRequest,
    CompactSMSBurstEncodeRequest,
    CompactSMSBurstDecodeRequest,
)


@pytest.mark.asyncio
async def test_inbound_sms_structured_syntax():
    req = InboundSMSRequest(
        sender_phone="+919876543212",
        message_text="SOS RESCUE 6 SECTOR 4 TRAPPED ON ROOFTOP WATER RISING",
        gateway_type="GSM_GATEWAY",
    )
    result = SMSGatewayService.process_inbound_sms(req)

    assert result.local_reference.startswith("SMS-REF-")
    assert result.category == "RESCUE"
    assert result.severity == "CRITICAL"
    assert result.people_at_risk == 6
    assert "Sector 4" in result.location_name
    assert result.priority_score >= 60.0
    assert len(result.auto_reply_sms) <= 160
    assert "SHIVI ALERT: SOS" in result.auto_reply_sms
    assert "Stay on high ground" in result.auto_reply_sms


@pytest.mark.asyncio
async def test_inbound_sms_multilingual_hindi():
    req = InboundSMSRequest(
        sender_phone="+919876543215",
        message_text="बाढ़ में 4 लोग फंसे हैं तुरंत नाव चाहिए सेक्टर 2",
        gateway_type="TWILIO",
    )
    result = SMSGatewayService.process_inbound_sms(req)

    assert result.category == "RESCUE"
    assert result.people_at_risk == 4
    assert "Sector 2" in result.location_name
    assert result.priority_score >= 50.0
    assert len(result.auto_reply_sms) <= 160


@pytest.mark.asyncio
async def test_inbound_sms_explicit_coordinates():
    req = InboundSMSRequest(
        sender_phone="+919876543216",
        message_text="CRITICAL MEDICAL 2 INJURED UNCONSCIOUS GPS 26.1433, 91.7898",
        gateway_type="GSM_GATEWAY",
    )
    result = SMSGatewayService.process_inbound_sms(req)

    assert result.category == "MEDICAL"
    assert result.severity == "CRITICAL"
    assert result.people_at_risk == 2
    assert abs(result.latitude - 26.1433) < 0.001
    assert abs(result.longitude - 91.7898) < 0.001


@pytest.mark.asyncio
async def test_outbound_sector_broadcast():
    req = BroadcastSMSRequest(
        sector_name="Sector 4 - Guwahati Basin",
        hazard_type="Flash Flood Warning",
        severity="CRITICAL",
        instruction="Route-88 Bridge Breached. Detour via Sector 4 Boat Ramp active.",
        recipient_phones=["+919876543210", "+919876543211"],
    )
    result = SMSGatewayService.broadcast_sector_alert(req)

    assert result.broadcast_id.startswith("BC-")
    assert result.sector_name == "Sector 4 - Guwahati Basin"
    assert result.character_count <= 160
    assert result.is_single_gsm_segment is True
    assert result.recipients_queued == 2
    assert result.delivery_status == "BROADCAST_TRANSMITTED"


@pytest.mark.asyncio
async def test_compact_satellite_sms_burst_roundtrip():
    req = CompactSMSBurstEncodeRequest(
        event_id="EVT-A9F8E7",
        category="RESCUE",
        severity="CRITICAL",
        people_at_risk=5,
        latitude=26.185,
        longitude=91.748,
        short_desc="ROOFTOP FLOOD EVAC",
    )
    encoded = SMSGatewayService.encode_compact_burst(req)

    assert encoded.fits_140_byte_satellite_limit is True
    assert encoded.byte_length <= 140
    assert encoded.burst_string.startswith("SHV:1:EVT-A9F8:RES:CRIT:5:26.185,91.748")
    assert len(encoded.crc32_checksum) == 8

    # Decode
    decoded = SMSGatewayService.decode_compact_burst(encoded.burst_string)
    assert decoded.protocol_version == 1
    assert decoded.event_id == "EVT-A9F8"
    assert decoded.category == "RESCUE"
    assert decoded.severity == "CRITICAL"
    assert decoded.people_at_risk == 5
    assert abs(decoded.latitude - 26.185) < 0.001
    assert abs(decoded.longitude - 91.748) < 0.001
    assert decoded.short_desc == "ROOFTOP FLOOD EVAC"
    assert decoded.crc32_valid is True


@pytest.mark.asyncio
async def test_compact_satellite_sms_corrupted_crc():
    req = CompactSMSBurstEncodeRequest(
        event_id="EVT-TAMPER",
        category="HAZARD",
        severity="HIGH",
        people_at_risk=1,
        latitude=26.180,
        longitude=91.740,
        short_desc="GAS LEAK",
    )
    encoded = SMSGatewayService.encode_compact_burst(req)

    # Tamper CRC hex at the end
    tampered_string = encoded.burst_string[:-4] + "DEAD"
    decoded = SMSGatewayService.decode_compact_burst(tampered_string)
    assert decoded.crc32_valid is False


@pytest.mark.asyncio
async def test_sms_transmission_logs():
    logs = SMSGatewayService.get_logs(limit=20)
    assert isinstance(logs, list)
    assert len(logs) > 0
    directions = {log.direction for log in logs}
    assert "INBOUND" in directions or "OUTBOUND" in directions or "BROADCAST" in directions
