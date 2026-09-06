# ShiVi: A Local-First, Conflict-Aware, and Cryptographically Auditable Coordination Architecture for Zero-Connectivity Tactical Disaster Response

**Authors:** Ravi Ranjan Singh, ShiVi Core Systems Architecture Group  
**Affiliation:** Advanced Tactical Edge Distributed Systems & Incident Command Informatics  
**Target Venue:** IEEE Transactions on Mobile Computing / ACM Transactions on Computer Systems (TOCS)  
**Classification:** Distributed Systems, Local-First Software, Delay-Tolerant Networking, Safety-Critical Human-in-the-Loop Systems

---

### Abstract

During catastrophic natural disasters—including cyclones, flash floods, earthquakes, and landslides—the first **72 hours** dictate human survival. However, central telecommunications infrastructure and power grids routinely experience total physical collapse, disabling conventional cloud-centric disaster management platforms. Existing mobile solutions fail critically through three primary failure modes: (1) client-side write freezes during radio silence, (2) destructive data overwrites caused by uncoordinated Last-Write-Wins (LWW) conflict resolution upon network reconnection, and (3) fatal resource deadlocks caused by decoupled physical-vs-virtual asset claims.

We present **ShiVi** (*Smart Hybrid Intelligent Virtual Integration*), an offline-first, safety-critical operational architecture designed specifically for zero-connectivity, high-friction tactical disaster environments. ShiVi introduces a mathematically grounded **8-Phase Operational Lifecycle** (*Capture $\to$ Persist $\to$ Synchronize $\to$ Reconcile $\to$ Protect $\to$ Decide $\to$ Verify $\to$ Audit*) enforced through five non-negotiable system invariants. Key innovations include: (i) an idempotent, causal vector clock reconciliation engine that automatically executes an emergency **Safety Freeze** when conflicting life-safety observations occur; (ii) a **Governed Advisory AI** framework that restricts machine intelligence strictly to advisory triage, transcription, and deduplication while requiring cryptographic human authorization (RBAC) for all consequential dispatches; (iii) an omni-bearer opportunistic mesh synchronization protocol spanning Bluetooth Low Energy (BLE 5.0) GATT framing, Wi-Fi Direct, and ad-hoc cellular/satellite relays; and (iv) an immutable, monotonically chained SHA-256 audit ledger that enables tamper-evident post-incident reconstruction. Empirical benchmarks on commodity edge and server hardware demonstrate sustained backend throughput exceeding **1,180 req/s** on edge health probes, **565 req/s** on in-memory common operational picture aggregations, and sub-second causal conflict escalation with zero data loss across simulated communication partitions.

**Index Terms**—*Local-First Computing, Delay-Tolerant Networking (DTN), Multi-Bearer Mesh Networks, Safety-Critical Systems, Causal Conflict Resolution, Governed AI, Common Operational Picture (COP).*

---

## I. Introduction & Problem Formalization

### A. The 72-Hour Golden Window & The Disaster Edge

In disaster response science, the initial 72 hours following an extreme event are universally recognized as the *Golden Window*. Within this window, the probability of extracting trapped survivors alive decays exponentially. Rapid situational awareness, dynamic route triage, and coordinated multi-agency dispatch (e.g., SDRF, NDRF, medical teams, civic volunteers) are paramount.

However, extreme events inflict severe physical damage on ground telecommunications:
1. **Base Transceiver Station (BTS) Blackouts:** Floods and tremors destroy power feeds and fiber backhauls.
2. **Bandwidth Saturation & Choke Points:** Surviving cells experience massive congestion ($>1000\times$ baseline load).
3. **Severe Asymmetric Partitions:** Responders in deep gorges or flooded sectors remain isolated for hours or days, encountering peer responders intermittently.

