# ShiVi: UI/UX and Accessibility Blueprint

## 1. Design System & WCAG 2.1 AA Compliance

### 1.1 Contrast & Emergency Modes
- **Extreme Sunlight Mode:** High-contrast light palette with dark black text ($12:1$ contrast ratio) for bright daylight boat rescue operations.
- **Night Operations Mode:** True dark palette (`#0B0F19`) with reduced blue light for low-glare night shelter coordination.
- **Color Invariant:** Critical status indicators (e.g., `CRITICAL`, `BLOCKED`, `CONFLICT`) are never communicated via color alone; they always include distinct geometric icons and clear textual badges.

### 1.2 Touch Ergonomics for Harsh Environments
- **Target Sizing:** All interactive buttons have a minimum hit target of $48 \times 48\text{ px}$ to accommodate wet hands or thick rescue gloves.
- **Haptic & Audio Feedback:** Distinct vibration and audio chimes on successful offline commits and emergency conflict alerts.

---

## 2. Key Screen Blueprints

### 2.1 Web Command Center (EOC)
- **Top Ambient Banner:** Real-time sync engine health, pending queue counts, flashing life-safety conflict alert indicator.
- **Left Column (30%):** Explainable Priority Queue with expandable multi-factor breakdown cards.
- **Center Column (50%):** Common Operational Picture with MapLibre GL spatial layers (NDEM flood contours, route status lines, responder markers).
- **Right Column (20%):** Conflict Adjudication Panel, Evidence Verification Gates, and Chronological Audit Timeline.

### 2.2 Field Mobile Client (Responder)
- **Home View:** Active assignment card with large `ACCEPT` / `EN_ROUTE` / `ON_SITE` / `COMPLETE` action buttons.
- **Route Status Reporter:** Quick 2-tap hazard reporting (`ROUTE_STATUS`: `USABLE` vs `BLOCKED`, optional photo/voice note).
- **Offline Sync Drawer:** Clear list of pending outbox events with manual retry button and timestamp indicators.
