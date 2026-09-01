# ShiVi: Synchronization and Conflict-Resolution Specification

## 1. Mathematical Model of Causal State Convergence

Each edge node $k \in \{1, \dots, M\}$ maintains:
1. A monotonic device counter $s_k \in \mathbb{N}$.
2. A causal version vector $V_k: \text{NodeID} \to \mathbb{N}$.
3. An append-only local event log $E_k = [e_1, e_2, \dots]$.

When node $k$ generates a local state mutation $\Delta$, it creates an operational event:
$$e = \langle \text{event\_id}, \text{tenant\_id}, \text{entity\_type}, \text{entity\_id}, \text{changes}, \text{actor\_id}, k, s_k, t_{\text{occurred}}, V_k, H(e) \rangle$$
where $H(e)$ is the SHA-256 integrity digest of the payload.

---

## 2. Server Causal Evaluation & Conflict Decision Tree

```
                     [Inbound Client Event Batch]
                                  │
                                  ▼
                     Is Event Valid & Authorized?
                     ├── No  ──> HTTP 403/422 + Security Audit Entry
                     └── Yes
                                  │
                                  ▼
                    Has Event ID Already Been Seen?
                    ├── Yes ──> Idempotent ACK (Return cached HTTP 200 OK)
                    └── No
                                  │
                                  ▼
                 Is Modified Property Additive/Append-Only?
                 (e.g., field notes array, supplementary photo IDs)
                     ├── Yes ──> Auto-Merge Set Union + Append Event
                     └── No
                                  │
                                  ▼
               Is Update Causally Subsequent to Server State?
               (Client Base Version == Server Current Entity Version)
                     ├── Yes ──> Fast-Path State Materialization
                     └── No  ──> Concurrent Update Conflict Detected!
                                  │
                                  ▼
                 Is Field Covered by Deterministic Rule?
                 (e.g., ACCEPTED state supersedes stale OFFERED state)
                     ├── Yes ──> Apply Deterministic State Transition
                     └── No  ──> Protected Life-Safety Contradiction!
                                  │
                                  ▼
            +─────────────────────────────────────────────────────+
            |              PROTECTED CONFLICT PROTOCOL            |
            | 1. Store and preserve all contradictory claims.     |
            | 2. Create first-class ConflictCase entity.          |
            | 3. Set materialized entity status to 'UNCERTAIN'.   |
            | 4. Flag entity as 'is_frozen = TRUE'.               |
            | 5. Freeze all dependent operational tasks.          |
            | 6. Alert Incident Commander on Command Dashboard.   |
            | 7. Require Authorized Human Adjudication + Reason.  |
            +─────────────────────────────────────────────────────+
```

---

## 3. Detailed Walkthrough of P0 Conflict Scenario

1. **Initial Condition:** Arterial `ROUTE-88` is seeded with status `UNKNOWN`.
2. **Task Dispatch:** Task `task-01` ("Evacuate 3 stranded civilians") is dispatched on `ROUTE-88`.
3. **Concurrent Offline Mutations:**
   - **Device A (SDRF Scout):** Observes clear asphalt, logs `ROUTE-88` as `USABLE`, attaches photo `photo-01`.
   - **Device B (Ward Volunteer):** Observes bridge railing collapse 2 miles ahead, logs `ROUTE-88` as `BLOCKED`, attaches warning text note.
4. **Reconnection & Sync Batch Push:** Both devices push their local event outboxes to `/v1/sync/push`.
5. **Server Conflict Detection:**
   - Additive properties auto-merge: `photos = ["photo-01"]`, `notes = ["Bridge railing collapsed..."]`.
   - Status property detects contradiction: `USABLE` vs `BLOCKED`.
   - Server creates `ConflictCase(entity_id="ROUTE-88", conflicting_field="status")`.
   - `ROUTE-88` status becomes `UNCERTAIN`; `is_frozen` becomes `TRUE`.
   - Dependent `task-01` is automatically updated to `is_route_blocked = TRUE` and status `BLOCKED`.
6. **Supervisor Adjudication:**
   - Incident Commander reviews photo, note, and timestamps in the Web Conflict Console.
   - Adjudicates status to `BLOCKED` with mandatory justification: *"Drone survey confirms bridge railing failure under 4ft water. Route impassable."*
7. **Convergence & Task Resumption:**
   - `ROUTE-88` status updates to `BLOCKED`.
   - Task `task-01` is recalculated and rerouted via Sector 4 Boat Ramp.
   - The resolution event synchronizes to all connected and reconnecting devices.
