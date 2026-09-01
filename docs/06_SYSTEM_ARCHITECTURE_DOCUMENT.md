# ShiVi: System Architecture Document (SAD)

## 1. Architectural Philosophy
ShiVi is architected as an **Offline-First, Causal-Convergent Operational System**. To avoid the fragility of distributed microservice architectures during disaster scenarios, the backend is built as an explicitly bounded **Modular Monolith**, while the field edge consists of autonomous **Local-First SQLite Nodes**.

```
+-------------------------------------------------------------------------------+
|                             Edge Access Boundary                              |
|           Citizen Mobile/PWA  |  Responder Flutter Node  |  Web Command Center |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼ (HTTPS / TLS 1.3 / WSS)
+-------------------------------------------------------------------------------+
|                       API Gateway & Ingestion Boundary                        |
|        JWT Auth  |  Tenant Resolver  |  Rate Limiter  |  Payload Validator   |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|                           ShiVi Modular Monolith                              |
|  ┌──────────────────┬──────────────────┬──────────────────┬────────────────┐  |
|  │ Identity/Tenants │  Incidents & COP │ Tasks/Assignment │   Resources    │  |
|  ├──────────────────┼──────────────────┼──────────────────┼────────────────┤  |
|  │  Causal Sync Engine  │ Conflict Review  │ Evidence Manager │ Verifications  │  |
|  ├──────────────────┼──────────────────┼──────────────────┼────────────────┤  |
|  │ Intelligence GW  │ SACHET/IMD Adapt │ Audit Ledger     │  COP Dashboard │  |
|  └──────────────────┴──────────────────┴──────────────────┴────────────────┘  |
+-------------------------------------------------------------------------------+
                                       │
               ┌───────────────────────┼───────────────────────┐
               ▼                       ▼                       ▼
+-----------------------------+ +----------------+ +---------------------------+
| PostgreSQL 16 + PostGIS     | | Redis 7 Broker | | MinIO / Blob Storage      |
| - Relational Materialized DB| | - Job Queue    | | - Private Evidence Bucket |
| - Immutable Event Log       | | - Sync Cache   | | - SHA-256 Validated Binary|
| - Spatial PostGIS Indexing  | | - Ephemeral Pub| | - Short-Lived Presigned   |
+-----------------------------+ +----------------+ +---------------------------+
```

---

## 2. Component Boundaries & Responsibilities

### 2.1 Field Mobile Node (Flutter + Drift SQLite)
- **Local Materialized Views:** Provides instantaneous UI reads and writes without waiting for network responses.
- **Local Immutable Event Log:** Records every user tap, status transition, and hazard observation as an immutable local event.
- **Transactional Outbox:** Guarantees that mutations, event logs, and pending network jobs commit in a single SQLite transaction.

### 2.2 Operations Core API (FastAPI + SQLAlchemy 2.0 Async)
- **Modular Boundaries:** Cleanly separated Python packages communicating via typed in-memory service interfaces.
- **Transactional Materializer:** Applies incoming operational events to the relational database and evaluates conflict rules within a single database transaction.
- **Transactional Server Outbox:** Writes background jobs (FCM push notifications, AI vector embeddings, webhook deliveries) to a persistent outbox table inside the same commit.

### 2.3 Data Storage & Geospatial Authority (PostgreSQL + PostGIS)
- **Primary Operational State:** Incidents, tasks, assignments, teams, conflict cases, and verification records.
- **Authoritative Spatial Engine:** PostGIS handles spatial indexing (`GIST`), point-in-polygon assignment constraints, and hazard buffer intersections.

### 2.4 Binary Evidence Store (MinIO / Azure Blob Storage)
- **Security Invariant:** Binary files (photos, audio notes) are stored in private object containers. Access is granted exclusively via short-lived presigned URLs after SHA-256 integrity verification.

---

## 3. Database Concurrency & Deadlock Prevention

### 3.1 Strict Canonical Lock Order
Whenever multi-row pessimistic locking (`SELECT ... FOR UPDATE`) is required for transactional reservations or adjudications, locks MUST be acquired in this exact sequence:
$$\text{tenants} \longrightarrow \text{incidents} \longrightarrow \text{tasks} \longrightarrow \text{assignments} \longrightarrow \text{resources (sorted by ID)} \longrightarrow \text{conflict\_cases} \longrightarrow \text{verifications}$$

### 3.2 Non-Blocking Transaction Scope
External network I/O (LLM API calls, Mapbox routing requests, S3 uploads, SMS dispatches) is **strictly forbidden** inside active PostgreSQL transactions.

### 3.3 Automated Serialization Failure Recovery
All critical write operations are wrapped in an asynchronous retry loop with exponential backoff and randomized jitter to transparently handle transient `40P01` (deadlock detected) and `40001` (serialization failure) database errors.
