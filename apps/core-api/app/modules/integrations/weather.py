"""
IMD / Weather Provider Integration Adapter
"""
from typing import Dict, Any
from pydantic import BaseModel


class NormalizedWeatherData(BaseModel):
    location: str
    latitude: float
    longitude: float
    temperature_celsius: float
    rainfall_rate_mm_per_hr: float
    wind_speed_kmh: float
    hazard_warning: str
    forecast_window_hours: int
    is_simulated: bool = False


class WeatherService:
    @staticmethod
    async def get_current_conditions(lat: float, lon: float, location_name: str = "Disaster Zone") -> NormalizedWeatherData:
        """
        Fetches current weather conditions with deterministic fallback for field operations.
        """
        # In production, queries IMD / Open-Meteo / Azure Maps Weather
        # Fallback simulation logic for local-first testing
        is_flood_zone = lat > 26.0 and lon > 91.0
        return NormalizedWeatherData(
            location=location_name,
            latitude=lat,
            longitude=lon,
            temperature_celsius=28.5,
            rainfall_rate_mm_per_hr=45.0 if is_flood_zone else 5.0,
            wind_speed_kmh=35.0,
            hazard_warning="HEAVY_RAINFALL_ORANGE_ALERT" if is_flood_zone else "NORMAL",
            forecast_window_hours=24,
            is_simulated=True,
        )
