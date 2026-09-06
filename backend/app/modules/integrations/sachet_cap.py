"""
NDMA SACHET / Common Alerting Protocol (CAP v1.2) Integration Adapter
"""
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CAPArea(BaseModel):
    areaDesc: str
    polygon: Optional[str] = None  # Lat,Lon space-separated coordinate string
    circle: Optional[str] = None


class CAPInfo(BaseModel):
    category: str  # Geo, Met, Safety, Rescue, Fire, Health, Env, Transport, Infra, Other
    event: str  # e.g., "Flash Flood Warning", "Severe Cyclone"
    urgency: str  # Immediate, Expected, Future, Past, Unknown
    severity: str  # Extreme, Severe, Moderate, Minor, Unknown
    certainty: str  # Observed, Likely, Possible, Unlikely, Unknown
    headline: Optional[str] = None
    description: Optional[str] = None
    instruction: Optional[str] = None
    area: Optional[List[CAPArea]] = None


class CAPAlertPayload(BaseModel):
    identifier: str
    sender: str
    sent: datetime
    status: str = "Actual"  # Actual, Exercise, System, Test, Draft
    msgType: str = "Alert"  # Alert, Update, Cancel, Ack, Error
    scope: str = "Public"
    info: List[CAPInfo]


class NormalizedAlertResult(BaseModel):
    alert_id: str
    issuing_authority: str
    hazard_event: str
    severity: str
    urgency: str
    certainty: str
    effective_time: datetime
    affected_areas: List[str]
    coordinates_polygon: Optional[List[List[float]]] = None
    verbatim_instruction: Optional[str] = None
    raw_payload_hash: str
    is_official: bool = True


def parse_cap_alert(payload: Dict[str, Any]) -> NormalizedAlertResult:
    """
    Parses and normalizes an authorized CAP v1.2 JSON alert payload.
    """
    alert = CAPAlertPayload(**payload)
    info = alert.info[0] if alert.info else None
    if not info:
        raise ValueError("CAP Alert missing <info> segment")

    # Compute raw payload integrity hash
    raw_str = str(payload)
    payload_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    # Parse polygon coordinates if present (e.g. "26.1,91.7 26.2,91.8 26.3,91.7 26.1,91.7")
    coords: List[List[float]] = []
    area_descs: List[str] = []

    if info.area:
        for a in info.area:
            area_descs.append(a.areaDesc)
            if a.polygon:
                points = a.polygon.strip().split()
                for pt in points:
                    try:
                        lat, lon = pt.split(",")
                        coords.append([float(lat.strip()), float(lon.strip())])
                    except Exception:
                        pass

    return NormalizedAlertResult(
        alert_id=alert.identifier,
        issuing_authority=alert.sender,
        hazard_event=info.event,
        severity=info.severity.upper(),
        urgency=info.urgency.upper(),
        certainty=info.certainty.upper(),
        effective_time=alert.sent,
        affected_areas=area_descs or ["District 01"],
        coordinates_polygon=coords if coords else None,
        verbatim_instruction=info.instruction or info.description,
        raw_payload_hash=payload_hash,
        is_official=True,
    )
