# ShiVi: Continuous Verified Operational Context Loop Master Specification

> **Positioning:** *"ShiVi is the execution layer for distributed teams operating when connectivity and information cannot be trusted."*  
> **Platform Principle:** Build ShiVi not merely as an AI disaster-management application, but as a resilient operational execution platform.  
> **Core Primitive:** Offline operational state + event-based synchronization + idempotent processing + domain-aware conflict protection + evidence and provenance + human authorization + configurable sector workflows + interoperable integrations.  
> **Governing Axiom:** AI is an accelerator. AI is NOT the authority for safety-critical decisions.

---

## 1. System Mission & Operating Philosophy

ShiVi converts fragmented, unreliable field observations into verified, coordinated, and auditable operational outcomes. The system guarantees trustworthy operational state under extreme failure regimes:
- Complete loss of internet and cellular infrastructure across multi-day horizons.
- Asymmetric, prolonged network partitions with out-of-order and late-arriving mutations.
- Concurrent multi-device edits to the same physical or virtual entity.
- Network duplication and replay attacks.
- Complete outage of third-party external integrations or AI services.
- Object storage and worker process crashes.
- Contradictory, life-safety observations submitted by multiple field responders.

**Non-Negotiable Rule:** The platform never depends on continuous connectivity for field data capture.

---

## 2. The Primary Product Loop: Continuous Verified Context Engine

ShiVi is **not a CRUD application**. It operates as an unbroken, circular **Continuous Verified Context Loop**:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           SHIVI CONTINUOUS VERIFIED CONTEXT LOOP                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│   ┌───────────────┐        ┌───────────────┐        ┌───────────────┐        ┌───────────────┐   │
│   │ 1. SENSE      │ ─────► │ 2. INGEST     │ ─────► │ 3. NORMALIZE  │ ─────► │ 4. VALIDATE   │   │
│   └───────────────┘        └───────────────┘        └───────────────┘        └───────┬───────┘   │
│           ▲                                                                          │           │
│           │                                                                          ▼           │
│   ┌───────┴───────┐        ┌───────────────┐        ┌───────────────┐        ┌───────────────┐   │
│   │14. AUDIT      │ ◄───── │13. RECONCILE  │ ◄───── │12. SYNC       │        │ 5. UNDERSTAND │   │
│   └───────────────┘        └───────────────┘        └───────────────┘        └───────┬───────┘   │
│           ▲                                                 ▲                        │           │
│           │                                                 │                        ▼           │
│   ┌───────┴───────┐        ┌───────────────┐        ┌───────┴───────┐        ┌───────────────┐   │
│   │UPDATED CONTEXT│        │11. VERIFY     │ ◄───── │10. ACT        │        │ 6. ENRICH     │   │
│   └───────────────┘        └───────────────┘        └───────────────┘        └───────┬───────┘   │
│                                     ▲                       ▲                        │           │
│                                     │                       │                        ▼           │
│                                     │               ┌───────┴───────┐        ┌───────────────┐   │
│                                     └────────────── │ 9. AUTHORIZE  │ ◄───── │ 7. PRIORITIZE │   │
│                                                     └───────────────┘        └───────┬───────┘   │
│                                                             ▲                        │           │
│                                                             │                        ▼           │
│                                                             └─────────────── ┌───────────────┐   │
│                                                                              │ 8. PLAN       │   │
│                                                                              └───────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

The output of each phase forms the direct input for the next. Audit and reconciliation continuously feed the next operational context.

---

## 3. Exhaustive 14-Phase Operational Lifecycle

### Phase 1: SENSE (Raw Operational Capture)
- **Purpose:** Capture raw operational reality without network dependence.
- **Inputs:** Official alerts (CAP v1.2), citizen distress SMS/voice, responder field logs, geotagged photographs, GPS NMEA telemetry, river-gauge IoT streams, weather radars.
- **Preservation Invariants:**
  - Separate `occurred_at`, `recorded_at`, and `received_at` timestamps.
  - Distinguish source tiers: `OFFICIAL`, `PARTNER`, `STAFF`, `COMMUNITY`.
  - Capture device hardware UUID, GPS coordinates, and accuracy radius ($\pm \epsilon\text{m}$).
  - Generate globally unique deterministic local reference (`SHV-OBS-<DEVICE>-<SEQ>`).
