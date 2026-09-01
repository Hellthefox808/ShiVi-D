"""
Integrations Router - SACHET CAP Ingestion, Weather Telemetry & Federated Lakehouse Catalogs
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from app.core.security import get_current_user
from app.modules.integrations.sachet_cap import parse_cap_alert, NormalizedAlertResult
from app.modules.integrations.weather import WeatherService, NormalizedWeatherData
from app.modules.integrations.lakehouse import (
    LakehouseFederationService,
    FederatedCatalogConfig,
    FederatedTableMetadata,
)

router = APIRouter(prefix="/v1/integrations", tags=["Integrations"])


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
