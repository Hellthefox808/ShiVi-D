# ShiVi: Ecosystem and Integration Architecture

## 1. External Integration Boundaries

```
[Official Alert Gateways]        [Geospatial Providers]         [Weather Providers]
 - NDMA SACHET (CAP v1.2)         - ISRO/NRSC NDEM (WMS/WFS)    - IMD Grid Telemetry
 - State Disaster Portals         - OpenStreetMap / OSRM        - Azure Maps Weather
               │                             │                           │
               └──────────────────────┬──────┴───────────────────────────┘
                                      │
                                      ▼
                      [ShiVi Integration Gateway Layer]
                   - Digital Signature & Provenance Check
                   - Schema Normalization & Deduplication
                   - Polygon Intersection Calculation
                                      │
                                      ▼
                           [ShiVi Operations Core]
```

---

## 2. Integration Adapters

### 2.1 NDMA SACHET / CAP Ingestion Adapter
- **Protocol:** Common Alerting Protocol v1.2 XML / JSON.
- **Workflow:**
  1. Receive webhook notification or poll authorized SACHET endpoint.
  2. Verify issuing authority signature and raw payload hash.
  3. Extract `<polygon>` / `<circle>` geospatial affected bounds.
  4. Perform PostGIS spatial intersection against active registered responder zones.
  5. Generate operational readiness alerts without altering official source text.

### 2.2 Weather & Hydro Telemetry Adapter
- **Provider Interface:**
  ```python
  class WeatherAdapter(Protocol):
      async def fetch_forecast(self, lat: float, lon: float) -> NormalizedWeatherObject:
          ...
  ```
- **Fallback Hierarchy:** Official IMD API $\rightarrow$ Azure Maps Weather $\rightarrow$ Local District Gauge Sensor $\rightarrow$ Mock Simulation Adapter.

### 2.3 ODK / KoboToolbox / CommCare Field Bridge
- **Purpose:** Ingest field survey data from existing NGO mobile teams.
- **Mapping:** Survey submissions with emergency tags automatically open a ShiVi incident; task completion updates are returned via signed webhooks to maintain external case records.