```text
                                DISASTER ZONE PARTITION
 ┌─────────────────────────┐               BLE / P2P Mesh              ┌─────────────────────────┐
 │   Sector 4 (Flooded)    │ ◄───────────────────────────────────────► │   Sector 5 (Cut Off)    │
 │   Scout Device Alpha    │                                           │   Medic Device Beta     │
 │   [Local SQLite DB]     │                                           │   [Local SQLite DB]     │
 └───────────┬─────────────┘                                           └────────────┬────────────┘
             │                                                                      │
             │ Offline Outbox                                     Offline Outbox    │
             ▼                                                                      ▼
     ┌───────────────┐                                                      ┌───────────────┐
     │  Supply Boat  │ ◄────── Transits Physical Gap (Physical Mule) ─────► │ Incident Post │
     └───────────────┘                                                      └───────┬───────┘
                                                                                    │ Intermittent
                                                                                    ▼ Satellite Link
                                                                           ┌─────────────────┐
                                                                           │ Central Command │
                                                                           │ FastAPI/PostGIS │
                                                                           └─────────────────┘
```

### B. Formal Failure Modes of Existing Systems

Current emergency management systems (e.g., cloud-hosted WebGIS or standard relational database forms) fail under tactical disaster conditions due to four fundamental design defects:

#### Failure Mode 1: Cloud-First Synchronous Blocking
Standard architectures treat mobile clients as "dumb" viewports. When HTTP POST requests to central endpoints fail during network dropouts, mutations are rejected or stored in volatile memory buffers that evaporate on process crash or battery depletion:
$$\mathbb{P}(\text{Data Loss} \mid \text{Network Partition}) \to 1.0$$

#### Failure Mode 2: Blind Last-Write-Wins (LWW) Semantic Corruption
When offline nodes finally re-establish connectivity, distributed stores typically rely on timestamps to resolve concurrent updates:
$$S_{final} = \arg\max_{t} \{ \text{Timestamp}(U_i) \}$$
Because mobile clocks exhibit severe drift ($\Delta t \ge 120\text{s}$) under physical stress and offline states, an outdated report ("*Bridge 4 Passable*", created at $t=10:15$ on a drifted device) silently overwrites an urgent field report ("*Bridge 4 Collapsed*", created at $t=10:10$ on a true-clock device). Responders guided by this corrupted state are routed directly into disaster hazards.

#### Failure Mode 3: Disconnected Physical Asset Contention
Two rescue teams separated by a hill both locally assign themselves the only remaining motorized inflatable boat ($A_1$). When both teams arrive at the boat cache, a physical deadlock occurs, wasting critical rescue hours.

#### Failure Mode 4: Ungoverned Autonomous AI Hallucination
Unchecked generative AI agents deployed for automated dispatch can hallucinate passable coordinates or invent resource availability based on partial, noisy radio transcripts, dispatching personnel without human supervisory authorization.

---

## II. Related Work & Comparative Analysis

Distributed systems literature offers partial solutions, but none satisfy all disaster-response invariants simultaneously:

1. **Conflict-Free Replicated Data Types (CRDTs):** State-based (CvRDT) and Operation-based (CmRDT) systems (Shapiro et al., 2011) guarantee eventual consistency through monotonic semilattices. However, pure CRDTs cannot resolve *semantic contradictions* where two mutually exclusive real-world facts exist (e.g., $IsBlocked = \text{true} \land IsBlocked = \text{false}$). In disaster operations, convergence must NOT be mathematical averaging; it must escalate to life-safety human triage.
2. **Delay-Tolerant Networking (DTN) & Epidemic Routing:** Vahdat and Becker (2000) established store-and-forward epidemic routing for intermittent networks. While robust for packet delivery, traditional DTN lacks transactional application-layer reconciliation, cryptographic custody proofs, and deterministic priority queuing.
3. **Consensus Protocols (Raft, Paxos):** Consensus algorithms require a strict majority quorum ($Q = \lfloor N/2 \rfloor + 1$). In partitioned disaster networks where $k$ isolated sectors each possess only $10\text{--}20\%$ of nodes, Raft completely halts write availability, violating tactical continuity.

| Architecture Dimension | Legacy Cloud-First WebGIS | Traditional P2P Mesh (DTN) | ShiVi Platform (This Work) |
| :--- | :--- | :--- | :--- |
| **Offline Durability** | Volatile cache / Fail | Local queue / Raw files | **ACID SQLite Outbox (Zero Data Loss)** |
| **Conflict Resolution** | Blind Last-Write-Wins (LWW) | Highest sequence number | **Causal Vector Clock + Automated Safety Freeze** |
| **Multi-Bearer Mesh** | Cellular Only | BLE or Wi-Fi Direct only | **Omni-Bearer: BLE 5.0 + Wi-Fi Direct + Cellular + Sat** |
| **Asset Contention** | Optimistic DB Lock | No contention management | **Physical Possession Priority + Dynamic Substitution** |
| **AI Integration** | None or Autonomous black-box | None | **Governed Advisory AI + Mandatory Human RBAC** |
| **Audit Verification** | Mutable DB update logs | Unsigned text logs | **Cryptographic SHA-256 Hash Chain Ledger** |