- **Local Output:** `RawObservation` + `SourceIdentity` + `CaptureContext` + `EvidenceReferences` + `LocalReference`.
- **Field Principle:** Server availability is never required for first capture.

### Phase 2: INGEST (Controlled Trust Boundary Admission)
- **Purpose:** Move captured data across the system trust boundary.
- **Controlled Pipeline:**
  1. Authenticate user/device/partner credentials (Ed25519 signature / OAuth2 token).
  2. Resolve tenant and jurisdictional organization.
  3. Enforce rate limits ($60\text{ req/s}$) and payload caps ($\le 25\text{MB}$ evidence, $\le 64\text{KB}$ metadata).
  4. Verify schema version and reject replay attacks ($\Delta t \le 120\text{s}$, monotonic sequence checks).
  5. Assign correlation ID and OpenTelemetry trace ID.
  6. Commit immutable raw event to ledger.
- **Rule:** A rejected event must never silently disappear; it is stored with error diagnostics in the security audit stream.

### Phase 3: NORMALIZE (Canonical Schema Projection)
- **Purpose:** Standardize heterogeneous data into the canonical ShiVi operational model.
- **Transformations:**
  - Project spatial coordinates to WGS84 (EPSG:4326).
  - Normalize timestamps to ISO-8601 UTC.
  - Detect input language (English, Hindi, Assamese) and preserve raw script.
  - Calculate SHA-256 payload digest.
- **Rule:** Normalize representation; never erase provenance. Original source payloads remain 100% reconstructable.

### Phase 4: VALIDATE (Deterministic Admissibility)
- **Purpose:** Determine structural and operational validity.
- **Checks:** Required fields, data types, value ranges, tenant boundary isolation, role permissions, geographic bounding box clipping, duplicate event suppression.
- **Classification:**
  - `CLASS A: Invalid` (Rejected cleanly).
  - `CLASS B: Incomplete` (Quarantined for missing parameters).
  - `CLASS C: Low Confidence` (Admitted with advisory tag).
  - `CLASS D: Requires Confirmation` (Escalated to supervisor).
  - `CLASS E: Valid` (Eligible for immediate automated pipeline processing).
- **Rule:** Validation is strictly deterministic. AI cannot bypass validation gates.

### Phase 5: UNDERSTAND (Operational Context Assembly)
- **Purpose:** Synthesize disparate validated observations into a live `OperationalContextSnapshot`.
- **Core Entities Combined:**
  $$\text{Context} = \text{Incidents} \cup \text{PeopleAtRisk} \cup \text{HazardPolygons} \cup \text{ActiveTasks} \cup \text{ResourceReservations} \cup \text{Conflicts} \cup \text{TemporalState}$$
- **Operational Answers Provided:**
  - *What is happening?* (Categorized hazard and casualty scale).
  - *Where?* (Geofenced boundaries, impassable routes).
  - *Who reported it?* (Source reliability and credentials).
  - *What is certain vs uncertain?* (Contradictory observations flagged).
  - *What resources exist?* (Available boats, medical personnel, fuel depots).

### Phase 6: ENRICH (Advisory Intelligence Gateway)
- **Purpose:** Provide operational decision-support without corrupting factual ground truth.
- **Capabilities:**
  - Multilingual voice-to-structured entity extraction (Whisper / NER).
  - Incident deduplication and spatial clustering.
  - NDMA Standard Operating Procedure (SOP) retrieval.
  - Route traversal feasibility analysis.
- **Non-Negotiable Boundaries:**
  - AI cannot directly mutate protected state.
  - AI cannot approve safety-critical dispatches.
  - AI cannot override deterministic authorization.
  - AI cannot become a single point of failure (deterministic heuristics execute if AI latencies $> 1500\text{ms}$).
