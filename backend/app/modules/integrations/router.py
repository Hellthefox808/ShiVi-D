"""
Integrations Router - SACHET CAP Ingestion, Weather Telemetry, Lakehouse Catalogs & Disaster SMS Gateway
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

router = APIRouter(prefix="/v1/integrations", tags=["Integrations & SMS Gateway"])


# ---------------------------------------------------------------------------
# NDMA SACHET / CAP Alerts & Weather Telemetry
# ---------------------------------------------------------------------------

@router.post("/alerts/cap", response_model=NormalizedAlertResult)
async def ingest_cap_alert(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Ingest authorized NDMA SACHET / CAP v1.2 alert payload.
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
    Fetch normalized hydro-meteorological weather telemetry.
    """
    data = await WeatherService.get_current_conditions(lat, lon, location_name)
    return data


@router.get("/lakehouse/catalogs", response_model=List[FederatedCatalogConfig])
async def list_federated_catalogs(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List connected BigLake Iceberg Federated Catalogs (Databricks Unity / AWS Glue).
    """
    return LakehouseFederationService.get_registered_catalogs()


@router.get("/lakehouse/catalogs/{catalog_name}/tables", response_model=List[FederatedTableMetadata])
async def list_federated_tables(
    catalog_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Inspect discovered Iceberg tables in the specified federated catalog.
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
    Ingest citizen/responder inbound SMS over cellular GSM or webhook.
    Extracts distress entities, calculates priority, logs incident,
    and returns immediate automated life-safety acknowledgment.
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
    Incident Commander tool to broadcast geo-targeted emergency alerts.
    Enforces GSM 160-character budget and multi-recipient queuing.
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
    Compress an incident event envelope into a <= 140-byte satellite SMS burst
    packet with IEEE 802.3 CRC-32 integrity validation.
    """
    return SMSGatewayService.encode_compact_burst(payload)


@router.post("/sms/compact/decode", response_model=DecodedSatelliteEvent)
async def decode_satellite_sms_burst(
    payload: CompactSMSBurstDecodeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Decode and validate a 140-byte satellite SMS burst string into structured
    event fields, checking CRC-32 checksum.
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
    Retrieve audit transmission history for inbound and outbound SMS/Satellite bursts.
    """
    return SMSGatewayService.get_logs(limit=limit)
