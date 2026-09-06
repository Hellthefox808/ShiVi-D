# ShiVi Tactical Field Mobile Client: Frontline Deployment Guide

This guide details the procedure for packaging, signing, and deploying the **ShiVi Flutter Field Client** (`mobile/`) to frontline responders operating in zero-connectivity and austere disaster zones.

---

## 1. Prerequisites & Toolchain

- **Flutter SDK:** 3.19.x or higher (Dart 3.3+)
- **Android SDK:** API Level 34 (Android 14) with minimum SDK Level 24 (Android 7.0 Nougat)
- **NDK Version:** 26.1.10909125+
- **JDK:** OpenJDK 17

---

## 2. Generating Release Keystore

For production field deployments, generate an immutable Ed25519 or RSA-4096 signing key:

```bash
keytool -genkey -v \
  -keystore android/app/shivi-release.jks \
  -keyalg RSA \
  -keysize 4096 \
  -validity 10000 \
  -alias shivi-field-key
```

Configure `android/key.properties`:
```properties
storePassword=your_secure_store_password
keyPassword=your_secure_key_password
keyAlias=shivi-field-key
storeFile=shivi-release.jks
```

---

## 3. Production Release APK Compilation

Disaster operations require optimized, standalone APK binaries split by hardware CPU architecture to conserve field storage and download bandwidth:

```bash
cd mobile

# 1. Fetch dependencies
flutter pub get

# 2. Build Architecture-Specific Release APKs
flutter build apk --release --split-per-abi
```

### Generated Artifacts
- `build/app/outputs/flutter-apk/app-arm64-v8a-release.apk` (~14 MB) — Modern 64-bit field smartphones (Samsung Galaxy XCover, Pixel, Motorola Defy).
- `build/app/outputs/flutter-apk/app-armeabi-v7a-release.apk` (~12 MB) — Budget legacy 32-bit tactical handsets.
- `build/app/outputs/flutter-apk/app-x86_64-release.apk` (~15 MB) — Ruggedized field tablets and laptops.

---

## 4. Offline Pre-Bundling & Zero-Connectivity Sideloading

In catastrophic blackouts, responders cannot access the Google Play Store. Deploy via one of three tactical distribution conduits:

### Method A: Direct Bluetooth Object Push (OPP)
Responders transfer the compiled `app-arm64-v8a-release.apk` peer-to-peer over Bluetooth 5.0 to arriving search-and-rescue teams.

### Method B: Wi-Fi Direct / Local Ad-Hoc Hotspot
A mobile incident command post deploys a battery-powered micro-hotspot serving the APK binary directly via HTTP on `http://192.168.49.1:8080/shivi.apk`.

### Method C: Physical OTG / MicroSD Handover
Rugged USB-C thumb drives containing the APK and pre-downloaded offline vector map tiles (`guwahati_sector4_contours.mbtiles`) are distributed to tactical team leads at the basecamp staging area.

---

## 5. First-Run Provisioning & Hardware Self-Calibration

Upon first launch without network:
1. The app initializes local ACID SQLite storage via Drift Write-Ahead Logging (`shivi_field_outbox.db`).
2. Hardware Performance Tier auto-calibration categorizes the device:
   - **Tier Low (<3 GB RAM):** Disables fluid shaders, locks to high-contrast tactical lists.
   - **Tier Mid (3–6 GB RAM):** Enables 2D tactical radar and vector maps at 30 FPS.
   - **Tier High (>6 GB RAM):** Enables full 3D terrain and satellite overlays.
3. Generates a unique local Ed25519 device keypair in hardware Keystore / Secure Enclave for cryptographic audit chain signing.
