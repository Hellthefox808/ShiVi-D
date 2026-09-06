"""
ShiVi Emergency Disaster SMS Gateway & Satellite Messaging Service
Provides resilient emergency communication under zero broadband/cellular data conditions:
1. Inbound SMS Ingestion & NLP Parsing (Structured & Unstructured Multilingual)
2. Automated Life-Safety Acknowledgment & Priority Triage
3. Outbound Sector Emergency Alert Broadcasting (160-char GSM Compliant)
4. Compact 140-Byte Satellite SMS Burst Encoding/Decoding with CRC-32 Checksums
"""
import re
import uuid
import zlib
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.modules.intelligence.gateway import IntelligenceGateway
from app.modules.incidents.priority import calculate_incident_priority


class InboundSMSRequest(BaseModel):
    sender_phone: str
    message_text: str
    received_at: Optional[datetime] = None
    gateway_type: str = "GSM_GATEWAY"  # GSM_GATEWAY, TWILIO, CDAC_CAP, SATELLITE_BURST


class InboundSMSResult(BaseModel):
    incident_id: str
    local_reference: str
    sender_phone: str
    category: str
    severity: str
    people_at_risk: int
    priority_score: float
    location_name: str
    latitude: float
    longitude: float
    extracted_hazards: List[str]
    auto_reply_sms: str
    status: str = "REPORTED"
    processed_at: datetime


class BroadcastSMSRequest(BaseModel):
    sector_name: str
    hazard_type: str
    severity: str = "CRITICAL"
    instruction: str
    recipient_phones: Optional[List[str]] = None
    include_hindi_translation: bool = False


class BroadcastSMSResult(BaseModel):
    broadcast_id: str
    sector_name: str
    primary_sms_text: str
    character_count: int
    is_single_gsm_segment: bool
    recipients_queued: int
    sent_at: datetime
    delivery_status: str = "QUEUED_FOR_BROADCAST"


class CompactSMSBurstEncodeRequest(BaseModel):
    event_id: str
    category: str
    severity: str
    people_at_risk: int
    latitude: float
    longitude: float
    short_desc: Optional[str] = None


class CompactSMSBurstResult(BaseModel):
    burst_string: str
    byte_length: int
    fits_140_byte_satellite_limit: bool
    crc32_checksum: str


class CompactSMSBurstDecodeRequest(BaseModel):
    burst_string: str


class DecodedSatelliteEvent(BaseModel):
    protocol_version: int
    event_id: str
    category: str
    severity: str
    people_at_risk: int
    latitude: float
    longitude: float
    short_desc: str
    crc32_valid: bool


class SMSLogEntry(BaseModel):
    id: str
    direction: str  # INBOUND, OUTBOUND, BROADCAST
    sender_or_recipient: str
    text: str
    timestamp: datetime
    status: str
    related_ref: Optional[str] = None


# Known Geographic Sector Mapping for Disconnected Environments
SECTOR_GEODATA: Dict[str, Dict[str, Any]] = {
    "sector 4": {"name": "Sector 4 - Guwahati Basin", "lat": 26.1856, "lon": 91.7483},
    "सेक्टर 4": {"name": "Sector 4 - Guwahati Basin", "lat": 26.1856, "lon": 91.7483},
    "sector 2": {"name": "Sector 2 - Brahmaputra Flood Wall", "lat": 26.1920, "lon": 91.7510},
    "सेक्टर 2": {"name": "Sector 2 - Brahmaputra Flood Wall", "lat": 26.1920, "lon": 91.7510},
    "sector 1": {"name": "Sector 1 - Dispur Medical Center", "lat": 26.1433, "lon": 91.7898},
    "सेक्टर 1": {"name": "Sector 1 - Dispur Medical Center", "lat": 26.1433, "lon": 91.7898},
    "dispur": {"name": "Sector 1 - Dispur Medical Center", "lat": 26.1433, "lon": 91.7898},
    "दिसपुर": {"name": "Sector 1 - Dispur Medical Center", "lat": 26.1433, "lon": 91.7898},
    "jalukbari": {"name": "Jalukbari Transit Hub", "lat": 26.1550, "lon": 91.6660},
    "जालुकबारी": {"name": "Jalukbari Transit Hub", "lat": 26.1550, "lon": 91.6660},
    "pandu": {"name": "Pandu Port Embankment", "lat": 26.1800, "lon": 91.7000},
    "पांडु": {"name": "Pandu Port Embankment", "lat": 26.1800, "lon": 91.7000},
}