---

## III. Mathematical Foundations & System Invariants

ShiVi enforces five fundamental invariants across every layer of the software stack:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SHIVI CORE SYSTEM INVARIANTS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Invariant 1: Local-First Durability                                         │
│   ∀ mutation m: Commit(m, SQLite_local) ≺ Emit(m, Network)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Invariant 2: Omni-Bearer Continuity                                         │
│   SyncEngine(Payload) ≡ Channel(BLE ∪ WiFiDirect ∪ Cellular ∪ Satellite)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Invariant 3: Zero Silent Overwrites & Safety Freeze                         │
│   e₁ ∥ e₂ ∧ Contradicts(e₁, e₂) ⟹ State(Target) ← Freeze(HumanReview)      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Invariant 4: Physical Possession Over Virtual Intent                        │
│   Possession(NFC_Lease) ≻ VirtualClaim(RemoteTask)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Invariant 5: Governed Advisory AI Boundary                                  │
│   DispatchAction = HumanSignature(AI_Advisory, RBAC_Token)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Invariant 1: Local-First Durability (Outbox Monotonicity)
Let $\mathcal{M}$ be the set of state mutations generated at node $N_i$. A mutation $m \in \mathcal{M}$ is defined as a tuple:
$$m = \langle \text{id}, \tau_{local}, \text{entity}, \Delta, \sigma_{sig} \rangle$$
where $\tau_{local}$ is the monotonic local timestamp and $\sigma_{sig} = \text{Sign}_{K_{i}^{-}}(m)$. Under Invariant 1, network transmission is strictly causal to local disk commitment:
$$\text{Commit}(m, \text{SQLite}_{local}) \prec \text{Transmit}(m, \mathcal{N})$$
If node $N_i$ abruptly loses power at time $t$, all mutations $m$ where $\tau_{local} \le t$ reside durably in the write-ahead log (WAL) and are guaranteed to replicate upon restart.

### Invariant 2: Vector Clocks and Causal Precedence
Every node $N_i \in \{1, \dots, K\}$ maintains an internal vector clock $V_i \in \mathbb{N}^K$. Upon generating event $e$, node $N_i$ increments its component:
$$V_i[i] \leftarrow V_i[i] + 1$$
When event $e$ with vector clock $V_e$ is received by node $N_j$, causal precedence is evaluated:
- **Causally Precedes ($e_1 \prec e_2$):** $\forall k, V_{e_1}[k] \le V_{e_2}[k] \land \exists k, V_{e_1}[k] < V_{e_2}[k]$
- **Concurrent ($e_1 \parallel e_2$):** $\neg(e_1 \prec e_2) \land \neg(e_2 \prec e_1)$

### Invariant 3: Causal Conflict Engine & The Safety Freeze Function
When two mutations $e_1$ and $e_2$ targeting entity $X$ are concurrent ($e_1 \parallel e_2$):
$$\Delta_1(X.field) \ne \Delta_2(X.field)$$
ShiVi evaluates the safety criticality of $X.field$:
$$\text{Crit}(X.field) = \begin{cases} 
1 & \text{if } X.field \in \{\text{is\_passable}, \text{hazard\_status}, \text{structural\_integrity}\} \\
0 & \text{otherwise}
\end{cases}$$

If $\text{Crit}(X.field) = 0$ (e.g., responder battery percentage), deterministic union or latest-timestamp merge is executed. If $\text{Crit}(X.field) = 1$, ShiVi halts automated reconciliation and transitions the entity into an immutable **Safety Freeze**:
$$\Sigma_{t+1}(X) \leftarrow \text{FREEZE}\big(X, \text{ConflictCase}(e_1, e_2)\big)$$
All automated tasks dependent on $X$ are frozen immediately. Automated execution remains blocked until an authenticated Incident Commander executes an adjudication decision:
$$\text{Adjudicate}(\text{ConflictID}, \text{ChosenValue}, \text{Rationale}, \text{CommanderSig})$$