- **Output:** `EnrichedContext` + `Recommendations` + `ConfidenceScores` + `ModelProvenance`.

### Phase 7: PRIORITIZE (Explainable Urgency Calculation)
- **Purpose:** Compute objective operational priority ($P \in [0, 100]$).
- **Formula:**
  $$P = \min\left(100.0, 30 \cdot W_{\text{sev}} + 25 \cdot \text{scale} + 20 \cdot V_{\text{pop}} + 15 \cdot V_{\text{infra}} + 10 \cdot T_{\text{decay}}\right)$$
- **Execution Order:** Hard safety constraints $\to$ Deterministic policy $\to$ Score computation $\to$ Advisory suggestion $\to$ Factor breakdown explanation.
- **Supervisor Override:** A supervisor may override score only with an auditable justification string.

### Phase 8: PLAN (Feasible Response Synthesis)
- **Purpose:** Generate valid, safe response options.
- **Constraints Checked:** Responder skills, availability, active workload, proximity, route passability (avoiding active safety freezes), equipment compatibility.
- **Rule:** Never optimize an unsafe plan. Safety constraints precede optimization.

### Phase 9: AUTHORIZE (Human-Governed Decision Gate)
- **Purpose:** Ensure consequential actions are controlled by legitimate, authenticated human authority.
- **Role Permissions:**
  - `Citizen`: Create observation.
  - `FieldResponder`: Accept/update assigned task, record evidence.
  - `Supervisor`: Assign teams, resolve protected conflicts, verify completion.
  - `Administrator`: Tenant configuration.
- **Rule:** Server-side authorization is mandatory. UI authorization is never trusted alone. AI output is never authorization.

### Phase 10: ACT (Frontline Offline Execution)
- **Purpose:** Execute authorized plans on mobile edge nodes without network connectivity.
- **Atomic Local Transaction:**
  $$\text{Action} \implies \text{BEGIN TRANSACTION} \to \text{EntityState} \to \text{EventEnvelope} \to \text{LocalOutbox} \to \text{COMMIT}$$
- **Result:** State saved offline with ACID durability in Drift SQLite with Write-Ahead Logging.

### Phase 11: VERIFY (Cryptographic Evidence Gate)
- **Purpose:** Confirm that field actions produced real, verifiable outcomes.
- **Verification Criteria:** Geotagged photograph, GPS coordinates within tolerance ($\le 15\text{m}$), responder signature, and supervisor counter-signature.
- **Rule:** "Task marked complete" $\ne$ "Task verified." High-impact tasks require evidentiary verification before status transitions to `CLOSED`.

### Phase 12: SYNC (Causal Delta Convergence)
- **Purpose:** Synchronize local state with central command when connectivity appears.
- **Protocol:**
  - Client pushes batched outbox events with causal vector clocks.
  - Server validates idempotency key ($EventID$).
  - Server commits accepted events and returns opaque cursor.
  - Client updates local outbox records to `SENT`.
- **User States Displayed:** `Saved Offline` $\to$ `Pending Sync` $\to$ `Syncing` $\to$ `Synced` $\to$ `Needs Attention` $\to$ `Conflict`.

### Phase 13: RECONCILE (Domain-Aware Conflict Adjudication)
- **Purpose:** Safely resolve concurrent distributed realities without data loss.
- **Conflict Classes:**
  - **Class A (Compatible Updates):** Device A adds photo; Device B adds note $\implies$ Retain both.
  - **Class B (Deterministic Policy):** Non-overlapping operational metadata $\implies$ Merge via deterministic rules.
  - **Class C (Protected Safety Conflict):** Device A reports `Route = SAFE`; Device B reports `Route = BLOCKED`.
    - **Never use Last-Write-Wins (LWW).**
    - Transition route state to `UNCERTAIN` / `RESTRICTED`.
    - Automatically freeze dependent rescue dispatches.
    - Generate `ConflictCase` with competing claims and evidentiary photos.
    - Require authorized supervisor resolution with mandatory reason log.

