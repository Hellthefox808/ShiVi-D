# ShiVi: Business Model, Unit Logic and Cross-Sector Scale

## 1. Commercial Pricing Tiers

```
+-------------------------------------------------------------------------------+
|  1. Community Tier (Free / Open Relief)                                       |
|     - Free for grassroots humanitarian volunteer squads (< 25 active users)   |
|     - Standard offline incident reporting and basic task dispatch            |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|  2. Professional NGO & District Tier ($12 / active field user / month)        |
|     - Offline causal delta sync, explainable priority triage, conflict engine |
|     - 99.9% uptime SLA, automated daily backups, email/phone support          |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|  3. Enterprise State Authority & Municipal License ($50,000 - $250,000 / yr) |
|     - Dedicated tenant deployment, single sign-on (Entra ID), custom GIS feeds|
|     - Pluggable Sector Packs (Health, Utilities, Agriculture), 24/7 EOC team  |
+-------------------------------------------------------------------------------+
```

---

## 2. Unit Economics & Cost Analysis

| Metric | Target Value | Economic Driver |
| :--- | :--- | :--- |
| **Cloud Infrastructure Cost / Active User** | $\$ 0.45\text{ / month}$ | Lightweight event delta payloads ($\le 5\text{KB}$) and ephemeral serverless compute. |
| **Media Storage Cost / Incident** | $\$ 0.02\text{ / incident}$ | Compressed photo/audio binaries stored in tiered Azure Blob storage. |
| **Gross Margin** | $85\%+$ | Software-only local-first architecture with minimal cloud egress. |
| **Payback Period** | $< 4\text{ months}$ | Rapid deployment without requiring on-premise hardware installations. |

---

## 3. Cross-Sector Primitive Leverage

| Sector | Core Incident / Case | Field Task | Scarce Resource | Protected Life-Safety Conflict |
| :--- | :--- | :--- | :--- | :--- |
| **Disaster Response** | Stranded civilians | Boat evacuation | Inflatable boat, fuel | Route safe vs submerged |
| **Public Health** | Cholera / Dengue cluster | Water chlorination | Paramedic squad, medicine | Contaminated vs clean well |
| **Municipal Utilities**| Water main rupture | Excavate & clamp pipe | Repair crew, heavy crane | High-voltage cable safe vs live |
| **Agriculture** | Locust swarm / blight | Aerial pesticide spray | Spraying drone, chemical | Field infested vs treated |
| **Logistics** | Critical relief supply drop| Deliver medical kit | 4x4 Truck, refrigerated van| Road passable vs washed out |