### Invariant 4: Physical Possession Priority
Let $A$ be a scarce physical asset (e.g., rescue boat, generator). A virtual claim $C_v$ is an assignment registered in software. A physical possession claim $C_p$ is established by scanning a cryptographic NFC tag bound to the asset:
$$\text{Priority}(C_p) \succ \text{Priority}(C_v)$$
If squad $S_1$ has a virtual dispatch claim $C_v(A)$ but squad $S_2$ physically reaches the asset and asserts $C_p(A)$, the engine revokes $S_1$'s virtual lock, logs an asset contention event, and automatically computes an optimal substitute asset allocation for $S_1$.

### Invariant 5: Governed Advisory AI Boundary
Let $\mathcal{A}_{\text{AI}}$ denote an advisory function computed by a neural network or large language model (e.g., triage classification, audio transcription):
$$\mathcal{A}_{\text{AI}}: \text{RawInput} \to \langle \text{SuggestedPriority}, \text{ExtractedEntities}, \text{RecommendedSOP} \rangle$$
Under Invariant 5, the execution of any consequential operational dispatch action $D$ is governed by a strict guardrail predicate:
$$\text{Execute}(D) \iff \text{ValidatePolicy}(D) \land \text{VerifyRBAC}(\sigma_{\text{human}}, \text{Role}_{\text{Supervisor}})$$
The advisory output cannot invoke backend state mutations without human cryptographic cosignature.

---

## IV. The 8-Phase Operational Lifecycle Architecture

```text
 ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 │ 1. CAPTURE  │ ──► │ 2. PERSIST  │ ──► │   3. SYNC   │ ──► │ 4.RECONCILE │
 │ GPS, Notes, │     │ Atomic ACID │     │ Multi-Bearer│     │ Idempotent  │
 │ Photo Hash  │     │ Outbox (WAL)│     │ BLE/Wi-Fi/4G│     │ Vector Clock│
 └─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
 ┌─────────────┐     ┌─────────────┐     ┌─────────────┐            │
 │  8. AUDIT   │ ◄── │  7. VERIFY  │ ◄── │  6. DECIDE  │ ◄──────────┴────────┐
 │ Reconstruct │     │ Cryptograph.│     │ Supervisor  │  No Conflict: Merge │
 │ Hash Chains │     │ Proof (2-Man)     │ Adjudication│  Conflict: FREEZE   │
 └─────────────┘     └─────────────┘     └─────────────┘                     ▼
                                                                     ┌───────────────┐
                                                                     │  5. PROTECT   │
                                                                     │ Safety Freeze │
                                                                     └───────────────┘
```

The ShiVi platform executes operations across eight formal lifecycle phases:

### Phase 1: Capture
- **Mechanism:** Responders record incident telemetry (GPS lat/lon, altitude, situational category, casualties, voice notes, photos) via the Flutter field client.
- **Priority Algorithm:** Deterministic triage scoring formula:
  $$P = w_c \cdot C_{\text{cat}} + w_s \cdot S_{\text{sev}} + w_p \cdot \min(N_{\text{people}} \cdot 2.5, 25.0)$$
  where weights satisfy $\sum w = 1.0$. Immediate deterministic priority score $P \in [0, 100]$ is computed locally.

### Phase 2: Atomic Persistence
- **Mechanism:** Telemetry is wrapped in a canonical `EventEnvelope` containing `event_id`, `aggregate_id`, `actor_id`, `vector_clock`, and `payload_sha256`.
- **Durability Guarantee:** Written to local SQLite using Drift ORM inside a single atomic transaction. The write-ahead log (WAL) checkpoint guarantees survivability against OS kills.

### Phase 3: Synchronize (Opportunistic Multi-Bearer Mesh)
- **Mechanism:** The background sync orchestrator continuously polls available network bearers in priority order:
  $$\text{Bearer Selection} = \begin{cases}
  \text{Cellular (4G/5G/LTE)} & \text{if internet ping } < 500\text{ms} \\
  \text{Wi-Fi Direct P2P} & \text{if peer SSID detected} \\
  \text{BLE 5.0 Mesh GATT} & \text{if peer BLE beacon active} \\
  \text{Satellite NTN / DTN} & \text{periodic burst schedule}
  \end{cases}$$
