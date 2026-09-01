# ShiVi: 14-Phase Continuous Context Loop Specification

## 1. Overview
ShiVi models operational decision-making as an unbroken, continuous, and verified **Context Loop**. Rather than treating features as isolated silos, every piece of information flows through a 14-phase pipeline that transforms raw field observations into prioritized, assigned, evidence-backed, and auditable outcomes.

```text
[Phase 1: SENSE] ──────> [Phase 2: INGEST] ──────> [Phase 3: NORMALIZE] ──────> [Phase 4: VALIDATE]
                                                                                        │
[Phase 8: PLAN]  <────── [Phase 7: PRIORITIZE] <── [Phase 6: ENRICH] <───────── [Phase 5: UNDERSTAND]
       │
       ▼
[Phase 9: AUTHORIZE] ──> [Phase 10: ACT] ────────> [Phase 11: VERIFY] ────────> [Phase 12: SYNC]
                                                                                        │
                                                   [Phase 14: LEARN] <────────── [Phase 13: RESOLVE CONFLICT]
```

---

## 2. Phase-by-Phase Specification

### Phase 1: SENSE (Raw Operational Capture)
- **Objective:** Capture raw field observations under any connectivity state.
- **Inputs:** Official CAP warnings, citizen text/voice, photo binaries, GPS coordinates, responder field notes, IoT river-gauge telemetry.
- **Invariants:** Capture hardware timestamp, network timestamp, location accuracy radius, actor ID, and device ID. Always preserve raw input without premature lossy parsing.

### Phase 2: INGEST (Trust Boundary Admission)
- **Objective:** Securely admit data through tenant-isolated API gateway.
- **Operations:** JWT token validation, device revocation check, payload size limit enforcement ($\le 10\text{MB}$ metadata, chunked binary streams), cryptographic SHA-256 hash assignment.
- **Failure Handling:** Immediate rejection of unauthenticated or tampered payloads with security audit logging.

### Phase 3: NORMALIZE (Canonical Schema Mapping)
- **Objective:** Standardize heterogeneous data into ShiVi canonical models.
- **Operations:** Convert local timestamps to ISO-8601 UTC, project spatial coordinates to WGS84 (EPSG:4326), map local category terms to sector pack taxonomy.

### Phase 4: VALIDATE (Operational Admissibility)
- **Objective:** Determine if the normalized observation is structurally and operationally valid.
- **Operations:** Schema verification, spatial bounding box checks against district boundaries, role permission checks, duplicate report detection.
- **Classification:** Valid (Auto-process), Valid (Confirmation required), or Rejected (Invalid schema).

### Phase 5: UNDERSTAND (Operational Context Assembly)
- **Objective:** Construct a unified `OperationalContextSnapshot`.
- **Composition:** Combine incident history + people at risk + active hazard polygons (NDEM) + squad locations + available resources + active conflict cases.

### Phase 6: ENRICH (Non-Blocking Hybrid Intelligence)
- **Objective:** Augment context with advisory AI without corrupting underlying facts.
- **Operations:** Multilingual voice-to-text transcription, translation to English/Hindi, duplicate incident similarity clustering, relevant SOP retrieval from authorized manuals.
- **Invariant:** AI predictions are purely advisory; AI NEVER mutates protected state directly.

### Phase 7: PRIORITIZE (Explainable Multi-Factor Ranking)
- **Objective:** Compute transparent, deterministic priority scores ($0 - 100$).
- **Algorithm:** Weighted sum of Severity, People at Risk, Urgency, Category Vulnerability, and Evidence Confidence.
- **Output:** Numerical score with full breakdown vector visible on the command dashboard.

### Phase 8: PLAN (Feasible Response Synthesis)
- **Objective:** Synthesize eligible response options for the Incident Commander.
- **Filters:** Exclude responders lacking required skills/equipment; exclude routes under active conflict freeze (`is_route_blocked == TRUE`); rank eligible teams by estimated arrival time and current workload.

### Phase 9: AUTHORIZE (Human-Governed Decision Gate)
- **Objective:** Guarantee that consequential decisions are authorized by permitted humans.
- **Mandatory Gates:** Task assignment approval, resource preemption, life-safety conflict adjudication, incident closure. Every human override requires a logged reason string.

### Phase 10: ACT (Field Execution & State Transitions)
- **Objective:** Convert authorized decisions into field task assignments.
- **Workflow:** Task transitions through `OFFERED` $\rightarrow$ `ACCEPTED` $\rightarrow$ `EN_ROUTE` $\rightarrow$ `ON_SITE` $\rightarrow$ `COMPLETED`. Real-time progress is staged in the local SQLite outbox.

### Phase 11: VERIFY (Cryptographic Evidence Gate)
- **Objective:** Prove that claimed field action produced the intended outcome.
- **Validation:** Photo/audio evidence SHA-256 checksum verification, GPS location proximity check, beneficiary count verification, and supervisor sign-off.

### Phase 12: SYNC (Causal Delta Convergence)
- **Objective:** Converge distributed replicas across intermittent networks.
- **Protocol:** Bounded batch push/pull using causal version vectors, opaque server cursors, and transactional idempotency filters.

### Phase 13: RESOLVE CONFLICT (Domain-Aware Concurrency Safety)
- **Objective:** Adjudicate concurrent multi-device updates safely.
- **Protocol:** Auto-merge additive properties (notes, photos); apply deterministic domain state rules; freeze protected life-safety contradictions in `UNCERTAIN` state for mandatory supervisor review.

### Phase 14: LEARN (Governed Platform Improvement)
- **Objective:** Continually improve operational templates, response heuristics, and dispatch algorithms based on post-incident audit reviews and supervisor override logs.
