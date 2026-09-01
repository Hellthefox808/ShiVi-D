# ShiVi: Pilot and Production Roadmap

## 1. Phase 0: 24-Hour MVP Baseline (Completed & Verified)
- Dockerized FastAPI modular monolith + Next.js 14 Web Command Center.
- Validated P0 loop: Offline report $\rightarrow$ Causal sync $\rightarrow$ Assignment $\rightarrow$ Concurrent updates $\rightarrow$ Auto-merge + Protected conflict freeze $\rightarrow$ Supervisor adjudication $\rightarrow$ Evidence verification $\rightarrow$ Audit ledger.

## 2. Phase 1: Controlled Field Pilot (Months 1 - 3)
- **Target Deployment:** District Disaster Management Authority (DDMA) / SDRF Battalion in flood-prone Brahmaputra Basin (Assam) or coastal Odisha.
- **Infrastructure:** Azure Container Apps, Azure Database for PostgreSQL Flexible Server (HA), Azure Blob Storage, and Microsoft Entra ID authentication.
- **Key Validation KPIs:**
  - $> 99.9\%$ offline event recovery ratio.
  - $< 2\text{ minutes}$ average report-to-dispatch turnaround time.
  - Zero unadjudicated silent overwrites.

## 3. Phase 2: Regional Scaling & Cross-Sector Packs (Months 4 - 9)
- Release of pluggable Sector Packs:
  - **Public Health Pack:** Disease outbreak surveillance, village health worker tasking, cold-chain vaccine logistics.
  - **Municipal Utilities Pack:** Water pipeline burst reporting, road pothole repair dispatch, waste management.
  - **Agricultural Extension Pack:** Pest outbreak tracking, crop damage assessment, fertilizer subsidy field verification.

## 4. Phase 3: Enterprise Platform & State-Wide Integration (Months 10 - 18)
- Full integration with NDMA SACHET national gateway and State Emergency Operations Centers (SEOC).
- Dedicated private cloud deployment tiers for sensitive defense and critical infrastructure agencies.
