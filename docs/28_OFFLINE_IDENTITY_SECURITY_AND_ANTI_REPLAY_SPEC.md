# ShiVi: Offline Identity Security, Hardware Attestation & Anti-Replay Specification

## 1. The Replay Attack & Identity Spoofing Loophole (The Dilemma)

In standard client-server web architectures, authentication and authorization are synchronous: the cloud server verifies JWT validity, role permissions, and request nonces in real-time before committing mutations.

In **local-first, disconnected disaster architectures**, mutations occur on edge devices hours or days before reaching the central server. This introduces four catastrophic attack vectors:

1. **Synthetic Clock Skew / Shift Backdating:** A malicious actor modifies the mobile device clock to backdate an action, attempting to bypass shift authorization windows or manipulate causal event sorting.
2. **Offline Privilege Escalation:** A compromised citizen or tier-1 volunteer device crafts synthetic mutation events claiming elevated roles (e.g. attempting to authorize `TASK_COMPLETION_VERIFIED` or mark hazardous routes as `USABLE`).
3. **Replay & Injection Attacks:** An attacker sniffs valid operational packets and replays them repeatedly or re-injects stale status mutations upon reconnection.
4. **Token Expiry Desynchronization:** An attacker uses an expired or revoked JWT session key created days earlier while claiming the action occurred offline during the valid session window.

---

## 2. The ShiVi 4-Tier Cryptographic Defense Architecture

```text
[Offline Edge Device (Hardware Keystore / Secure Enclave)]
  ├── Monotonic Device Sequence Counter: N = N + 1
  ├── Cryptographic Hash Chain: Hash_N = SHA256(Event_N || Hash_{N-1})
  ├── Hardware Asymmetric Signature: Ed25519_Sign(PrivKey_HW, Event_N)
  └── Offline Capability Token: Signed Server Role Grant
                 │
                 ▼ (Stored in Transactional Local SQLite Outbox)
           [Reconnection & Sync Push]
                 │
                 ▼
    [Server-Side Asynchronous Authorization Engine]
  ├── Step 1: Global Nonce Deduplication (Anti-Replay)
  ├── Step 2: Monotonic Sequence Counter Verification (Seq_N > Seq_{N-1})
  ├── Step 3: Hash Chain Integrity Check (Hash_{N-1} == Expected_Parent)
  ├── Step 4: Role-Based Capability Matrix Enforcement
  ├── Step 5: Clock Drift Clamping (Max skew: <= 120s from true server UTC)
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
[VALID ADMISSION]     [SECURITY QUARANTINE / DLQ]
- Causal Event Log    - Immediate Audit Alert
- State Materialized  - Incident Commander Notified
```

---

## 3. Security Invariants & Defense Mechanics

### 3.1 Hardware-Bound Device Identity (Keystore / Secure Enclave)

- Every enrolled responder and supervisor device provisions a non-exportable hardware-backed keypair ($K_{\text{priv}}, K_{\text{pub}}$).
- Every event is signed over its canonical tuple:
  $$\text{Signature} = \text{HMAC/Sign}(K_{\text{device}}, \text{event\_id} \parallel \text{tenant\_id} \parallel \text{actor\_id} \parallel \text{device\_id} \parallel \text{device\_sequence} \parallel \text{event\_type} \parallel \text{prev\_event\_hash})$$
- Even if an attacker extracts a bearer JWT or password, they cannot forge device signatures without physical access to the device's secure element.

### 3.2 Monotonic Tamper-Evident Hash Chain

- Each device maintains a local genesis hash chain.
- An event with `device_sequence: 5` must reference the exact SHA-256 digest of `device_sequence: 4`.
- Replayed past events or fabricated intermediary events immediately break the hash chain and fail validation (`HASH_CHAIN_BROKEN`).

### 3.3 Offline Capability Grants (Role-Based Action Gating)

- Role permissions are strictly enforced against the immutable Capability Matrix:
  - `CITIZEN`: Restricted to `INCIDENT_REPORTED`, `HAZARD_OBSERVED`, `PHOTO_ATTACHED`.
  - `RESPONDER`: Field transitions (`TASK_ACCEPTED`, `TASK_ON_SITE`, `TASK_COMPLETED`, `ROUTE_STATUS_UPDATED`, `EVIDENCE_SUBMITTED`).
  - `SUPERVISOR`: Dispatch & verification (`TASK_ASSIGNED`, `TASK_COMPLETION_VERIFIED`, `CONFLICT_ADJUDICATED`, `EVIDENCE_VERIFIED`).
- Any attempt by a lower-privileged role to craft an elevated mutation is halted with `UNAUTHORIZED_ROLE`.

### 3.4 Logical Clock Verification & Clock Drift Clamping

- The server rejects any offline event claiming a wall-clock time in the future beyond a strict 120-second threshold (`TIME_SKEW_EXCEEDED`).
- Causal ordering relies on Lamport vector clocks and monotonic device sequences, rendering client system clock manipulation harmless to global ordering.

---

## 4. Verification Test Evidence

- **Test Suite:** [`tests/test_offline_identity_and_anti_replay.py`](file:///d:/ShiVi,/tests/test_offline_identity_and_anti_replay.py)
- **Covered Attack Vectors:**
  1. `test_reject_privilege_escalation_from_offline_citizen` (Passed)
  2. `test_anti_replay_duplicate_event_id` (Passed)
  3. `test_monotonic_sequence_violation` (Passed)
  4. `test_detect_tampered_cryptographic_signature` (Passed)
  5. `test_detect_future_clock_skew_tampering` (Passed)
  6. `test_valid_signed_event_sequence` (Passed)
- **Engine Implementation:** [`apps/core-api/app/core/security_crypto.py`](file:///d:/ShiVi,/apps/core-api/app/core/security_crypto.py)
