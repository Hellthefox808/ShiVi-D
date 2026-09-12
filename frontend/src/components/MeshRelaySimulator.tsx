/**
 * ShiVi Operations Console - Omni-Bearer BLE Mesh Packet Framing Inspector
 * =========================================================================
 *
 * Briefing:
 *     Interactive protocol workbench component (`MeshRelaySimulator`) demonstrating the ShiVi
 *     Omni-Bearer Mesh Protocol and BLE 5.0 GATT packet fragmentation specification (DOC-30).
 *     Features:
 *     - Multi-bearer selector switching MTU boundaries dynamically:
 *       * BLE 5.0 GATT: 496 Bytes
 *       * Wi-Fi Direct: 1024 Bytes
 *       * LoRa Tactical: 222 Bytes
 *       * Satellite SBD: 340 Bytes
 *     - 3-hop mesh relay topology visualization (Citizen Originator -> Volunteer Repeater -> Boat Unit -> SEOC Sink).
 *     - Real-time payload fragmentation calling backend `/v1/sync/mesh/packetize`.
 *     - Multi-frame reassembly with out-of-order frame delivery simulation.
 *     - Adversarial bit-flip injection demonstrating that corrupted chunks fail CRC32 checksums
 *       and are dropped before poisoning the canonical state.
 *
 * Reason:
 *     When commercial internet collapses during natural disasters, search-and-rescue data must traverse
 *     austere radio channels with strict MTU limits. This component provides mission engineers and
 *     evaluators with a visual, testable verification suite for packetization, checksumming, and reassembly.
 */

"use client";

import React, { useState } from "react";
import {
  Radio,
  Cpu,
  Layers,
  ArrowRight,
  ShieldCheck,
  AlertOctagon,
  CheckCircle2,
  RefreshCw,
  Zap,
  Wifi,
  WifiOff,
  Hash,
  Database,
  Shuffle,
  Binary,
} from "lucide-react";
import api, { MeshFrame, MeshPacketizeResponse, MeshReassembleResponse } from "../services/api";

/**
 * Briefing:
 *     Mesh Relay Simulator and Packet Framing Workbench component.
 *
 * Reason:
 *     Enables engineers and incident commanders to inspect physical transmission frames,
 *     verify CRC32 checksums, and test out-of-order reassembly mechanics across different radios.
 */
