# ShiVi: Technical Requirements Document (TRD)

## 1. Technology Portfolio & Version Standards

| Tier | Component | Technology Selected | Version | Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Mobile Client** | Framework | Flutter (Dart) | 3.22+ | Native compilation for Android/iOS, cross-platform performance, MapLibre mobile support. |
| | Local Database | Drift + SQLite | 2.18+ | Type-safe reactive SQLite queries, transaction support, embedded outbox capability. |
| | State Management | Riverpod | 2.5+ | Compile-time safe dependency injection, robust async state caching. |
| **Command Web** | Framework | Next.js (App Router) | 14.2+ | React Server Components, server-side rendering for accessible EOC dashboards. |
| | Styling & UI | Tailwind CSS | 3.4+ | High-contrast emergency dark/light themes, responsive layout engine. |
| | Maps | MapLibre GL JS | 4.1+ | Open-source vector tile rendering, offline style packaging, custom WebGL layers. |
| | Server State | TanStack Query | 5.3+ | Cache invalidation, optimistic UI updates, real-time polling/SSE sync. |
| **Backend API** | Runtime | Python | 3.11+ | High-performance asynchronous runtime, extensive geospatial and ML ecosystem. |
| | Framework | FastAPI | 0.110+ | Asynchronous ASGI framework, automated OpenAPI/JSON Schema generation. |
| | ORM & Validation | SQLAlchemy 2 + Pydantic v2 | 2.0+ / 2.6+ | Type-safe async queries, strict validation, sub-millisecond serialization. |
| **Data Platform** | Primary Database | PostgreSQL + PostGIS | 16-3.4 | Authoritative transactional consistency and industry-standard spatial queries. |
| | Cache & Queue | Redis | 7.2+ | In-memory sync cursor tracking, rate limiting, and worker queue broker. |
| | Object Store | MinIO / Azure Blob | Latest | S3-compatible private binary storage for cryptographic evidence attachments. |

---

## 2. Offline Synchronization Technical Rules

- **TR-S01 (Atomic Local Commit):** Every mobile mutation MUST execute in a single SQLite transaction:
  ```sql
  BEGIN TRANSACTION;
    UPDATE materialized_tasks SET status = 'COMPLETED' WHERE id = 'task-01';
    INSERT INTO local_event_log VALUES ('evt-01', 'TASK_COMPLETED', ...);
    INSERT INTO local_outbox VALUES ('outbox-01', 'evt-01', 'PENDING');
  COMMIT;
  ```
- **TR-S02 (Deterministic Event Identity):** Event IDs are generated on the client as globally unique ULIDs or UUIDs containing timestamp prefixes.
- **TR-S03 (Server Idempotency):** The backend enforces uniqueness on `(tenant_id, event_id)`. Re-received events immediately return the cached acknowledgment (`HTTP 200 OK`) without re-applying business logic.
- **TR-S04 (Causal Vector Tracking):** Events carry a `version_vector` dictionary mapping device IDs to monotonic sequence numbers: `{"device-A": 12, "device-B": 5}`.
- **TR-S05 (Media Decoupling):** Critical structured event payloads ($\le 5\text{KB}$) synchronize immediately; large binary evidence (photos/audio $\ge 1\text{MB}$) is staged in background workmanager queues.
