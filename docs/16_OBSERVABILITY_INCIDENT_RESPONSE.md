# ShiVi: Observability and Incident-Response Plan

## 1. Domain Metric Families (Prometheus / OpenTelemetry)

### 1.1 Synchronization Metrics
- `shivi_sync_events_pending`: Gauge tracking total unprocessed events in client outboxes.
- `shivi_sync_batch_latency_ms`: Histogram tracking end-to-end sync batch processing duration (p50, p95, p99).
- `shivi_sync_event_duplicates_total`: Counter of duplicate events absorbed by the idempotency filter.
- `shivi_sync_events_rejected_total`: Counter of events rejected due to schema or authorization violations.

### 1.2 Conflict & Life-Safety Metrics
- `shivi_conflicts_open_total`: Gauge tracking active unresolved conflict cases.
- `shivi_conflict_age_seconds`: Histogram tracking duration from conflict detection to supervisor resolution.
- `shivi_conflict_frozen_dependencies`: Gauge tracking total operational tasks halted by conflict freezes.

### 1.3 Operational Workflow Metrics
- `shivi_report_to_assignment_seconds`: Duration from incident ingestion to responder assignment.
- `shivi_verified_completion_ratio`: Percentage of completed tasks with validated cryptographic evidence.

---

## 2. Alert Thresholds & Severity Triage

| Alert Name | Condition | Severity | Notification Channel |
| :--- | :--- | :--- | :--- |
| **`LifeSafetyConflictOpen`** | `shivi_conflicts_open_total > 0` for $> 2\text{ min}$ | **P1 - CRITICAL** | Flashing EOC Header + PagerDuty to Commander |
| **`SyncBatchLatencyHigh`** | `p95(shivi_sync_batch_latency_ms) > 2000` for $> 5\text{ min}$ | **P2 - WARNING** | Slack/Teams Platform Channel |
| **`DatabaseDeadlockSpike`** | `rate(shivi_db_deadlocks_total[5m]) > 0.05` | **P2 - WARNING** | Engineering Operations Alert |
| **`EvidenceIntegrityMismatch`**| `shivi_evidence_integrity_failures_total > 0` | **P1 - CRITICAL** | Security Audit Alert |
