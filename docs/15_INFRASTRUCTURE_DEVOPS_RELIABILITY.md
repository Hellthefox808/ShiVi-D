# ShiVi: Infrastructure, DevOps and Reliability Plan

## 1. Deployment Topology Evolution

```
[HACKATHON MVP (Docker Compose)]
  core-api (FastAPI) + command-web (Next.js) + postgres (PostGIS) + redis + minio
                             │
                             ▼
[PILOT / AZURE MANAGED TOPOLOGY]
  Azure Front Door (WAF) ──> Azure API Management (JWT/Throttling)
                                       │
                                       ▼
                     Azure Container Apps Environment
           ├── core-api (Autoscaling replicas)
           ├── command-web (Static Web Apps / Container)
           └── async-workers (Sync, AI, Media, Notifications)
                                       │
                ┌──────────────────────┼──────────────────────┐
                ▼                      ▼                      ▼
    Azure DB for PostgreSQL       Azure Service Bus       Azure Blob Storage
     (Flexible Server HA)         (Topics & Queues)       (Private Containers)
```

---

## 2. Infrastructure as Code (Azure Bicep Blueprint)

The pilot infrastructure is codified in standard Azure Bicep:
- `core-api` container app with managed identity integration to Key Vault.
- PostgreSQL Flexible Server with Zone-Redundant High Availability and automatic daily backups.
- Azure Blob Storage with soft-delete enabled (7-day retention window) and lifecycle archival rules.
- OpenTelemetry instrumentation exporting metrics to Azure Monitor Application Insights.

---

## 3. High Availability & Disaster Recovery Targets
- **Recovery Point Objective (RPO):** $< 1\text{ minute}$ (via PostgreSQL continuous WAL archiving and asynchronous read replicas).
- **Recovery Time Objective (RTO):** $< 5\text{ minutes}$ (automated Container App health check failovers).
- **Graceful Degradation:** If cloud services become completely unreachable, local field squads continue running locally on embedded SQLite with zero data loss.