- **Epidemic Exchange:** When two responder devices pass within radio range ($10\text{--}80\text{m}$), they exchange Bloom filters representing their local event catalogs and transmit missing event envelopes.

### Phase 4: Reconcile (Idempotency & Vector Clock Validation)
- **Mechanism:** Ingested envelopes pass through an idempotent ingestion filter. Duplicate events (identical `event_id` or identical `(entity_id, sequence_number)`) are acknowledged immediately without re-execution:
  $$\text{Ingest}(e) \equiv \text{NoOp} \quad \forall e \in \text{ProcessedEvents}$$
- Concurrent updates are checked against causal vector clock dependency graphs. Compatible updates (disjoint attribute mutations) are merged automatically.

### Phase 5: Protect (Causal Safety Freeze)
- **Mechanism:** If concurrent reports assert contradictory values on life-safety attributes (e.g., Device 1 reports route `PASSABLE`, Device 2 reports route `BLOCKED`), the engine invokes Invariant 3.
- **Safety Action:** Automatically marks the route `BLOCKED`, locks all downstream tasks dispatched via that route, and broadcasts an audible/haptic alert to field personnel:
  > *"SAFETY FREEZE: Route-88 status contradictory. Dispatched tasks paused pending Commander Adjudication."*

### Phase 6: Decide (Supervisor Adjudication)
- **Mechanism:** The incident commander Web Command Center displays an adjudication card containing side-by-side claim timestamps, scout credentials, GPS coordinates, and aerial drone feeds.
- **Resolution:** The commander selects the authoritative state, enters ground rationales, and signs the adjudication event with their cryptographic private key.

### Phase 7: Verify (Two-Person Rule & Evidence Submission)
- **Mechanism:** Responders completing a rescue or hazard clearance cannot self-resolve an incident with a simple toggle.
- **Cryptographic Evidence Proof:** Responders must upload photographic evidence and GPS coordinates. The client computes:
  $$\text{ProofHash} = \text{SHA-256}(\text{RawImageData} \parallel \text{ExifGPS} \parallel \text{Timestamp})$$
- **Two-Person Verification:** Incident status transitions from `COMPLETED` to `RESOLVED` only after a designated safety supervisor verifies the evidentiary proof.

### Phase 8: Audit (Reconstructable Monotonic Ledger)
- **Mechanism:** Every action—creation, triage, sync, conflict freeze, adjudication, evidence upload, and closure—appends to a tamper-evident audit ledger.
- **Hash Chain Construction:** Each entry $A_N$ stores a cryptographic link to $A_{N-1}$:
  $$H_N = \text{SHA-256}(H_{N-1} \parallel \text{ActionType} \parallel \text{EntityID} \parallel \text{PayloadHash} \parallel T_N)$$
- Any modification to past entries breaks the hash chain, providing verifiable non-repudiation during post-disaster judicial or parliamentary inquiries.

---

## V. Governed Advisory AI Architecture

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                       SHIVI GOVERNED AI ADVISORY GATEWAY                    │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │                                                                             │
 │   Unstructured Distress Audio / Text (Local Radio Transcripts, SMS, Calls)  │
 │                                      │                                      │
 │                                      ▼                                      │
 │   ┌─────────────────────────────────────────────────────────────────────┐   │
 │   │                       ADVISORY AI INFERENCE                         │   │
 │   │  • Multilingual Entity Extraction (Hindi, English, Regional Patois) │   │
 │   │  • Hazard Categorization (Flash Flood, Landslide, Building Collapse)│   │
 │   │  • Casualty Estimation & Geolocation NER Parsing                    │   │
 │   │  • NDMA Standard Operating Procedure (SOP) Protocol Matching        │   │
 │   └──────────────────────────────────┬──────────────────────────────────┘   │
 │                                      │                                      │
 │                                      ▼                                      │
 │                          Candidate Extraction Output                        │
 │                   {people_at_risk: 3, priority_score: 85.0}                 │
 │                                      │                                      │
 │                                      ▼                                      │
 │   ┌─────────────────────────────────────────────────────────────────────┐   │
 │   │                 DETERMINISTIC SAFETY VALIDATION GATE                │   │
 │   │  [Rule 1] Output is strictly ADVISORY; zero auto-dispatch permitted │   │
 │   │  [Rule 2] Confidence score threshold check (Score ≥ 0.70)           │   │
 │   │  [Rule 3] Fallback to regex/keyword rules if LLM offline / timeout  │   │
 │   └──────────────────────────────────┬──────────────────────────────────┘   │
 │                                      │                                      │
 │                                      ▼                                      │
 │   ┌─────────────────────────────────────────────────────────────────────┐   │
 │   │                MANDATORY HUMAN AUTHORIZATION (RBAC)                 │   │
 │   │  Incident Commander reviews parsed advisory & signs with Ed25519    │   │
 │   └──────────────────────────────────┬──────────────────────────────────┘   │
 │                                      │                                      │
 │                                      ▼                                      │
 │                      Authorized Operational Dispatch                        │
 └─────────────────────────────────────────────────────────────────────────────┘
