# ShiVi: 24-Hour Hackathon Execution Plan

## 1. Hour-by-Hour Milestones & Verification Gates

| Timeframe | Workstream | Primary Deliverables | Verification Gate |
| :--- | :--- | :--- | :--- |
| **00:00 - 03:00** | Contracts & DB Baseline | Event schemas, SQLAlchemy models, SQLite/PostgreSQL configuration. | `pytest tests/test_contracts.py` passes. |
| **03:00 - 07:00** | Core API & Workflow State Machine | Incident CRUD, explainable priority algorithm, task assignment engine. | Endpoints respond with HTTP 200; priority breakdown matches math. |
| **07:00 - 11:00** | Local-First Engine & Outbox Sync | SQLite outbox persistence, push/pull causal sync endpoints, idempotency filters. | Offline crash test passes with 0 data loss. |
| **11:00 - 15:00** | Conflict Engine & Safety Freeze | Auto-merge set logic, protected conflict detection, supervisor adjudication API. | Route 88 conflict freezes tasks and unfreezes on supervisor review. |
| **15:00 - 18:00** | Web Command Center UI | Next.js 14 interactive COP, MapLibre GL styling, conflict review modal. | UI displays live priority queue and conflict alert banner. |
| **18:00 - 21:00** | Evidence, Verification & Audit | SHA-256 binary validation, supervisor sign-off gate, immutable audit ledger. | Task closure is blocked until valid evidence is verified. |
| **21:00 - 24:00** | End-to-End P0 Suite & Pitch Polish | `simulate_p0_demo.py` execution drill, pitch deck finalization, backup video recording. | Complete automated E2E script runs with 100% test pass. |
