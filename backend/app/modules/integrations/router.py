"""
ShiVi Integrations & Telemetry API Router
=========================================

Briefing:
    Unified integrations router bridging the ShiVi platform with external civil defense systems,
    analytical cloud lakehouses, weather networks, and resilient disaster messaging relays.

Integrated Systems:
    1. NDMA SACHET / Common Alerting Protocol (CAP v1.2): Ingests government civil alerts.
    2. Meteorological Telemetry: Live hydro-weather telemetry (IMD, rainfall rates, flood alerts).
    3. BigLake Apache Iceberg Catalogs: Cross-cloud metadata federation (Databricks Unity / AWS Glue).
    4. Disaster SMS & Satellite Burst Gateway: 2G SMS intake, 160-char broadcasts, and 140-byte
       compact satellite burst packetization with CRC-32 checksums.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from app.core.security import get_current_user
from app.modules.integrations.sachet_cap import parse_cap_alert, NormalizedAlertResult
from app.modules.integrations.weather import WeatherService, NormalizedWeatherData
from app.modules.integrations.lakehouse import (
    LakehouseFederationService,
    FederatedCatalogConfig,
    FederatedTableMetadata,
)
from app.modules.integrations.sms import (
    SMSGatewayService,
    InboundSMSRequest,
    InboundSMSResult,
    BroadcastSMSRequest,
    BroadcastSMSResult,
    CompactSMSBurstEncodeRequest,
    CompactSMSBurstResult,
    CompactSMSBurstDecodeRequest,
    DecodedSatelliteEvent,
    SMSLogEntry,
)

# Briefing: FastAPI Router mounted under `/integrations` for multi-agency external protocols.
# Reason: Centralizes adapters for external telemetry, messaging, and analytical lakehouses.
router = APIRouter(prefix="/integrations", tags=["Integrations & SMS Gateway"])


# ---------------------------------------------------------------------------
# NDMA SACHET / CAP Alerts & Weather Telemetry
# ---------------------------------------------------------------------------

@router.post("/alerts/cap", response_model=NormalizedAlertResult)
async def ingest_cap_alert(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Ingests and normalizes an authorized NDMA SACHET / CAP v1.2 alert payload.

    Reason:
        Parses government hazard perimeters and evacuation instructions into GIS polygons
        and calculates a SHA-256 payload integrity hash.

    Parameters:
        payload: Inbound CAP v1.2 JSON payload.
        current_user: Authenticated user or service account.

    Returns:
        `NormalizedAlertResult` populated with parsed coordinates and hazard event details.

    Raises:
        HTTPException(422): If payload parsing fails.
    """
    try:
        result = parse_cap_alert(payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse CAP v1.2 payload: {str(e)}",
        )


@router.get("/weather", response_model=NormalizedWeatherData)
async def get_weather_telemetry(
    lat: float = 26.1856,
    lon: float = 91.7483,
    location_name: str = "Guwahati Flood Sector",
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Retrieves real-time hydro-meteorological weather telemetry for tactical coordinates.

    Reason:
        Provides rainfall rate (mm/hr), wind velocity, and hazard warning levels to dispatchers
        and priority calculation algorithms.

    Parameters:
        lat: WGS84 Latitude.
        lon: WGS84 Longitude.
        location_name: Geographic sector headline.
        current_user: Authenticated user.

    Returns:
        `NormalizedWeatherData` object.
    """
    data = await WeatherService.get_current_conditions(lat, lon, location_name)
    return data


@router.get("/lakehouse/catalogs", response_model=List[FederatedCatalogConfig])
async def list_federated_catalogs(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Lists all connected BigLake Apache Iceberg federated catalogs (Databricks Unity / AWS Glue).

    Reason:
        Enables analytical dashboards to inspect which cross-cloud lakehouses are synchronized.

    Returns:
        List of `FederatedCatalogConfig` models.
    """
    return LakehouseFederationService.get_registered_catalogs()


@router.get("/lakehouse/catalogs/{catalog_name}/tables", response_model=List[FederatedTableMetadata])
async def list_federated_tables(
    catalog_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Inspects discovered Iceberg table schemas in the specified federated catalog.

    Parameters:
        catalog_name: Name of target catalog.

    Returns:
        List of `FederatedTableMetadata` records.
    """
    return LakehouseFederationService.inspect_sample_tables(catalog_name)


# ---------------------------------------------------------------------------
# Disaster SMS Gateway & Satellite Burst Messaging Endpoints
# ---------------------------------------------------------------------------

@router.post("/sms/inbound", response_model=InboundSMSResult)
async def process_inbound_emergency_sms(
    payload: InboundSMSRequest,
):
    """
    Briefing:
        Ingests inbound emergency SMS from citizens or responders over GSM or satellite relays.

    Reason:
        Extracts distress parameters using multilingual NLP, computes explainable priority,
        registers an incident, and returns an immediate automated life-safety acknowledgment reply.

    Parameters:
        payload: `InboundSMSRequest` with sender number and text.

    Returns:
        `InboundSMSResult` detailing incident reference and auto-reply text.
    """
    try:
        result = SMSGatewayService.process_inbound_sms(payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process inbound emergency SMS: {str(e)}",
        )


@router.post("/sms/broadcast", response_model=BroadcastSMSResult)
async def broadcast_sector_alert(
    payload: BroadcastSMSRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Broadcasts a geo-targeted emergency alert to civilian phones in an endangered sector.

    Reason:
        Enforces standard GSM single-segment 160-character budgets to guarantee delivery.

    Parameters:
        payload: `BroadcastSMSRequest` specifying sector, hazard, and instructions.

    Returns:
        `BroadcastSMSResult` detailing queued recipient counts and transmission status.
    """
    try:
        result = SMSGatewayService.broadcast_sector_alert(payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to transmit sector broadcast: {str(e)}",
        )


@router.post("/sms/compact/encode", response_model=CompactSMSBurstResult)
async def encode_satellite_sms_burst(
    payload: CompactSMSBurstEncodeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Compresses an incident event into a <= 140-byte satellite SMS burst packet with CRC-32 integrity.

    Reason:
        Complies with low-bandwidth satellite transceiver limits (Iridium SBD, Inmarsat).

    Parameters:
        payload: `CompactSMSBurstEncodeRequest`.

    Returns:
        `CompactSMSBurstResult` containing encoded burst string.
    """
    return SMSGatewayService.encode_compact_burst(payload)


@router.post("/sms/compact/decode", response_model=DecodedSatelliteEvent)
async def decode_satellite_sms_burst(
    payload: CompactSMSBurstDecodeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Decodes and validates a raw satellite SMS burst string, verifying CRC-32 checksums.

    Parameters:
        payload: `CompactSMSBurstDecodeRequest`.

    Returns:
        `DecodedSatelliteEvent` with verified coordinates and categories.
    """
    try:
        return SMSGatewayService.decode_compact_burst(payload.burst_string)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid or corrupted satellite SMS burst: {str(e)}",
        )


@router.get("/sms/logs", response_model=List[SMSLogEntry])
async def get_sms_transmission_logs(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Retrieves transmission history for inbound, outbound, and broadcast SMS/satellite messages.

    Parameters:
        limit: Number of log records to return (default 50).

    Returns:
        List of `SMSLogEntry` records.
    """
    return SMSGatewayService.get_logs(limit=limit)
