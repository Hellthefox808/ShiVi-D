# ShiVi Operations: Comprehensive Troubleshooting & Diagnostic Wizard

This diagnostic guide provides field operators, tactical communicators, and command center engineers with actionable runbooks for diagnosing and recovering from anomalies across the ShiVi edge-to-cloud topology.

---

## 📑 Diagnostic Matrix

| Subsystem | Common Symptom | Diagnostic Command / Log Marker | Primary Root Cause | Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **BLE Mesh GATT** | Packets dropping, partial sync | `CRC32_MISMATCH` / `CHUNK_TIMEOUT` | MTU size exceeding physical radio buffer | Enable 496-byte chunking in `bluetooth_mesh_framing.dart` |
| **SQLite Edge DB** | App pauses on field mutation | `sqlite3.OperationalError: database is locked` | Concurrent async writes without WAL mode | Enable `PRAGMA journal_mode=WAL;` and busy timeout (5000ms) |
| **Conflict Engine** | Tasks frozen, cannot dispatch | `ConflictCase active: is_route_blocked=TRUE` | Unresolved contradictory life-safety reports | Human Incident Commander must adjudicate claim in Command Web |
| **AI Gateway** | Entity extraction taking >3s | `AI_GATEWAY_TIMEOUT: falling back to regex` | Large model inference latency | Verify deterministic regex fallback triggered; adjust threshold to 1500ms |
| **Web Command COP** | DevTools connection failure | `Could not find DevToolsActivePort` | Chrome remote debugging disabled | Run Chrome with `--remote-debugging-port=9222` and remote debugging active |
| **Next.js on Node 26**| `EISDIR: readlink ... _app.js` | `Build failed because of webpack errors` | Node 26 Windows libuv readlink bug | Run via `node scripts/run-next.js dev` with preload compatibility patch |

---

## 1. Multi-Bearer Mesh & Edge Radio Diagnostics

### Symptom: BLE Mesh Gossip fails to discover neighboring responders
1. **Verify BLE Radio Permissions:**
   On Android 12+, ensure runtime permissions are granted:
   - `android.permission.BLUETOOTH_SCAN` (with `neverForLocation` flag if applicable)
   - `android.permission.BLUETOOTH_ADVERTISE`
   - `android.permission.BLUETOOTH_CONNECT`
   - `android.permission.ACCESS_FINE_LOCATION`
2. **Inspect GATT MTU Negotiation:**
   If peer devices connect but drop event envelopes:
   ```bash
   # Filter mobile logs for packet fragmentation
   adb logcat -s "ShiViBLEMesh:V" "BluetoothGatt:D"
   ```
   If packets exceed 512 bytes without fragmentation, verify `PacketFraming.chunkPayload(payload, maxChunkSize: 496)` is active.
3. **Clear Stale BLE Cache:**
   Cycle Bluetooth adapter or toggle Airplane Mode for 5 seconds to flush the OS BLE GATT table.

---

## 2. SQLite Outbox & Drift Concurrency Diagnostics

### Symptom: `database is locked` (`SQLITE_BUSY`) during high-frequency GPS tracking
1. **Verify Write-Ahead Logging (WAL):**
   Execute SQLite integrity check:
   ```sql
   PRAGMA journal_mode;
   -- Must return 'wal'
   PRAGMA busy_timeout = 5000;
   -- Ensures 5-second wait before raising SQLITE_BUSY
   ```
2. **Inspect WAL Checkpoint:**
   If `shivi_local.db-wal` grows beyond 20 MB:
   ```sql
   PRAGMA wal_checkpoint(TRUNCATE);
   ```
3. **Ensure Single Writer Connection:**
   In Drift, configure all write queries through the designated database repository singleton to prevent thread contention.

---

## 3. Causal Conflict Engine & Safety Freeze Recovery

