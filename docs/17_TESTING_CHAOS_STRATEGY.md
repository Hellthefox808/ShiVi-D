# ShiVi: Testing and Chaos-Engineering Strategy

## 1. Automated Test Hierarchy

```text
[Unit Tests (Fast & In-Memory)]
  - State machine transitions, priority calculation, Pydantic event serialization.
           │
           ▼
[Contract & Sync Tests (Async HTTP Client)]
  - Causal delta push/pull, idempotency replay filter, out-of-order event sequence.
           │
           ▼
[Domain Conflict & Safety Tests]
  - Additive auto-merge, protected life-safety contradiction detection, dependency freeze.
           │
           ▼
[End-to-End P0 Simulation (`simulate_p0_demo.py`)]
  - Complete 8-step multi-device disaster scenario with cryptographic evidence verification.
           │
           ▼
[Chaos & Fault-Injection Drills]
  - Sudden process termination during sync, network jitter, PostgreSQL deadlock injection.
```

---

## 2. Chaos Fault-Injection Scenarios

### 2.1 Scenario A: Process Crash During Local Outbox Write
- **Action:** Kill mobile/client process midway through writing an emergency report.
- **Assertion:** SQLite WAL guarantees that either all 3 tables (`incidents`, `operational_events`, `local_outbox`) commit together, or none do. No corrupted partial state exists.

### 2.2 Scenario B: Duplicate Ingestion Storm (Triple Replay)
- **Action:** Deliver 10 identical event batches simultaneously across 3 parallel threads.
- **Assertion:** Server idempotency filter catches 20 duplicates; exactly 10 unique events are inserted into `operational_events`. Zero duplicate side-effects.

### 2.3 Scenario C: PostgreSQL Concurrency Deadlock Recovery
- **Action:** Inject simulated `40P01` (deadlock detected) during simultaneous task assignments.
- **Assertion:** Asynchronous transaction retry decorator automatically retries with jitter and succeeds on attempt 2 without failing the user request.
