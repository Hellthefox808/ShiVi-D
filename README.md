# ShiVi (Smart Hybrid Intelligent Virtual Integration)

> **The execution layer for distributed teams operating when connectivity and information cannot be trusted.**

---

## 📌 Architecture Overview

ShiVi is a local-first, conflict-aware, human-authorized operational coordination platform engineered for extreme reliability during natural disasters, humanitarian crises, and distributed field operations.

```text
Official Ecosystem (NDMA SACHET / CAP, NDEM, IMD)
                       ↓
               Integration Gateway
                       ↓
              ShiVi Operations Core
 (Incident → Priority → Assignment → Action → Evidence)
                       ↓
     Causal Delta Sync + Domain Conflict Engine
                       ↓
           Immutable Audit Ledger & Traceability
```

---

## 🚀 Quickstart (Docker Compose)

Launch the complete ShiVi ecosystem with a single command:

```bash
docker compose up -d --build
```

### Services & Endpoints

- **Web Command Center:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Operations API:** [http://localhost:8000](http://localhost:8000) (Interactive Swagger docs at `/docs`)
- **PostgreSQL + PostGIS:** `localhost:5432` (`postgres:shivi_secret`)
- **Redis Cache & Queue Broker:** `localhost:6379`
- **MinIO S3-Compatible Object Store:** [http://localhost:9001](http://localhost:9001) (`admin:shivi_minio_secret`)

---

## 🧪 Running the Verification Suites

### 1. Automated Test Suite (Pytest)

```bash
.\.venv\Scripts\pytest
```

*Executes all 28 unit, integration, and conflict-freeze tests in memory with 100% pass rate.*

### 2. End-to-End P0 Multi-Device Concurrency Simulation

```bash
.\.venv\Scripts\python scripts/simulate_p0_demo.py
```

### Demonstration Steps Validated

1. **Offline Incident Capture:** Citizen reports 3 stranded people offline; commits atomically to local outbox.
2. **Causal Sync:** Device reconnects; server deduplicates and materializes incident.
3. **Triage & Dispatch:** Supervisor inspects explainable priority factors and assigns responder squad.
4. **Concurrent Field Updates:**
   - Device A logs Route 88 as `USABLE` with photograph.
   - Device B logs Route 88 as `BLOCKED` with warning note.
5. **Conflict Safety Freeze:** Server auto-merges metadata, detects life-safety contradiction, sets Route 88 to `UNCERTAIN`, and freezes dependent dispatches.
6. **Supervisor Adjudication:** Authorized supervisor reviews evidence and sets status to `BLOCKED` with mandatory justification.
7. **Task Re-routing & Completion:** Affected tasks recalculate; responder uploads rescue evidence.
8. **Supervisor Verification & Audit:** Supervisor approves closure; complete immutable audit trail is displayed.

---

## 📚 Complete Founder & Principal-Engineer Documentation Suite

All 22 architectural specifications and deliverables are available in `docs/`:

1. [01_EXECUTIVE_PROJECT_BRIEF.md](file:///d:/ShiVi,/docs/01_EXECUTIVE_PROJECT_BRIEF.md)
2. [02_RESEARCH_AND_EVIDENCE_REVIEW.md](file:///d:/ShiVi,/docs/02_RESEARCH_AND_EVIDENCE_REVIEW.md)
3. [03_PRODUCT_REQUIREMENTS_DOCUMENT.md](file:///d:/ShiVi,/docs/03_PRODUCT_REQUIREMENTS_DOCUMENT.md)
4. [04_FUNCTIONAL_SPECIFICATION_DOCUMENT.md](file:///d:/ShiVi,/docs/04_FUNCTIONAL_SPECIFICATION_DOCUMENT.md)
5. [05_CONTEXT_LOOP_SPECIFICATION.md](file:///d:/ShiVi,/docs/05_CONTEXT_LOOP_SPECIFICATION.md)
6. [06_SYSTEM_ARCHITECTURE_DOCUMENT.md](file:///d:/ShiVi,/docs/06_SYSTEM_ARCHITECTURE_DOCUMENT.md)
7. [07_TECHNICAL_ARCHITECTURE_DOCUMENT.md](file:///d:/ShiVi,/docs/07_TECHNICAL_ARCHITECTURE_DOCUMENT.md)
8. [08_DATA_MODEL_AND_EVENT_CONTRACTS.md](file:///d:/ShiVi,/docs/08_DATA_MODEL_AND_EVENT_CONTRACTS.md)
9. [09_SYNC_AND_CONFLICT_RESOLUTION_SPEC.md](file:///d:/ShiVi,/docs/09_SYNC_AND_CONFLICT_RESOLUTION_SPEC.md)
10. [10_API_SPECIFICATION.md](file:///d:/ShiVi,/docs/10_API_SPECIFICATION.md)
11. [11_SECURITY_PRIVACY_THREAT_MODEL.md](file:///d:/ShiVi,/docs/11_SECURITY_PRIVACY_THREAT_MODEL.md)
12. [12_AI_HYBRID_INTELLIGENCE_SPEC.md](file:///d:/ShiVi,/docs/12_AI_HYBRID_INTELLIGENCE_SPEC.md)
13. [13_UI_UX_ACCESSIBILITY_BLUEPRINT.md](file:///d:/ShiVi,/docs/13_UI_UX_ACCESSIBILITY_BLUEPRINT.md)
14. [14_ECOSYSTEM_INTEGRATION_ARCHITECTURE.md](file:///d:/ShiVi,/docs/14_ECOSYSTEM_INTEGRATION_ARCHITECTURE.md)
15. [15_INFRASTRUCTURE_DEVOPS_RELIABILITY.md](file:///d:/ShiVi,/docs/15_INFRASTRUCTURE_DEVOPS_RELIABILITY.md)
16. [16_OBSERVABILITY_INCIDENT_RESPONSE.md](file:///d:/ShiVi,/docs/16_OBSERVABILITY_INCIDENT_RESPONSE.md)
17. [17_TESTING_CHAOS_STRATEGY.md](file:///d:/ShiVi,/docs/17_TESTING_CHAOS_STRATEGY.md)
18. [18_24_HOUR_HACKATHON_EXECUTION_PLAN.md](file:///d:/ShiVi,/docs/18_24_HOUR_HACKATHON_EXECUTION_PLAN.md)
19. [19_PILOT_PRODUCTION_ROADMAP.md](file:///d:/ShiVi,/docs/19_PILOT_PRODUCTION_ROADMAP.md)
20. [20_BUSINESS_MODEL_UNIT_LOGIC_SCALE.md](file:///d:/ShiVi,/docs/20_BUSINESS_MODEL_UNIT_LOGIC_SCALE.md)
21. [21_PITCH_DEMO_AND_JUDGE_QA.md](file:///d:/ShiVi,/docs/21_PITCH_DEMO_AND_JUDGE_QA.md)
22. [22_FINAL_EVALUATION_AND_CHECKLIST.md](file:///d:/ShiVi,/docs/22_FINAL_EVALUATION_AND_CHECKLIST.md)
23. [23_ACCIDENTAL_DATA_LOSS_PREVENTION_POLICY.md](file:///d:/ShiVi,/docs/23_ACCIDENTAL_DATA_LOSS_PREVENTION_POLICY.md)
24. [24_FEDERATED_LAKEHOUSE_CATALOG_ARCHITECTURE.md](file:///d:/ShiVi,/docs/24_FEDERATED_LAKEHOUSE_CATALOG_ARCHITECTURE.md)
25. [25_MOBILE_PERFORMANCE_TIER_OPTIMIZATION.md](file:///d:/ShiVi,/docs/25_MOBILE_PERFORMANCE_TIER_OPTIMIZATION.md)
26. [26_LOAD_BALANCING_DEADLOCK_PREVENTION_AND_LOOP_AVOIDANCE.md](file:///d:/ShiVi,/docs/26_LOAD_BALANCING_DEADLOCK_PREVENTION_AND_LOOP_AVOIDANCE.md)

---

## 📂 Project Structure

```text
ShiVi/
├── apps/
│   ├── core-api/          # FastAPI modular monolith operations backend (9 modules)
│   ├── command-web/       # Next.js 14 Web Command Center (COP, MapLibre, Conflict Console)
│   └── field-mobile/      # Flutter local-first edge client (Drift SQLite outbox, causal sync)
├── packages/
│   └── event-contracts/   # JSON Schema, Pydantic & TypeScript event envelope definitions
├── infrastructure/
│   ├── bicep/             # Azure Infrastructure as Code (Container Apps, PostgreSQL HA, Blob)
│   ├── prometheus/        # Metrics scraping configuration
│   └── dashboards/        # Grafana domain metrics dashboard
├── docs/                  # 29 complete architecture, policy, and engineering specifications
├── scripts/
│   ├── seed_data.py       # Seed tenants, users, responders, and sample alert layers
│   └── simulate_p0_demo.py# End-to-end multi-device concurrency simulation
├── tests/                 # Full automated Pytest suite (sync, conflicts, priority, AI, CAP)
└── docker-compose.yml     # Complete containerized local deployment
```

---

## 📜 Principles & Core Invariants

- **Local-First Durability:** Zero data loss on disconnection or crash.
- **Strict Idempotency:** Duplicate delivery creates exactly one business effect.
- **Zero Silent Overwrites:** Life-safety contradictions demand authorized human review.
- **Responsible AI:** AI advises; authorized humans govern consequential actions.
