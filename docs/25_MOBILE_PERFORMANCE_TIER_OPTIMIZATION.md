# ShiVi: Mobile Optimization Architecture (Low-End to High-End Hardware)

## 1. Executive Summary & Design Constraints

Disaster response and emergency operations personnel deploy with vastly heterogeneous hardware:

- **Low-End Tier (Tier 1):** Budget field smartphones (e.g., 2GB–3GB RAM, Android Go / Android 8.0+, MediaTek Quad-Core, low-efficiency batteries, 60Hz LCD).
- **Mid-Range Tier (Tier 2):** Standard government issue devices (4GB–6GB RAM, Octa-Core, Android 11–13).
- **High-End Tier (Tier 3):** Commander tablets & ruggedized flagship terminals (8GB–12GB RAM, OLED 120Hz, satellite uplink accessories).

**ShiVi Mobile Invariant:**
> **The app must never crash from OutOfMemory (OOM), never drop below 60fps on the main UI thread during background sync, and must operate seamlessly in direct sunlight and extended battery blackouts.**

---

## 2. Adaptive Hardware Tier Matrix

| Parameter | Low-End Tier (2GB - 3GB RAM) | Mid-Range Tier (4GB - 6GB RAM) | High-End Tier (8GB+ RAM) |
| :--- | :---: | :---: | :---: |
| **Max Concurrent Sync Requests** | `1` (Strict sequential) | `2` | `4` |
| **Image Dimension Clamping** | Max `800px` | Max `1280px` | Max `2048px` |
| **Image Compression Quality** | `50%` | `75%` | `90%` |
| **Background JSON / Crypto Parsing** | Offloaded to background Isolate | Offloaded to background Isolate | Offloaded to background Isolate |
| **UI Animations & Blur** | Disabled (`0ms` transitions, zero blur) | Enabled standard Material | Enabled 120fps physics & glassmorphism |
| **Offline Map Tile Cache Cap** | `50 MB` | `150 MB` | `500 MB` |
| **Sync Batch Size** | `10 events / payload` | `25 events / payload` | `50 events / payload` |
| **Battery Throttling Threshold** | Throttle sync at `< 20%` battery | Throttle sync at `< 15%` battery | Throttle sync at `< 10%` battery |

---

## 3. Tactical Visual Profiles for Extreme Environments

### 3.1 OLED Stealth / Ultra Battery Saver Mode

- **True Black `#000000` Palette:** Powers down pixels on OLED displays, extending device mission life by up to **40%**.
- **High-Contrast Accents:** High-visibility Cyan `#06B6D4` and Hazard Orange `#F59E0B`.

### 3.2 Direct Sunlight Daylight Mode

- **Zero Glare Interference:** `#FFFFFF` background with heavy `#0F172A` high-contrast typography and bold borders. Responders can read incident summaries under midday tropical sun without blinding backlights.

### 3.3 Tactical Night Vision Mode

- **Dark-Adaptation Protection:** Monochromatic deep red `#FF1744` and dark ruby `#0A0000` prevents blinding responders or disturbing night-vision goggles.

---

## 4. Touch Target & Accessibility Standards

- **Gloved Touch Compliance:** All interactive buttons and selector chips meet or exceed **$\ge 48 \times 48\text{ dp}$** (with critical emergency triggers at $\ge 56\text{ dp}$).
- **Single-Handed Thumb Reach:** Emergency broadcast triggers and status transition buttons reside within the lower $40\%$ screen area for single-handed field operation while holding equipment.