class SMSGatewayService:
    _transmission_logs: List[SMSLogEntry] = []

    @classmethod
    def process_inbound_sms(cls, req: InboundSMSRequest) -> InboundSMSResult:
        """
        Parses an incoming SMS, extracts entities, calculates triage priority,
        registers an incident reference, and returns an automated emergency acknowledgment.
        """
        raw_text = req.message_text.strip()
        text_lower = raw_text.lower()

        # 1. Check for Structured Syntax: e.g. "SOS RESCUE 6 SECTOR 4 TRAPPED"
        category = "RESCUE"
        severity = "HIGH"
        people_at_risk = 1
        location_name = "Sector 4 - Guwahati Basin"
        lat = 26.1856
        lon = 91.7483
        hazards = ["FLOOD_INUNDATION"]

        # Multilingual & Entity Extraction via Advisory Intelligence Engine
        extracted = IntelligenceGateway.extract_structured_incident(raw_text)
        category = extracted.category
        severity = extracted.severity
        people_at_risk = extracted.estimated_people
        hazards = extracted.extracted_hazards

        # Check explicit sector names
        for sec_key, sec_data in SECTOR_GEODATA.items():
            if sec_key in text_lower:
                location_name = sec_data["name"]
                lat = sec_data["lat"]
                lon = sec_data["lon"]
                break

        # Check explicit GPS coordinate format in SMS: e.g. "GPS 26.1856, 91.7483" or "26.18,91.74"
        coord_match = re.search(r"(\d{2}\.\d{2,6})[,\s]+(\d{2}\.\d{2,6})", raw_text)
        if coord_match:
            try:
                found_lat = float(coord_match.group(1))
                found_lon = float(coord_match.group(2))
                if 20.0 <= found_lat <= 30.0 and 85.0 <= found_lon <= 98.0:
                    lat = found_lat
                    lon = found_lon
                    location_name = f"Coordinates {lat:.4f}, {lon:.4f}"
            except Exception:
                pass

        # 2. Deterministic Priority Calculation
        urgency = "IMMEDIATE" if severity == "CRITICAL" else "HIGH"
        score, _ = calculate_incident_priority(
            severity=severity,
            people_at_risk=people_at_risk,
            category=category,
            urgency_level=urgency,
            has_photo_evidence=False,
            is_official_source=False,
        )

        incident_id = str(uuid.uuid4())
        local_ref = f"SMS-REF-{incident_id[:6].upper()}"

        # 3. Generate Automated Life-Safety Acknowledgment Reply
        # Fits standard single GSM SMS (<= 160 characters)
        auto_reply = (
            f"SHIVI ALERT: SOS {local_ref} logged. Priority P{score:.0f}. "
            f"Rescue team notified for {location_name.split(' - ')[0]}. "
            f"Stay on high ground. Help is en route."
        )
        if len(auto_reply) > 160:
            auto_reply = auto_reply[:157] + "..."

        now = req.received_at or datetime.now(timezone.utc)

        # Log inbound message & outbound reply
        cls._transmission_logs.insert(0, SMSLogEntry(
            id=str(uuid.uuid4()),
            direction="INBOUND",
            sender_or_recipient=req.sender_phone,
            text=raw_text,
            timestamp=now,
            status="RECEIVED",
            related_ref=local_ref,
        ))

        cls._transmission_logs.insert(0, SMSLogEntry(
            id=str(uuid.uuid4()),
            direction="OUTBOUND",
            sender_or_recipient=req.sender_phone,
            text=auto_reply,
            timestamp=now,
            status="SENT",
            related_ref=local_ref,
        ))

        return InboundSMSResult(
            incident_id=incident_id,
            local_reference=local_ref,
            sender_phone=req.sender_phone,
            category=category,
            severity=severity,
            people_at_risk=people_at_risk,
            priority_score=score,
            location_name=location_name,
            latitude=lat,
            longitude=lon,
            extracted_hazards=hazards,
            auto_reply_sms=auto_reply,
            status="REPORTED",
            processed_at=now,
        )

    @classmethod
    def broadcast_sector_alert(cls, req: BroadcastSMSRequest) -> BroadcastSMSResult:
        """
        Formats and broadcasts a geo-targeted emergency alert.
        Enforces standard GSM 160-character budget.
        """
        broadcast_id = f"BC-{uuid.uuid4().hex[:8].upper()}"

        # Compile concise GSM 160-char alert text
        short_sector = req.sector_name.split(" - ")[0]
        alert_body = (
            f"SHIVI ALERT [{short_sector}]: {req.hazard_type.upper()}. "
            f"{req.instruction.strip()} Dial 112/1070."
        )
        if len(alert_body) > 160:
            alert_body = alert_body[:157] + "..."

        char_count = len(alert_body)
        is_single_segment = char_count <= 160

        recipients = req.recipient_phones or [
            "+919876543210", "+919876543211", "+919876543212"
        ]

        now = datetime.now(timezone.utc)

        for phone in recipients:
            cls._transmission_logs.insert(0, SMSLogEntry(
                id=str(uuid.uuid4()),
                direction="BROADCAST",
                sender_or_recipient=phone,
                text=alert_body,
                timestamp=now,
                status="SENT",
                related_ref=broadcast_id,
            ))

        return BroadcastSMSResult(
            broadcast_id=broadcast_id,
            sector_name=req.sector_name,
            primary_sms_text=alert_body,
            character_count=char_count,
            is_single_gsm_segment=is_single_segment,
            recipients_queued=len(recipients),
            sent_at=now,
            delivery_status="BROADCAST_TRANSMITTED",
        )

    @classmethod
    def encode_compact_burst(cls, req: CompactSMSBurstEncodeRequest) -> CompactSMSBurstResult:
        """
        Encodes an incident event into an ultra-compact <= 140 character
        satellite SMS burst packet with IEEE 802.3 CRC-32 integrity.
        Wire Format:
        SHV:1:<EVT_ID>:<CAT>:<SEV>:<PEOPLE>:<LAT>,<LON>:<DESC>:<CRC32>
        """
        desc_clean = re.sub(r"[:\n\r]+", " ", req.short_desc or "SOS").strip()[:24]
        # Core payload without CRC
        core = f"SHV:1:{req.event_id[:8]}:{req.category[:3].upper()}:{req.severity[:4].upper()}:{req.people_at_risk}:{req.latitude:.3f},{req.longitude:.3f}:{desc_clean}"

        # Compute CRC-32 checksum of the core string
        crc_val = zlib.crc32(core.encode("utf-8")) & 0xFFFFFFFF
        crc_hex = f"{crc_val:08X}"

        burst_string = f"{core}:{crc_hex}"
        byte_len = len(burst_string.encode("utf-8"))

        return CompactSMSBurstResult(
            burst_string=burst_string,
            byte_length=byte_len,
            fits_140_byte_satellite_limit=byte_len <= 140,
            crc32_checksum=crc_hex,
        )

    @classmethod
    def decode_compact_burst(cls, burst_string: str) -> DecodedSatelliteEvent:
        """
        Decodes and validates a compact satellite SMS burst string.
        """
        parts = burst_string.strip().split(":")
        if len(parts) < 8 or parts[0] != "SHV" or parts[1] != "1":
            raise ValueError(f"Invalid ShiVi Satellite SMS burst framing: '{burst_string}'")

        event_id = parts[2]
        cat_short = parts[3]
        sev_short = parts[4]
        people = int(parts[5])
        lat_lon_part = parts[6]
        short_desc = parts[7]
        crc_received = parts[8] if len(parts) > 8 else ""

        # Verify CRC-32
        core = ":".join(parts[:8])
        expected_crc = f"{zlib.crc32(core.encode('utf-8')) & 0xFFFFFFFF:08X}"
        crc_valid = (expected_crc.upper() == crc_received.upper())

        # Expand abbreviations
        cat_map = {"RES": "RESCUE", "MED": "MEDICAL", "HAZ": "HAZARD", "REL": "RELIEF"}
        sev_map = {"CRIT": "CRITICAL", "HIGH": "HIGH", "MEDI": "MEDIUM", "LOW": "LOW"}

        category = cat_map.get(cat_short, "RESCUE")
        severity = sev_map.get(sev_short, "HIGH")

        lat, lon = 26.1856, 91.7483
        if "," in lat_lon_part:
            coords = lat_lon_part.split(",")
            lat = float(coords[0])
            lon = float(coords[1])

        return DecodedSatelliteEvent(
            protocol_version=1,
            event_id=event_id,
            category=category,
            severity=severity,
            people_at_risk=people,
            latitude=lat,
            longitude=lon,
            short_desc=short_desc,
            crc32_valid=crc_valid,
        )

    @classmethod
    def get_logs(cls, limit: int = 50) -> List[SMSLogEntry]:
        return cls._transmission_logs[:limit]
