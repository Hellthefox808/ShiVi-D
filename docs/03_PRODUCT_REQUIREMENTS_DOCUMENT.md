# ShiVi: Product Requirements Document (PRD)

## 1. Product Identification
- **Product Name:** ShiVi (*Smart Hybrid Intelligent Virtual Integration*)
- **Positioning Statement:** The execution layer for distributed teams operating when connectivity and information cannot be trusted.
- **Target Users:** Disaster response agencies (NDRF, SDRF, DDMA), humanitarian NGOs (Red Cross, SEEDS), community volunteers, and municipal emergency field services.

---

## 2. Core User Personas

### 2.1 Citizen Reporter (Offline Field Contributor)
- **Context:** Stranded or observing an evolving emergency in a zero-connectivity or low-bandwidth zone.
- **Jobs to be Done:**
  - Submit an emergency report in $\le 5$ clicks using voice note, photo, GPS, or simple category selection.
  - Receive an instant offline tracking identifier (Local Reference) confirming local data durability.
  - Seamlessly sync the report when network or bluetooth mesh beacon becomes available.
- **Pain Points:** Complex emergency forms that require multi-step verification or fail when network drops.

### 2.2 Field Responder (Search & Rescue / Relief Squad Lead)
- **Context:** Mobile rescue squad operating in boats, all-terrain vehicles, or on foot in remote flood plains or disaster zones.
- **Jobs to be Done:**
  - Receive, accept, or decline dispatched tasks while disconnected.
  - Transition task lifecycle (`ACCEPTED` $\rightarrow$ `EN_ROUTE` $\rightarrow$ `ON_SITE` $\rightarrow$ `COMPLETED`).
  - Capture real-time route observations (e.g., "Route 88 submerged") and upload cryptographic photo/audio evidence.
- **Pain Points:** Outdated radio instructions dispatching them to roads that are already flooded or missions already handled.

### 2.3 Incident Commander / Supervisor (Command Center)
- **Context:** Coordinating district-level emergency operations from the Emergency Operations Center (EOC) or mobile command vehicle.
- **Jobs to be Done:**
  - Maintain an accurate Common Operational Picture (COP) with real-time geospatial layers and hazard overlays.
  - Review explainable multi-factor incident priority rankings and override recommendations with mandatory justifications.
  - Adjudicate open life-safety conflict cases (e.g., conflicting route status reports).
  - Verify field completion evidence before authorizing incident closure.
- **Pain Points:** Contradictory information, duplicate dispatching of scarce boats/helicopters, and unverified claims of task completion.

### 2.4 System Administrator
- **Context:** IT and disaster management authority administrator managing tenants, sector packs, and audit compliance.
- **Jobs to be Done:**
  - Configure organizational hierarchies, team roles, and region-scoped permissions.
  - Install and customize Sector Packs (e.g., Disaster Response, Epidemic Tracking, Municipal Water Utilities).
  - Review immutable audit ledgers and OpenTelemetry system health metrics.

---

## 3. Scope Boundaries & Requirements

### 3.1 P0 MVP Requirements (Non-Negotiable)
| ID | Requirement Area | Specification |
| :--- | :--- | :--- |
| **P0-01** | Multi-Role Authentication | Role-based JWT authentication for Citizen, Responder, Supervisor, and Admin. |
| **P0-02** | Local-First Offline Durability | SQLite/Drift local outbox; atomic commit of entity, event, and outbox entry surviving app crash. |
| **P0-03** | Causal Delta Sync | Push/pull synchronization using opaque cursor streams and causal version vectors. |
| **P0-04** | Strict Idempotency | Deterministic event deduplication via `(tenant_id, event_id)` preventing duplicate state mutations. |
| **P0-05** | Explainable Incident Priority | Multi-factor deterministic ranking with visible breakdown (Severity, People at Risk, Urgency, Category, Confidence). |
| **P0-06** | Bidirectional Task Machine | State transitions with full field validation and offline capability. |
| **P0-07** | Additive Auto-Merge | Automatic merging of non-conflicting concurrent properties (e.g., multiple notes, photos). |
| **P0-08** | Life-Safety Conflict Detection | Detection of contradictory status updates on protected fields (e.g., Route Safe vs Blocked). |
| **P0-09** | Operational Safety Freeze | Contradicted entities transition to `UNCERTAIN`; dependent task dispatch is automatically blocked. |
| **P0-10** | Human Conflict Adjudication | Supervisor review console with mandatory rationale capture and state rematerialization. |
| **P0-11** | Cryptographic Evidence Gate | Task completion requires valid SHA-256 binary hash, GPS accuracy, and supervisor verification. |
| **P0-12** | Immutable Audit Ledger | Append-only chronological audit log of all decisions, overrides, and state transitions. |
| **P0-13** | Reproducible Deployment | Complete single-command Docker Compose setup. |

### 3.2 P1 (Post-MVP Enhancements)
- Multilingual voice extraction (Hindi, Bengali, Tamil, Telugu, Marathi).
- Offline MapLibre vector tile region packaging.
- Automated duplicate-incident clustering recommendations.
- SMS / Webhook notification dispatch via Azure Service Bus.

### 3.3 Explicit Non-Goals & Exclusions
- Autonomous life-critical dispatch without human authorization.
- Medical diagnosis or automated triage prescription.
- Full peer-to-peer blockchain consensus.
- Black-box AI models directly mutating operational database state.
