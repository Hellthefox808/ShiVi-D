# ShiVi: Distributed Physical Asset Lock & Possession Resolution Protocol

## 1. The Distributed Asset Lock Loophole (The Dilemma)

In disaster response operations with zero telecommunications connectivity, physical reality is atomic and scarce:
- A specific high-capacity de-watering water pump (`GEN-PUMP-01`) or inflatable rescue boat can physically only exist in one geographic coordinate at a time.
- Two disconnected squad leads (Lead A and Lead B) inspect their local offline caches. Both see `GEN-PUMP-01` marked as `AVAILABLE`.
- **Action:**
  - Lead A allocates `GEN-PUMP-01` to Incident 101 (Flooded Hospital ICU).
  - Lead B allocates `GEN-PUMP-01` to Incident 102 (Submerged Residential Lane).
- **The Classical Failure Modes:**
  1. **Option 0: Last-Write-Wins (LWW) / Silent Theft:** Whichever mutation reaches the cloud server last silently overwrites ownership. Lead A may have loaded the pump onto a boat and motored away, while Lead B arrives expecting the pump, resulting in stranded rescue teams and life-safety catastrophe.
  2. **Option 1: Complete Freeze / Paralyzing Lock:** The server detects dual allocation, marks the generator `UNCERTAIN / LOCKED`, and demands manual Incident Commander adjudication before permitting use. While awaiting review, neither squad can operate the generator, paralyzing the rescue operation.

---

## 2. The ShiVi 5-Pillar Resolution Architecture

ShiVi resolves this dilemma through **"Physical Possession Verification & Priority-Based Continuous Allocation with Automated Substitution."**

```text
       [Disconnected Lead A]                   [Disconnected Lead B]
       (Incident 101: Hospital ICU)            (Incident 102: Road Lane)
       (Physical NFC Tag Scan Proof)           (Virtual Intent Reservation)
                 │                                       │
                 ▼                                       ▼
       [Local Outbox Commit]                   [Local Outbox Commit]
                 │                                       │
                 └───────────────┬───────────────────────┘
                                 │ (Reconnection & Push)
                                 ▼
         [Distributed Physical Asset Allocation Engine]
                                 │
     ┌───────────────────────────┴───────────────────────────┐
     │                                                       │
     ▼                                                       ▼
[Winner: Lead A (Hospital ICU)]             [Contingency: Lead B (Roadway)]
- Retains GEN-PUMP-01                       - Immediate Contingency Notification
- Physical Proof Verified (NFC/GPS)         - Auto-Allocated Substitute (GEN-PUMP-02)
- Zero Interruption to ICU Drainage         - Dispatch from Sector 3 Depot (ETA 18m)
     │                                                       │
     └───────────────────────────┬───────────────────────────┘
                                 │
                                 ▼
                   [Immutable Audit Ledger]
                   (Recorded & Commander Alerted)
```

---

## 3. Decision Matrix & Precedence Invariants

```text
Claim A vs Claim B Decision Tree:

1. Physical Possession Check:
   - Does one claim have cryptographic physical proof (NFC tap / QR scan / GPS <= 15m)?
     -> YES: Physical possessor WINS. Virtual claimant is automatically assigned substitute.

2. Life-Safety Priority Precedence:
   - Both claims are virtual OR both have physical proof:
     - Is |Priority(A) - Priority(B)| >= 5.0 points?
       -> YES: Higher life-safety priority WINS (e.g. ICU 95.0 vs Road 45.0).

3. Causal First-Claim Invariant:
   - Priority scores are within 5.0 points:
     -> Causal earlier timestamp WINS.

4. Zero-Deadlock Substitute Guarantee:
   - The non-winning squad is NEVER stalled or locked.
   - The engine automatically queries available inventory in the same asset category and immediately reserves the nearest substitute (e.g. GEN-PUMP-02 from Sector 3 Depot).
```

---

## 4. Implementation Reference

- **Data Models:** [`apps/core-api/app/modules/assets/models.py`](file:///d:/ShiVi,/apps/core-api/app/modules/assets/models.py) (`PhysicalAsset`, `AssetAllocationClaim`)
- **Resolution Engine:** [`apps/core-api/app/modules/assets/allocation_engine.py`](file:///d:/ShiVi,/apps/core-api/app/modules/assets/allocation_engine.py) (`DistributedAssetAllocationEngine`)
- **REST Endpoints:** [`apps/core-api/app/modules/assets/router.py`](file:///d:/ShiVi,/apps/core-api/app/modules/assets/router.py) (`POST /v1/assets/{code}/claim`)
- **Automated Tests:** [`tests/test_distributed_asset_contention.py`](file:///d:/ShiVi,/tests/test_distributed_asset_contention.py) (100% passing across physical proof, priority hierarchy, and auto-substitution).

---

> **Guiding Principle:** Software should never paralyze physical action during a crisis. Ground reality takes precedence; the system adapts with automatic contingency options.