export default function MeshRelaySimulator() {
  // Explanation: Selected radio bearer protocol defining the MTU boundary.
  const [bearerType, setBearerType] = useState<"BLE_5.0_GATT" | "WIFI_DIRECT" | "LORA_TACTICAL" | "SATELLITE_SBD">("BLE_5.0_GATT");
  // Explanation: Current maximum transmission unit in bytes (defaults to 496 for BLE GATT).
  const [mtuBytes, setMtuBytes] = useState<number>(496);
  // Explanation: Raw JSON event payload text to be fragmented.
  const [payloadText, setPayloadText] = useState<string>(
    JSON.stringify(
      {
        event_id: "EVT-RAD-8821",
        entity_type: "route_observation",
        entity_id: "ROUTE-88",
        event_type: "ROUTE_STATUS_UPDATE",
        status: "BLOCKED",
        hazard: "PIER_3_UNDERMINED_BY_4FT_SURGE",
        coordinates: { lat: 26.1856, lng: 91.7483 },
        reported_by: "scout_das",
        timestamp: new Date().toISOString(),
        evidence_sha256: "4a543aa2a700ae04e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934c",
      },
      null,
      2
    )
  );

  // Explanation: Sliced packet metadata and frames returned by /v1/sync/mesh/packetize.
  const [packetResult, setPacketResult] = useState<MeshPacketizeResponse | null>(null);
  // Explanation: Reassembly verification response returned by /v1/sync/mesh/reassemble.
  const [reassembleResult, setReassembleResult] = useState<MeshReassembleResponse | null>(null);
  // Explanation: True while packetize request is inflight.
  const [isPacketizing, setIsPacketizing] = useState<boolean>(false);
  // Explanation: True while reassembly request is inflight.
  const [isReassembling, setIsReassembling] = useState<boolean>(false);
  // Explanation: True if operator injected a malicious bit flip into the frame array.
  const [isTampered, setIsTampered] = useState<boolean>(false);

  /**
   * Briefing:
   *     Dispatches raw payload to backend packetizer service.
   *
   * Reason:
   *     Segments JSON string into ≤mtuBytes chunks, computing individual CRC32 checksums.
   */
  const handlePacketize = async () => {
    setIsPacketizing(true);
    setIsTampered(false);
    setReassembleResult(null);
    try {
      let parsedPayload: any = payloadText;
      try {
        parsedPayload = JSON.parse(payloadText);
      } catch {
        parsedPayload = payloadText;
      }
      const res = await api.packetizeMeshPayload(parsedPayload, mtuBytes, bearerType);
      setPacketResult(res);
    } catch (err) {
      console.error("Packetize error:", err);
    } finally {
      setIsPacketizing(false);
    }
  };

  /**
   * Briefing:
   *     Dispatches sliced frames to backend reassembler service.
   *
   * @param shuffleOrder If true, reverses frame arrival sequence to test out-of-order sorting.
   */
  const handleReassemble = async (shuffleOrder = false) => {
    if (!packetResult || packetResult.frames.length === 0) return;
    setIsReassembling(true);
    try {
      let framesToSend = [...packetResult.frames];
      if (shuffleOrder) {
        framesToSend.reverse();
      }
      const res = await api.reassembleMeshFrames(framesToSend);
      setReassembleResult(res);
    } catch (err) {
      console.error("Reassemble error:", err);
    } finally {
      setIsReassembling(false);
    }
  };

  /**
   * Briefing:
   *     Corrupts the first frame payload with malicious data to test tampering defenses.
   *
   * Reason:
   *     Validates that receiving gateway nodes detect CRC32/SHA-256 mismatches and discard
   *     poisoned packets before they reach application domain stores.
   */
  const handleTamperBit = async () => {
    if (!packetResult || packetResult.frames.length === 0) return;
    const tamperedFrames: MeshFrame[] = packetResult.frames.map((f, idx) =>
      idx === 0
        ? {
            ...f,
            chunk_payload_base64:
              typeof btoa !== "undefined"
                ? btoa("TAMPERED_MALICIOUS_DATA_STRING")
                : Buffer.from("TAMPERED_MALICIOUS_DATA_STRING").toString("base64"),
          }
        : f
    );
    setIsTampered(true);
    setIsReassembling(true);
    try {
      const res = await api.reassembleMeshFrames(tamperedFrames);
      setReassembleResult(res);
    } catch (err) {
      console.error("Tamper reassemble error:", err);
    } finally {
      setIsReassembling(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="bg-[#111318] border border-amber-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
              <Radio className="w-6 h-6 animate-pulse" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">
                  Omni-Bearer Mesh Protocol & BLE Packet Framing Inspector
                </h3>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  SPEC: DOC-30
                </span>
              </div>
              <p className="text-xs text-gray-400 max-w-3xl">
                In collapsed network conditions, ShiVi dynamically fragments large operational events into ≤496-byte
                BLE 5.0 GATT MTU frames with individual CRC32 checksums, multi-hop hop tracking, and SHA-256 payload assembly.
              </p>
            </div>
          </div>

          {/* Bearer Selectors */}
          <div className="flex flex-wrap gap-2">
            {[
              { id: "BLE_5.0_GATT", label: "BLE 5.0 GATT", mtu: 496 },
              { id: "WIFI_DIRECT", label: "Wi-Fi Direct", mtu: 1024 },
              { id: "LORA_TACTICAL", label: "LoRa Tactical", mtu: 222 },
              { id: "SATELLITE_SBD", label: "Satellite SBD", mtu: 340 },
            ].map((b) => (
              <button
                key={b.id}
                onClick={() => {
                  setBearerType(b.id as any);
                  setMtuBytes(b.mtu);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                  bearerType === b.id
                    ? "bg-amber-500 border-amber-400 text-black font-bold shadow-lg shadow-amber-500/30"
                    : "bg-[#08090C] border-[#222634] text-gray-400 hover:text-white"
                }`}
              >
                {b.label} ({b.mtu}B)
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Mesh Relay Hop Architecture Diagram */}
      <div className="bg-[#111318] border border-[#222634] rounded-2xl p-5 space-y-3">
        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider font-mono">
          Live Mesh Relay Topology // 3-Hop Multi-Bearer Gossip Route
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 relative">
          {[
            { name: "Node Alpha (Citizen Device)", role: "Originator", bearer: "BLE 5.0", range: "Local 80m", color: "border-amber-500 text-amber-400" },
            { name: "Node Bravo (SDRF Volunteer)", role: "Hop 1 Repeater", bearer: "BLE / Wi-Fi", range: "Relay 150m", color: "border-orange-500 text-orange-400" },
            { name: "Node Charlie (IRB Boat Unit)", role: "Hop 2 Repeater", bearer: "VHF Tactical", range: "Corridor 1.2km", color: "border-purple-500 text-purple-400" },
            { name: "Node Delta (SEOC Operations Hub)", role: "Destination Sink", bearer: "Satellite / Fiber", range: "Permanent", color: "border-emerald-500 text-emerald-400" },
          ].map((node, i) => (
            <div key={i} className={`bg-[#08090C] border ${node.color} rounded-xl p-3.5 space-y-2 relative`}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-gray-500">
                  HOP {i}
                </span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <div className="font-bold text-white text-xs">{node.name}</div>
              <div className="text-[11px] text-gray-400 font-mono flex justify-between">
                <span>{node.role}</span>
                <span>{node.bearer}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive Packet Slicing Studio */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input Payload & Controls */}
        <div className="bg-[#111318] border border-[#222634] rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Binary className="w-4 h-4 text-amber-400" /> Operational Event Payload (Raw)
            </h4>
            <span className="text-[11px] font-mono text-gray-400">{payloadText.length} bytes</span>
          </div>

          <textarea
            value={payloadText}
            onChange={(e) => setPayloadText(e.target.value)}
            rows={10}
            className="w-full bg-[#08090C] border border-[#222634] rounded-xl p-3 text-xs font-mono text-gray-300 focus:outline-none focus:border-amber-500"
          />

          <div className="flex flex-wrap gap-3">
            <button
              onClick={handlePacketize}
              disabled={isPacketizing}
              className="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50"
            >
              {isPacketizing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
              <span>Slice into ≤{mtuBytes}B Frames</span>
            </button>

            {packetResult && (
              <>
                <button
                  onClick={() => handleReassemble(false)}
                  disabled={isReassembling}
                  className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-2 transition-all"
                >
                  <CheckCircle2 className="w-4 h-4" /> Reassemble
                </button>

                <button
                  onClick={() => handleReassemble(true)}
                  disabled={isReassembling}
                  className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center gap-2 transition-all"
                  title="Test out-of-order frame delivery"
                >
                  <Shuffle className="w-4 h-4" /> Out-of-Order
                </button>

                <button
                  onClick={handleTamperBit}
                  disabled={isReassembling}
                  className="px-4 py-2.5 rounded-xl bg-red-600/80 hover:bg-red-500 text-white text-xs font-bold flex items-center gap-2 transition-all"
                  title="Test CRC32 / SHA-256 corruption detection"
                >
                  <AlertOctagon className="w-4 h-4" /> Inject Bit Flip
                </button>
              </>
            )}
          </div>
        </div>

        {/* Right: Sliced Frames & Reassembly Status */}
        <div className="bg-[#111318] border border-[#222634] rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-400" /> Sliced Mesh Frames (
              {packetResult ? packetResult.total_frames : 0})
            </h4>
            {packetResult && (
              <span className="text-[11px] font-mono text-emerald-400">
                Packet ID: {packetResult.packet_id}
              </span>
            )}
          </div>

          {/* Reassembly Result Alert */}
          {reassembleResult && (
            <div
              className={`p-3.5 rounded-xl border flex items-start gap-3 text-xs ${
                reassembleResult.status === "REASSEMBLED_VERIFIED"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                  : "bg-red-500/10 border-red-500/30 text-red-300"
              }`}
            >
              {reassembleResult.status === "REASSEMBLED_VERIFIED" ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <AlertOctagon className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-1 overflow-hidden">
                <div className="font-bold uppercase tracking-wider">
                  STATUS: {reassembleResult.status}
                </div>
                <div className="font-mono text-[11px] truncate">
                  SHA-256: {reassembleResult.integrity_hash_sha256 || "<CORRUPTED_DISCARDED>"}
                </div>
                <div className="text-[10px] text-gray-400">
                  CRC32 Integrity Check: {reassembleResult.crc32_verified ? "PASSED (100%)" : "FAILED (Tampered)"} | Frames:{" "}
                  {reassembleResult.received_frames} of {reassembleResult.total_frames}
                </div>
              </div>
            </div>
          )}

          {/* Frame Cards List */}
          <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
            {!packetResult ? (
              <div className="text-center py-12 text-xs text-gray-500 font-mono">
                Click "Slice into ≤{mtuBytes}B Frames" to inspect BLE 5.0 GATT framing.
              </div>
            ) : (
              packetResult.frames.map((frame) => (
                <div
                  key={frame.chunk_index}
                  className="bg-[#08090C] border border-[#222634] rounded-xl p-3 space-y-1.5 font-mono text-xs"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-amber-400 font-bold">
                      FRAME [{frame.chunk_index + 1}/{frame.total_chunks}]
                    </span>
                    <span className="text-gray-400 text-[10px]">{frame.chunk_bytes} bytes</span>
                    <span className="text-amber-400 text-[10px] bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                      CRC: 0x{frame.crc32.toUpperCase()}
                    </span>
                  </div>

                  <div className="bg-[#111318] p-2 rounded text-[11px] text-gray-300 truncate font-mono">
                    {frame.chunk_payload_text}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