### Phase 14: AUDIT (Monotonically Chained Ledger)
- **Purpose:** Make every consequential disaster action legally and operationally reconstructable.
- **Cryptographic Hash Chain:**
  $$H_N = \text{SHA-256}(H_{N-1} \parallel \text{ActorID} \parallel \text{DeviceID} \parallel \text{ActionType} \parallel \text{PayloadHash} \parallel T_N)$$
- **Reconstruction:** Enables complete post-disaster judicial and operational inquiry with zero non-repudiation.

---

## 4. Cross-Cutting Data Model & Entity Boundaries

- **Operational Event:** Immutable historical record of an action or observation.
- **Materialized State:** Current operational state computed from accepted events and authoritative decisions.
- **Conflict Case:** First-class entity containing competing claims, source proofs, status, and supervisor resolution.
- **Protected Field:** Any operational attribute whose contradiction directly impacts life safety (e.g. `route_status`, `shelter_capacity`, `hazard_level`).

---

## 5. Distributed Systems Guarantees & Degradation Model

| Guarantee | Mechanism | Verification Method |
| :--- | :--- | :--- |
| **Zero Field Data Loss** | SQLite Drift WAL + Atomic Outbox | Simulated process kills and low-battery shutdowns |
| **Zero Duplicate Effects** | Canonical $EventID$ Idempotency Gate | 100x replay tests producing 1 business outcome |
| **Zero Silent Overwrites** | Causal Vector Clocks + Safety Freeze | Concurrent conflicting updates escalate to supervisor |
| **Zero Unauthorized Action**| Server-Side Cryptographic RBAC | Unauthorized token injection tests rejected with 403 |
| **Zero Blind AI Automation**| Mandatory Human Authorization Gate | Dispatches blocked until signed by Incident Commander |

---

## 6. The P0 Vertical Demonstration Script (The 23-Step Proof)

The definitive verification that proves ShiVi's architecture under hackathon jury evaluation:

1. Disconnect Field Device A from network (Airplane Mode).
2. Report flash flood distress incident with 5 trapped citizens.
3. Verify state displays `Saved Offline` with Drift WAL durability.
4. Force restart the mobile application.
5. Confirm operational data and outbox queue survive 100% intact.
6. Reconnect Field Device A to network.
7. Observe automatic outbox synchronization to Command Center.
8. Incident Commander views triaged incident on Web COP.
9. System computes deterministic priority score ($85.0/100$).
10. Commander authorizes dispatch and assigns Rescue Team Bravo.
11. Disconnect both Field Device A and Field Device B.
12. Device A reports: `Route-88 = SAFE (Water receded)`.
13. Device B reports: `Route-88 = BLOCKED (Bridge undermined)`.
14. Reconnect both devices simultaneously.
15. Verify compatible updates (timestamps, battery logs) merge cleanly.
16. Verify life-safety contradiction triggers **Automated Safety Freeze**.
17. Route-88 transitions to `RESTRICTED`; all dispatches via Route-88 are paused.
18. Incident Commander opens Conflict Adjudication console.
19. Inspect side-by-side photographic evidence and sensor coordinates.
20. Commander adjudicates: Selects `BLOCKED` with reason: *"Bridge pylon damaged."*
21. Decision commits as authoritative event; alternative detour dispatched.
22. Responder arrives, extracts citizens, and uploads cryptographic photo proof.
23. Supervisor verifies evidence; complete audit timeline is reconstructed.

---

## 7. Master Engineering Principles

1. **Reliable before intelligent.**
2. **Offline before online dependency.**
3. **Deterministic before probabilistic.**
4. **Evidence before assertion.**
5. **Authorization before action.**
6. **Conflict preservation before overwrite.**
7. **Audit before scale.**
8. **Simple architecture before unnecessary complexity.**

**Final Product Statement:** *"ShiVi converts fragmented, unreliable field information into coordinated, synchronized, verified, and auditable action — even when connectivity fails."*
