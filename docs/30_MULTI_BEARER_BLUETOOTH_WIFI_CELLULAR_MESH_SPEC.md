# ShiVi: Multi-Bearer Network Architecture & Bluetooth/Wi-Fi/Cellular Mesh Protocol

## 1. Executive Summary & Disaster Radio Realities

In tier-4 catastrophic disaster zones (e.g. Cyclone landfall, major flooding, seismically severed fiber corridors), telecommunications infrastructure does not fail uniformly:

- **Phase 1 (Normal Operations):** High-speed Wi-Fi Broadband and 4G/5G Cellular LTE are active.
- **Phase 2 (Grid Disruption):** Wi-Fi is lost; cellular falls back to congested 2G/3G EDGE.
- **Phase 3 (Tower Collapse / Zero Internet):** Cellular towers lose power or backhaul; zero internet connectivity remains.
- **Phase 4 (Total Blackout):** Only peer-to-peer radio frequency communication between mobile responder devices is physically possible.

ShiVi implements an **Adaptive Multi-Bearer Mesh Architecture** that dynamically shifts across 6 network transport layers without interrupting field workflow.

---

## 2. Multi-Bearer Transport Layer Matrix

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                    ShiVi Adaptive Multi-Bearer Stack                         │
├─────────────────┬──────────┬──────────────┬───────────────┬──────────────────┤
│ Bearer Layer    │ Max MTU  │ Internet Req │ P2P Supported │ Battery Profile  │
├─────────────────┼──────────┼──────────────┼───────────────┼──────────────────┤
│ Wi-Fi Broadband │ 64 KB    │ YES          │ NO            │ Low (Tier 2)     │
│ Cellular 4G/5G  │ 32 KB    │ YES          │ NO            │ Medium (Tier 3)  │
│ Cellular 2G/3G  │ 2 KB     │ YES          │ NO            │ Medium (Tier 3)  │
│ Satellite NTN   │ 256 B    │ YES (Orbit)  │ NO            │ High (Tier 5)    │
│ Wi-Fi Direct    │ 16 KB    │ NO           │ YES (High-BW) │ High (Tier 4)    │
│ BLE 5.0+ Mesh   │ 480 B    │ NO           │ YES (Gossip)  │ Ultra-Low (Tier 1│
└─────────────────┴──────────┴──────────────┴───────────────┴──────────────────┘
```

---

## 3. Bluetooth Low Energy (BLE) Mesh & Framing Engine

Because standard BLE GATT characteristics have effective payload limits (23 to 512 bytes MTU), large JSON operational mutations cannot be transmitted in a single packet.

```text
[Original Outbox Mutation (1.5 KB JSON Event)]
                      │
                      ▼
        [Crc32Calculator: IEEE 802.3]
                      │
                      ▼
         [BleMeshFramingEngine]
 ┌────────────────────┬────────────────────┬────────────────────┐
 ▼                    ▼                    ▼                    ▼
[Chunk 0 / 3]        [Chunk 1 / 3]        [Chunk 2 / 3]        [Chunk 3 / 3]
- PacketID: 0x0A4F   - PacketID: 0x0A4F   - PacketID: 0x0A4F   - PacketID: 0x0A4F
- TotalChunks: 4     - TotalChunks: 4     - TotalChunks: 4     - TotalChunks: 4
- ChunkIdx: 0        - ChunkIdx: 1        - ChunkIdx: 2        - ChunkIdx: 3
- CRC32: 0x9B2C11F4  - CRC32: 0x9B2C11F4  - CRC32: 0x9B2C11F4  - CRC32: 0x9B2C11F4
- Payload: 450 B     - Payload: 450 B     - Payload: 450 B     - Payload: 150 B
                      │
                      ▼ (Transmitted via BLE GATT Characteristic)
         [Peer Reassembler & CRC Check]
                      │
                      ▼
  [Validated & Ingested into Peer SQLite Outbox]
```

### 3.1 Binary Chunk Header Format

```text
Offset | Field Name   | Type    | Description
0..1   | Packet ID    | Uint16  | Unique 16-bit packet identifier
2      | Total Chunks | Uint8   | Total number of fragments (1 - 255)
3      | Chunk Index  | Uint8   | Zero-based sequence index
4..7   | CRC-32       | Uint32  | IEEE 802.3 polynomial checksum of full payload
8..N   | Payload      | Bytes   | Raw fragment payload slice
```

---

## 4. Epidemic Gossip & "Data Mule" Delay-Tolerant Routing

In disaster zones without cell coverage, responders physically move across geographical sectors:

```text
[Isolated Sector A]                 [En Route Path]             [Relief Base (Connected)]
(Responder Alpha)                    (Direct BLE Sync)           (Responder Charlie)
- Reports Hazard Incident            Alpha ◄─BLE─► Charlie      - Uploads Alpha's Incident
- Zero Cell / Wi-Fi Signal           (Charlie acts as Data Mule)  via Cellular 5G
- Transmits via BLE Mesh                                         - Incident Triage Complete!
```

### 4.1 Multi-Hop Relay Security & Loop Prevention

To prevent infinite event propagation loops across mobile meshes, every relayed event includes:

- `relay_hops`: Incremented on each peer transfer.
- `relayed_by_devices`: Ordered list of carrier device IDs.
- `LoopGuard.check_event_loop()`: Halts propagation if $Hops > 5$ or if an event encounters a previously traversed node.

---

## 5. Adaptive Radio Duty Cycling & Battery Preservation

To maximize phone survivability in the field (where responders may lack electricity for 72+ hours):

- **Battery > 50%:** Full-speed BLE discovery (10s scan / 5s advertise) + Wi-Fi Direct search.
- **Battery 20% - 50%:** Power-saver BLE discovery (5s scan / 30s advertise); Wi-Fi Direct disabled unless explicitly triggered.
- **Battery < 20%:** Ultra-low duty cycle (2s scan every 2 minutes); transmits critical life-safety SOS beacons only.

---

## 6. Implementation & Verification Summary

- **Network Bearer Core:** [`apps/field-mobile/lib/core/network/network_bearer.dart`](file:///d:/ShiVi,/apps/field-mobile/lib/core/network/network_bearer.dart)
- **BLE Mesh Framing & CRC-32:** [`apps/field-mobile/lib/core/network/bluetooth_mesh_framing.dart`](file:///d:/ShiVi,/apps/field-mobile/lib/core/network/bluetooth_mesh_framing.dart)
- **Multi-Bearer Sync Orchestrator:** [`apps/field-mobile/lib/core/sync/multi_bearer_sync_orchestrator.dart`](file:///d:/ShiVi,/apps/field-mobile/lib/core/sync/multi_bearer_sync_orchestrator.dart)
- **Backend Relay Gateway:** [`apps/core-api/app/modules/sync/router.py`](file:///d:/ShiVi,/apps/core-api/app/modules/sync/router.py)
- **Flutter Test Suite:** [`apps/field-mobile/test/multi_bearer_network_test.dart`](file:///d:/ShiVi,/apps/field-mobile/test/multi_bearer_network_test.dart)
- **Backend Test Suite:** [`tests/test_multi_bearer_mesh_relay.py`](file:///d:/ShiVi,/tests/test_multi_bearer_mesh_relay.py) (All 47 tests passing).