```

ShiVi implements a strict hybrid intelligence model. AI models (e.g., Whisper for on-device voice transcription, quantized LLMs / Regex pipelines for Named Entity Recognition) operate with zero administrative authority:

1. **Entity Extraction:** Extracts incident category, casualty count, trapped individuals, and landmark-relative spatial indicators from unstructured text:
   $$\mathcal{E}: \text{"3 people stuck on roof near shiva temple flooded"} \to \begin{cases} 
   \text{category: RESCUE} \\
   \text{people: 3} \\
   \text{landmark: "shiva temple"}
   \end{cases}$$
2. **Deterministic Fallback:** If inference exceeds a $1500\text{ms}$ timeout or model weights are uninitialized, execution cascades instantly to deterministic keyword-rule scoring, ensuring zero pipeline stalls.
3. **NDMA SOP Recommendation:** Suggests pre-approved National Disaster Management Authority (NDMA) tactical protocols (e.g., deployment of motorized inflatable boats with 4-person rescue teams, life jackets, dry rations).
4. **Mandatory Human Cosignature:** Suggestions populate a supervisory draft. Only upon explicit commander click and cryptographic token verification is the task dispatched.

---

## VI. Multi-Bearer Mesh Architecture & Packet Framing

### A. BLE 5.0 GATT Fragmentation and Framing

To support BLE 5.0 GATT connections with limited Maximum Transmission Units ($\text{MTU} \approx 512\text{ bytes}$), ShiVi implements an adaptive fragmentation and reassembly layer:

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Magic (0x5356)       |          Packet ID            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Chunk Index           |         Total Chunks          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Payload Length          |            Reserved           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                   Fragmented Payload (≤ 496 B)                |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           CRC32                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **Loop Avoidance:** Each packet carries a bitmask and 16-bit monotonic hop counter. Nodes decrement TTL ($TTL_{default} = 7$) and discard packets with previously seen hash signatures within a $3600\text{s}$ sliding bloom filter window.
- **Priority Fair Queuing:** Event envelopes are transmitted in priority order: $P0 \text{ (Safety Freezes / Distress)} \succ P1 \text{ (Task Updates)} \succ P2 \text{ (Telemetry / Heartbeats)} \succ P3 \text{ (Media Chunks)}$.

### B. Satellite-Constrained Burst Protocol (140-Byte SBD Framing) & Citizen Emergency SMS Gateway

When terrestrial towers and ad-hoc VHF/UHF repeaters suffer catastrophic failure, field nodes fall back to two highly bandwidth-constrained channels: satellite transceivers (Garmin inReach, Iridium Short Burst Data (SBD), C-DOT terminals) and surviving cellular 2G/GSM SMS links.

#### 1. Compact 140-Byte Satellite Burst Framing
Satellite Short Burst Data services impose rigid Maximum Transmission Unit limits ($\text{MTU} \le 140\text{ bytes}$ or 340 bytes) where per-byte transmission costs and transmission latencies are severe. ShiVi specifies a colon-delimited ASCII micro-framing protocol:

$$\text{Packet} = \texttt{"SHV:1:"} \parallel \text{EvtID} \parallel \texttt{":"} \parallel \text{Cat} \parallel \texttt{":"} \parallel \text{Sev} \parallel \texttt{":"} \parallel \text{People} \parallel \texttt{":"} \parallel \text{Lat} \parallel \texttt{","} \parallel \text{Lon} \parallel \texttt{":"} \parallel \text{Desc} \parallel \texttt{":"} \parallel \text{CRC32}$$

```text
 0                                                          139 Bytes Max
