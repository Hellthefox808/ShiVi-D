---
name: shivi-disaster-workflow
description: >-
  Executes, verifies, and audits the ShiVi 8-Phase Disaster Coordination Operational Lifecycle (Capture, Persist, Synchronize, Reconcile, Protect, Decide, Verify, Audit). Use when validating offline outbox sync, causal safety freezes, supervisor adjudication, or performance benchmarking on the ShiVi platform.
---

# ShiVi Disaster Workflow: 8-Phase Operational Lifecycle & Verification

## Overview
This skill provides automated orchestration, diagnostic validation, and empirical auditing for the **ShiVi** (*Smart Hybrid Intelligent Virtual Integration*) offline-first disaster response coordination platform. It enforces the 5 core system invariants across the 8 operational phases.

## Dependencies
- `python` 3.11+
- `httpx` or `urllib` for API interaction
- Running ShiVi backend on `http://localhost:8000` (or standalone in-memory mode)

## Quick Start

```bash
# 1. Execute full 8-phase operational lifecycle simulation
python .agents/skills/shivi-disaster-workflow/scripts/verify_workflow.py simulate --output results.json

# 2. Benchmark backend throughput and latency metrics
python .agents/skills/shivi-disaster-workflow/scripts/verify_workflow.py benchmark --output benchmark.json

# 3. Verify cryptographic integrity of the immutable audit chain
python .agents/skills/shivi-disaster-workflow/scripts/verify_workflow.py audit --output audit_check.json
```

## Utility Scripts (CLI-Based)

The helper script `verify_workflow.py` provides multi-command CLI automation with strict rate limits and JSON file output:

### Subcommands

1. **`simulate`**:
   - Executes the complete 8-phase workflow against the running backend (`POST /v1/demo/simulate-workflow`).
   - Verifies:
     - Phase 1: Local incident recording & priority scoring.
     - Phase 2: Atomic outbox commit.
     - Phase 3: Omni-bearer vector clock ingestion.
     - Phase 4: Idempotent deduplication.
     - Phase 5: Automated Safety Freeze on route contradiction.
     - Phase 6: Human Incident Commander adjudication.
     - Phase 7: Cryptographic SHA-256 evidence verification.
     - Phase 8: Immutable audit ledger reconstruction.
   - Example:
     ```bash
     python .agents/skills/shivi-disaster-workflow/scripts/verify_workflow.py simulate --output /tmp/shivi_sim.json
     ```

2. **`benchmark`**:
   - Measures requests/sec and latency distributions (P50, P95) across `/health`, `/v1/dashboard/summary`, and `/v1/demo/simulate-workflow`.
   - Example:
     ```bash
     python .agents/skills/shivi-disaster-workflow/scripts/verify_workflow.py benchmark --concurrency 10 --limit 50 --output /tmp/bench.json
     ```

3. **`health`**:
   - Probes edge liveness and fetches the Inversion of Control (IOC) summary metrics.
   - Example:
     ```bash
     python .agents/skills/shivi-disaster-workflow/scripts/verify_workflow.py health --output /tmp/health.json
     ```

4. **`audit`**:
   - Reads the latest audit chain records and mathematically verifies that $H_N = \text{SHA-256}(H_{N-1} \parallel \dots)$ holds for every record.
   - Example:
     ```bash
     python .agents/skills/shivi-disaster-workflow/scripts/verify_workflow.py audit --limit 100 --output /tmp/audit_validation.json
     ```

## Workflow: 8-Phase Operational Lifecycle

When manually inspecting or testing a deployment:

1. **Verify Outbox Durability (Capture & Persist):**
   - Confirm that mutations commit to local SQLite with WAL mode before network transmission.
2. **Test Multi-Bearer Mesh Synchronizer:**
   - Confirm packets are framed into $\le 496$-byte fragments for BLE 5.0 GATT MTU constraints.
3. **Trigger Causal Conflict Protection:**
   - Post two concurrent updates asserting opposing route conditions (`USABLE` vs `BLOCKED`).
   - Verify that status immediately transitions to `SAFETY_FREEZE` and dependent tasks are locked.
4. **Execute Supervisor Decision & Evidence Verification:**
   - Submit commander adjudication token; confirm task unlocks and re-routes.
   - Submit completion proof with SHA-256 photo digest; verify supervisor approval transitions state to `RESOLVED`.
5. **Verify Monotonic Audit Ledger:**
   - Confirm all 8 lifecycle events appear in sequential cryptographic order.

## Rate Limiting & Error Handling

- All requests enforce a 10 req/s local burst limiter with exponential backoff on HTTP 429 / 5xx.
- In case of API downtime, the CLI script automatically detects local SQLite fallback.

## Common Mistakes

1. **Bypassing the Safety Freeze:** Never attempt to resolve a life-safety route contradiction automatically via Last-Write-Wins (LWW). It MUST be adjudicated by an authenticated supervisor.
2. **Missing Outbox Persistence:** Never transmit a mutation over BLE or cellular without first confirming SQLite ACID commit.
3. **Self-Closure Without Evidence:** Responders cannot close tasks without submitting geofenced photographic proof and receiving two-person verification.