### Symptom: Emergency task is safety-frozen (`is_route_blocked=TRUE`) and automated routing is blocked
1. **Explanation:**
   This is an **intentional system invariant** (Invariant 3: Zero Silent Overwrites). When concurrent contradictory observations arrive regarding a life-safety route, the system refuses to automate dispatch.
2. **Adjudication Runbook (Web Command Center):**
   - Navigate to **Conflict Adjudicator** panel at `http://localhost:3000`.
   - Review contradictory claims side-by-side:
     - Claim A (e.g. *SDRF Scout Alpha*: `USABLE`)
     - Claim B (e.g. *Ward Volunteer Beta*: `BLOCKED`)
   - Click **Adjudicate Claim**, select the verified field condition (`BLOCKED` or `PASSABLE`), enter justification, and submit.
3. **CLI Adjudication (if Web COP unavailable):**
   ```bash
   curl -X POST "http://localhost:8000/v1/conflicts/{conflict_id}/resolve" \
     -H "Content-Type: application/json" \
     -d '{"resolved_value": "BLOCKED", "adjudicator_id": "IC-COMMANDER-01", "rationale": "Aerial drone confirmed road submerged."}'
   ```

---

## 4. Governed Advisory AI Gateway Diagnostics

### Symptom: Distress transcriptions or entity extraction hanging
1. **Inspect Fallback Mechanism:**
   ShiVi is architected with a strict $1,500\text{ms}$ deterministic circuit breaker. If the local or remote LLM does not respond:
   ```text
   [AI_GATEWAY] Warning: Model response exceeded 1500ms.
   [AI_GATEWAY] Cascading to deterministic RuleBasedExtractor.
   ```
2. **Verify Entity Extraction Rules:**
   Test the deterministic regex parser directly:
   ```python
   from app.modules.intelligence.gateway import RuleBasedExtractor
   result = RuleBasedExtractor.extract("3 people trapped near flooded temple")
   assert result["people_at_risk"] == 3
   assert result["category"] == "RESCUE"
   ```

---

## 5. Web Command Center & Chrome DevTools MCP Diagnostics

### Symptom: Chrome DevTools MCP server returns `Could not find DevToolsActivePort`
1. **Ensure Google Chrome is Running with Remote Debugging:**
   ```powershell
   # Windows PowerShell launch with remote debugging
   Start-Process "chrome.exe" -ArgumentList "--remote-debugging-port=9222","--user-data-dir=$env:TEMP\chrome_dev_profile"
   ```
2. **Verify Debugging Port Accessibility:**
   Open a browser tab or curl:
   ```bash
   curl http://127.0.0.1:9222/json/version
   ```
   Ensure it returns valid browser and protocol version metadata.
3. **Configure MCP Server Parameters:**
   In `.mcp.json` or client settings, pass `--browser-url=http://127.0.0.1:9222` rather than relying on `--autoConnect` in sandboxed environments.

### Symptom: Next.js Webpack Build Error on Windows Node 26 (`EISDIR: readlink ... _app.js`)
1. **Explanation:**
   Node 26 on Windows contains a known libuv quirk where `fs.readlink` on regular files throws `EISDIR` instead of `EINVAL`.
2. **Resolution:**
   Use the built-in ShiVi runner wrapper:
   ```bash
   # From frontend/
   node scripts/run-next.js dev
   # Or build:
   node scripts/run-next.js build
   ```
   This automatically preloads `node26-patch.js` to normalize error codes.

---

## 6. Backend Performance & Health Monitoring

### Diagnostic Health Checks
```bash
# Liveness probe (should be >1,000 req/s)
curl -i http://localhost:8000/health

# IOC Dashboard In-Memory Cache summary
curl -i http://localhost:8000/v1/dashboard/summary

# Full 9-Step Disaster Simulation Endpoint
curl -X POST http://localhost:8000/v1/demo/simulate-workflow
```

### Resetting Transient Local Data Safely
```bash
# Run safe database reset without data loss
python backend/scripts/reset_db_safe.py
```