┌───────┬───┬──────────────┬─────┬─────┬───┬─────────────┬───────────┬────────┐
│ "SHV" │ 1 │ Event ID (8) │ Cat │ Sev │ P │ Lat,Lon(17) │ Desc (48) │ CRC-32 │
└───────┴───┴──────────────┴─────┴─────┴───┴─────────────┴───────────┴────────┘
```

- **Efficiency:** A complete life-safety distress event compresses into $55\text{--}85\text{ bytes}$, leaving ample headroom under the 140-byte hardware ceiling.
- **Integrity Verification:** Field receivers and central gateways calculate the 32-bit IEEE 802.3 polynomial ($0xEDB88320$) over the micro-frame before accepting or decoding. Any frame corruption induced by atmospheric fading or orbital satellite doppler shifts is rejected immediately ($\text{CRCError}$).

#### 2. Multilingual Citizen Distress SMS Ingestion
Unconnected citizens in disaster perimeters submit unstructured distress SMS messages in English, Hindi (Devanagari), or regional dialects (e.g., Assamese):
$$\mathcal{M} = \texttt{"बाढ़ में 3 लोग छत पर फंसे हैं सेक्टर 4 मदद भेजो"}$$

The Ingestion Engine executes:
1. **Named Entity Recognition & Coordinate Resolution:** Maps sector landmarks (`"सेक्टर 4"`, `"दिसपुर"`, `"गुवाहाटी"`) to geographic bounding polygons.
2. **Casualty Scale Extraction:** Parses numerical digits and Devanagari numerals to extract trapped populations ($\text{people} = 3$).
3. **Deterministic Urgency Scoring:** Evaluates hazard vocabulary against the explainable priority function:
   $$P = \min(100.0, 30 \cdot W_{sev} + 25 \cdot \text{scale} + 20 \cdot V_{pop} + 15 \cdot V_{infra})$$
4. **Automated Life-Safety Reply Dispatch:** Generates immediate SMS acknowledgment advising survival protocol while providing tracking reference:
   $$\mathcal{R} = \texttt{"SHIVI ALERT: SOS SMS-REF-3829 logged. Priority: CRITICAL (90.0/100). Responders alerted. Remain on high ground."}$$

#### 3. Geo-Targeted 160-Character Cell Alert Broadcasting
Command center operators broadcast sector-wide evacuation warnings. To prevent message fragmentation into multiple billable or congested SMS segments, the broadcast engine dynamically clamps payloads to the standard GSM $160\text{-character}$ boundary:
$$\text{len}(\mathcal{B}) \le 160 \implies \mathbb{P}(\text{Multi-Part Drop} \mid \text{Congested BTS}) \to 0$$

## VII. Empirical Evaluation & Performance Benchmarks

Empirical performance evaluation was conducted on commodity hardware:
- **Server:** Intel Core i7-13700H, 32 GB DDR5 RAM, NVMe SSD, Python 3.11 / FastAPI with Uvicorn ASGI workers.
- **Edge Devices:** Android 13 / 14 mobile devices running Flutter 3.x and SQLite 3.42 via Drift.

### A. Throughput and Latency Micro-Benchmarks

Benchmarking was performed using `backend/scripts/benchmark.py` under concurrent request loads ($\text{Concurrency} = 10$, $\text{Requests} = 100$ per endpoint):

| Target Endpoint | Method | Throughput (req/s) | Mean Latency | Median (P50) | P95 Latency | Evaluation Metric |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `/health` | `GET` | **1,186.40** | 0.83 ms | 0.56 ms | 1.83 ms | Micro-health edge heartbeat |
| `/v1/dashboard/summary` | `GET` | **565.89** | 15.39 ms | 8.50 ms | 46.12 ms | In-Memory IOC Cached Metric Aggregation |
| `/v1/dashboard/geojson` | `GET` | **402.34** | 23.56 ms | 24.27 ms | 31.89 ms | PostGIS Spatial Polygon Clipping |
| `/v1/demo/simulate-workflow`| `POST` | **33.71** | 57.21 ms | 29.26 ms | 129.56 ms | Complete 9-step cryptographic loop |

```text
Throughput Comparison (Requests / Second)
─────────────────────────────────────────────────────────────────────────────
/health                   ████████████████████████████████████ 1,186.40 req/s
/v1/dashboard/summary     █████████████████ 565.89 req/s
/v1/dashboard/geojson     ████████████ 402.34 req/s
/v1/demo/simulate-workflow █ 33.71 req/s (9-step transactional cryptographic loop)
─────────────────────────────────────────────────────────────────────────────
```

### B. Scalability & Partition Recovery

During stress tests simulating a **6-hour complete radio blackout** involving 50 field responder devices and 1,200 accumulated outbox mutations:
- **Zero Data Loss:** 100% of outbox events ($1,200 / 1,200$) successfully synchronized upon physical rendezvous with a central mobile gateway.
- **Conflict Freezes:** 14 concurrent route contradictions were automatically detected and converted into Safety Freezes within $42\text{ms}$ of packet ingestion. Zero silent overwrites occurred.
- **Audit Chain Integrity:** Ledger validation script traversed 1,200 sequential blocks, confirming 100% cryptographic continuity.

---

## VIII. Threat Model, Cryptographic Identity & Tamper-Evident Ledgers

ShiVi is evaluated against the **STRIDE** threat model:

1. **Spoofing:** Responders are provisioned with asymmetric Ed25519 keypairs stored in Android Keystore / iOS Secure Enclave. All event envelopes are signed at creation. Unsigned or invalidly signed packets are rejected at the ingestion gate.
2. **Tampering:** Payloads carry SHA-256 digests verified at each hop. Hash chain $H_N = \text{SHA-256}(H_{N-1} \parallel e_N)$ ensures retroactive tampering is mathematically impossible without invalidating all subsequent signatures.
3. **Repudiation:** Dual-signature verification (Field Responder + Incident Commander) creates non-repudiable proof of action.
4. **Information Disclosure:** Peer-to-peer mesh transfers use ChaCha20-Poly1305 authenticated symmetric encryption derived from pre-shared tactical operational keys.
5. **Denial of Service:** Monotonic sequence numbers and vector clocks eliminate packet replay attacks. Devices maintain an anti-replay sliding window filter.
6. **Elevation of Privilege:** Role-Based Access Control (RBAC) capabilities (`Citizen`, `FieldResponder`, `TeamLead`, `IncidentCommander`, `Auditor`) are embedded into cryptographic claims and strictly enforced by API dependencies.

---

## IX. Conclusion & Future Work

ShiVi establishes a new operational paradigm for tactical emergency response software. By rejecting the fragility of cloud-first assumptions and the hazards of blind Last-Write-Wins synchronization, ShiVi proves that disaster platforms can achieve **zero data loss**, **causal safety protection**, and **cryptographic accountability** simultaneously.

Future work includes integrating satellite non-terrestrial networks (3GPP Rel-17 NTN direct-to-cell), compiling the causal conflict engine to WebAssembly for edge execution on low-power IoT microcontrollers, and deploying district-scale multi-agency pilot trials across cyclone-prone coastal corridors.

---

## References

1. **Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M.** (2011). Conflict-free replicated data types. *Symposium on Self-Stabilizing Systems (SSS)*, Springer, 386–400.
2. **Vahdat, A., & Becker, D.** (2000). Epidemic routing for partially connected ad hoc networks. *Technical Report CS-200006*, Duke University.
3. **Lamport, L.** (1978). Time, clocks, and the ordering of events in a distributed system. *Communications of the ACM*, 21(7), 558–565.
4. **National Disaster Management Authority (NDMA).** (2019). *National Disaster Management Plan*. Government of India.
5. **Fall, K.** (2003). A delay-tolerant network architecture for challenged internets. *ACM SIGCOMM Computer Communication Review*, 33(4), 27–34.
6. **Kleppmann, M., & Beresford, A. R.** (2017). A conflict-free replicated JSON datatype. *IEEE Transactions on Parallel and Distributed Systems*, 28(10), 2733–2746.
7. **Bernstein, P. A., Hadzilacos, V., & Goodman, N.** (1987). *Concurrency Control and Recovery in Database Systems*. Addison-Wesley.
