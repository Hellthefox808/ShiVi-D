# ShiVi: Security, Privacy and STRIDE Threat Model

## 1. Security Architecture & Trust Zones

```
[Untrusted Public Edge (Citizens / Public Sensors)]
                     │
                     ▼ (WAF + TLS 1.3 + Rate Limiting)
[Authenticated Tenant Zone (Device JWT + Role Validation)]
                     │
                     ▼
[Authorized Domain Execution (RBAC + ABAC Policies)]
                     │
                     ▼
[Protected Storage & Evidence Zone (PostgreSQL + MinIO / Blob)]
                     │
                     ▼
[Audited Egress (Immutable Audit Ledger + Signed Partner Webhooks)]
```

---

## 2. STRIDE Threat Analysis and Countermeasures

| Threat Category | Disaster Operation Attack Vector | ShiVi Mitigations |
| :--- | :--- | :--- |
| **Spoofing** | Adversary injects fabricated rescue reports to misdirect emergency squads. | Device fingerprint registration, JWT token signing, and quarantine of unverified citizen reports as `UNVERIFIED` until corroborated. |
| **Tampering** | Rogue actor alters route observations or modifies evidence photographs. | Client-side SHA-256 pre-hashing of binaries before upload; append-only immutable operational event tables with SHA-256 integrity digests. |
| **Repudiation** | Commander denies issuing an evacuation abort order. | Append-only `audit_entries` ledger recording actor ID, IP address, exact timestamp, and mandatory justification strings for all protected state overrides. |
| **Information Disclosure** | Multi-tenant leak exposing vulnerable victim locations or shelter capacities to unauthorized actors. | Strict tenant boundary enforcement (`tenant_id`) across all ORM queries; future pilot adds database Row-Level Security (RLS). |
| **Denial of Service** | Mass device reconnection storm overwhelming the central API after backhaul recovery. | Client-side jittered exponential backoff; maximum batch size limits ($\le 50$ events/request); asynchronous Redis queue ingestion. |
| **Elevation of Privilege** | Field responder attempts to force supervisor verification or self-assign command authority. | Server-side role validation (`SUPERVISOR` check) on all adjudication and verification endpoints. |

---

## 3. Data Privacy and Sensitive Citizen Protection
1. **Data Minimization:** Citizen reporting requires only essential fields: Category, People Count, Location, and Evidence. No Aadhaar numbers, financial data, or unnecessary PII is ever collected.
2. **Short-Lived Evidence Access:** Presigned object storage URLs expire after 15 minutes.
3. **Retention & Archival:** Incident data transitions to cold archive storage 90 days after closure according to configurable disaster management retention policies.
