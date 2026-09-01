# ShiVi: Functional Specification Document (FSD)

## 1. Domain Entities and Lifecycles

### 1.1 Incident Lifecycle
```text
DRAFT (Local) ──> REPORTED (Synced) ──> TRIAGED (Priority Scored)
                       │                       │
                       ▼                       ▼
                   REJECTED                ASSIGNED (Dispatched)
                                               │
                                               ▼
                                         IN_PROGRESS (On Site)
                                               │
                                               ▼
                                      AWAITING_VERIFICATION (Evidence Uploaded)
                                               │
                                               ▼
                                           RESOLVED (Supervisor Approved)
                                               │
                                               ▼
                                            CLOSED (Archived)
```

- **Transitions:**
  - `DRAFT` $\rightarrow$ `REPORTED`: Triggered when an offline report is successfully committed and pushed during synchronization.
  - `REPORTED` $\rightarrow$ `TRIAGED`: Priority score is calculated; supervisor verifies or overrides category/severity.
  - `TRIAGED` $\rightarrow$ `ASSIGNED`: Operational task is created and assigned to a specific responder or team.
  - `ASSIGNED` $\rightarrow$ `IN_PROGRESS`: Responder accepts task and transitions status to `EN_ROUTE` or `ON_SITE`.
  - `IN_PROGRESS` $\rightarrow$ `AWAITING_VERIFICATION`: Responder completes task and attaches completion evidence.
  - `AWAITING_VERIFICATION` $\rightarrow$ `RESOLVED`: Supervisor reviews evidence and confirms completion.

---

### 1.2 Task Lifecycle
```text
CREATED ──> OFFERED ──> ACCEPTED ──> EN_ROUTE ──> ON_SITE ──> COMPLETED ──> VERIFIED
               │                                                    │
               ▼                                                    ▼
            DECLINED                                      FAILED_VERIFICATION
```
- **Exceptional States:**
  - `BLOCKED`: Triggered automatically if the task route is placed under an active conflict freeze or hazard escalation.
  - `CANCELLED`: Preempted by supervisor due to mission reprioritization.

---

## 2. Explainable Multi-Factor Priority Algorithm

Incident priority score $P \in [0, 100]$ is calculated deterministically via a weighted sum of normalized factors:
$$P = \min\left(100, \sum_{i=1}^{5} w_i \cdot f_i\right)$$

### Factor Breakdown:
1. **Severity Factor ($w_1 = 30$):**
   - `CRITICAL`: 1.0 (Contribution: 30.0)
   - `HIGH`: 0.8 (Contribution: 24.0)
   - `MEDIUM`: 0.5 (Contribution: 15.0)
   - `LOW`: 0.2 (Contribution: 6.0)
2. **People at Risk Factor ($w_2 = 25$):**
   - Scaled logarithmically: $f_2 = \frac{\log_{10}(\min(N, 100) + 1)}{\log_{10}(101)}$ (Contribution: $0.0 - 25.0$).
3. **Urgency & Time Sensitivity ($w_3 = 15$):**
   - `IMMEDIATE` ($<1\text{ hr}$ rescue window): 1.0 (Contribution: 15.0)
   - `HIGH` ($<3\text{ hrs}$): 0.75 (Contribution: 11.25)
   - `MODERATE` ($<12\text{ hrs}$): 0.4 (Contribution: 6.0)
   - `LOW`: 0.1 (Contribution: 1.5)
4. **Category & Vulnerability ($w_4 = 15$):**
   - `RESCUE`: 1.0 (Contribution: 15.0)
   - `MEDICAL`: 0.9 (Contribution: 13.5)
   - `FLOOD_HAZARD`: 0.7 (Contribution: 10.5)
   - `SHELTER`: 0.5 (Contribution: 7.5)
   - `SUPPLY`: 0.3 (Contribution: 4.5)
5. **Evidence Confidence ($w_5 = 15$):**
   - Official sensor / verified authority: 1.0 (Contribution: 15.0)
   - Citizen report with verified photo & GPS: 0.85 (Contribution: 12.75)
   - Text-only unverified report: 0.5 (Contribution: 7.5)

---

## 3. Conflict Resolution Protocol

### 3.1 Decision Taxonomy
1. **Auto-Merge (Safe Additive Properties):**
   - Triggered when concurrent updates modify independent list fields (e.g., field notes array, supplementary photos).
   - Behavior: The server computes the union of the arrays, appends the operational event, and sets status to resolved without human intervention.
2. **Deterministic Domain Policy:**
   - Triggered when domain state rules deterministically order updates (e.g., an `ACCEPTED` state transition on an active device supersedes a stale `OFFERED` status from a delayed sync).
3. **Protected Conflict (Life-Safety Contradiction):**
   - Triggered when concurrent updates provide mutually exclusive values for safety-critical attributes (e.g., `route_status`: `USABLE` vs `BLOCKED`, `person_status`: `MISSING` vs `RESCUED`).
   - Behavior:
     - Target entity status is set to `UNCERTAIN`.
     - Entity is flagged as `is_frozen = TRUE`.
     - All active tasks relying on the entity are transitioned to `is_route_blocked = TRUE`.
     - An active `ConflictCase` is generated and assigned to the supervisor console.
     - Automated dispatch through the affected zone is blocked until an authorized human adjudicates the conflict with a mandatory explanation string ($\ge 10$ characters).

---

## 4. Evidence Verification Gate
- **Integrity Rule:** Before any critical task is marked `VERIFIED`, the system verifies:
  1. A valid binary attachment exists in object storage.
  2. The SHA-256 hash computed on upload matches the original client hash.
  3. The capture GPS coordinates fall within the acceptable bounding radius of the task location.
  4. An authorized supervisor explicitly approves the completion evidence with signed audit notes.
