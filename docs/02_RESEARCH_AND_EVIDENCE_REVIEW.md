# ShiVi: Research and Evidence Review

## 1. Official Warning Ecosystems: NDMA SACHET and CAP

### 1.1 The Common Alerting Protocol (CAP) Standard
- **Standard Reference:** ITU-T Recommendation X.1303 / OASIS CAP v1.2.
- **Role in India:** The National Disaster Management Authority (NDMA) operates the **SACHET** (National Disaster Alert Portal - `sachet.ndma.gov.in`). SACHET aggregates multi-hazard warnings from India Meteorological Department (IMD), Central Water Commission (CWC), Indian National Centre for Ocean Information Services (INCOIS), Defence Geoinformatics Research Establishment (DGRE), and Forest Survey of India (FSI).
- **Protocol Schema:**
  - Standard elements: `<identifier>`, `<sender>`, `<sent>`, `<status>`, `<msgType>`, `<scope>`, `<info>` (containing `<category>`, `<event>`, `<urgency>`, `<severity>`, `<certainty>`, `<headline>`, `<description>`, `<instruction>`, and `<area>` polygons/circles).
- **ShiVi Integration Boundary:**
  - ShiVi operates as an **operational execution consumer**, not a competing public alert broadcaster.
  - Ingests authorized CAP XML/JSON feeds via webhook or polling gateway.
  - Computes spatial intersection of `<area>` polygons with active district responder units.
  - Converts official alert into operational readiness workflows (e.g., proactive shelter preparation, floodgate monitoring).
  - Preserves raw payload hash (`sha256`), issuing authority signatures, and exact verbatim instructions.

---

## 2. Geospatial Ecosystems: NDEM & PostGIS

### 2.1 National Database for Emergency Management (NDEM)
- **Authority:** National Remote Sensing Centre (NRSC) / Indian Space Research Organisation (ISRO) (`ndem.nrsc.gov.in`).
- **Data Layers:** Satellite-derived flood extent maps, landslide zonation, cyclone track forecasts, administrative ward boundaries, and critical infrastructure (hospitals, shelters, helipads).
- **ShiVi Integration Boundary:**
  - ShiVi consumes authorized GIS vector and raster overlays from NDEM.
  - Uses PostGIS spatial engine to execute spatial containment checks:
    - Point-in-polygon queries for responder dispatch.
    - Hazard-zone intersection for routing restrictions.
    - Safe corridor calculation around active flood inundation contours.

---

## 3. Connectivity Realities & Offline Distributed Systems

### 3.1 Field Telecommunications Failure Modes
- Disasters (e.g., Cyclone Biparjoy 2023, Wayanad Landslides 2024, Chennai Floods 2023) regularly cause severe telecommunication outages:
  - Fiber backhaul severance due to uprooted trees and road washouts.
  - Base Transceiver Station (BTS) tower power loss.
  - Cellular spectrum congestion from mass public calls.
- **Why Standard CRUD Mobile Apps Fail:**
  - Traditional web and mobile apps rely on synchronous REST/GraphQL calls. When the connection drops, in-flight HTTP requests time out, causing data loss, partial updates, and silent overwrites upon reconnect.
- **The ShiVi Solution:**
  - **Local-First Architecture:** All mutations commit locally to an embedded SQLite database before any network request is attempted.
  - **Causal Version Vectors:** Devices maintain monotonic sequence counters and causal version vectors to detect concurrent edits without relying on wall-clock synchrony (which drifts during power outages).
  - **Atomic Local Outbox:** A mutation updates the local materialized view, appends an immutable event record, and enqueues an outbox entry in a **single atomic SQLite transaction**.

---

## 4. Existing Field Tools & Competitive Differentiation

| Solution | Primary Focus | Major Bottleneck in Disaster Operations | ShiVi Differentiation |
| :--- | :--- | :--- | :--- |
| **ODK / KoboToolbox** | Structured survey data collection | Passive data collection; no bidirectional task dispatch, dynamic re-routing, or real-time conflict handling | Active operational execution engine, bidirectional task state machine, and domain-aware conflict safety |
| **CommCare** | Longitudinal case management | Strict case hierarchy; limited spatial task dispatch and rapid life-safety contradiction handling | Spatial tasking, multi-party causal sync, and protected field freeze |
| **WhatsApp Groups** | Ad-hoc volunteer messaging | Unstructured noise, zero audit trail, massive duplicate dispatches, unverified closures | Structured triage, explainable priority, evidence provenance, and verified supervisor closure |

---

## 5. Summary of Key Architectural Invariants
1. **Never Overwrite Life-Safety Fields via Last-Write-Wins (LWW):** Contradictory observations on routes, shelters, or missing persons must freeze dependent automation and alert an authorized human commander.
2. **Deterministic Idempotency:** Any event delivered multiple times over unstable radios/networks must produce exactly one business effect.
3. **Evidence-Gated Verification:** Tasks cannot be marked complete without valid cryptographic evidence (SHA-256 binary hash, GPS accuracy, timestamp).
