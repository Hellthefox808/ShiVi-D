/**
 * ShiVi Operations Console - Disaster SMS & Satellite Broadcast Gateway
 * =====================================================================
 *
 * Briefing:
 *     Austere communications console page (`SmsGatewayPage`) enabling bidirectional emergency SMS
 *     intake, localized cell broadcasts, and 140-byte compact satellite burst encoding/decoding.
 *     Features:
 *     - Tab 1: Inbound Citizen Emergency SOS Simulator:
 *       * Ingests unstructured citizen distress messages (GSM modem, Twilio, or C-DOT CAP).
 *       * Multilingual NLP entity extraction (casualties, GPS, landmarks, severity).
 *       * Automated life-safety SMS dispatch within 160-character single-segment constraints.
 *     - Tab 2: Sector Emergency Broadcast Console:
 *       * Geographic sector targeting with live character counter and segment calculator.
 *       * Delivery receipts and cell broadcast ledger tracking.
 *     - Tab 3: Satellite 140-Byte Burst Lab:
 *       * Compact alphanumeric encoding for bandwidth-constrained satellite transceivers
 *         (Iridium SBD, Garmin inReach, C-DOT satellite terminals).
 *       * Strict <=140 byte budget with IEEE 802.3 8-character hexadecimal CRC32 checksum.
 *       * Satellite burst decoder reconstituting wire strings into validated domain objects.
 *     - Tab 4: Transmission Audit Ledger:
 *       * Tamper-evident logging of all inbound SOS reports, auto-replies, and broadcasts.
 *
 * Reason:
 *     When 4G/5G mobile towers fail or lose backhaul in severe floods, basic 2G voice/SMS channels
 *     and satellite communicators remain the sole surviving links for stranded citizens and remote scouts.
 *     This gateway bridges low-bandwidth citizen SMS directly into the high-bandwidth Common Operational Picture.
 */

"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  MessageSquare,
  Send,
  Radio,
  Satellite,
  ShieldAlert,
  CheckCircle,
  Clock,
  ArrowLeft,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  PhoneCall,
  Activity,
  Layers,
} from "lucide-react";
import { api } from "../../services/api";

/**
 * Briefing:
 *     Disaster SMS & Satellite Gateway page component.
 *
 * Reason:
 *     Provides operators with an interactive workbench to test, verify, and broadcast
 *     emergency text messages and satellite telemetry bursts.
 */
export default function SmsGatewayPage() {
  // Explanation: Active tab view ('inbound', 'broadcast', 'satellite', 'logs').
  const [activeTab, setActiveTab] = useState<"inbound" | "broadcast" | "satellite" | "logs">("inbound");

  // =========================================================================
  // Inbound SMS Simulator State
  // =========================================================================

  // Explanation: Simulated citizen sender phone number.
  const [inboundPhone, setInboundPhone] = useState("+919876543212");
  // Explanation: Simulated unstructured emergency text message.
  const [inboundText, setInboundText] = useState("SOS RESCUE 6 SECTOR 4 TRAPPED ROOFTOP RAPID FLOOD WATER RISE");
  // Explanation: Selected channel gateway ('GSM_GATEWAY', 'TWILIO', 'CDAC_CAP').
  const [inboundGateway, setInboundGateway] = useState("GSM_GATEWAY");
  // Explanation: True while inbound SMS request is inflight.
  const [isIngesting, setIsIngesting] = useState(false);
  // Explanation: Parsed incident and auto-reply response from /v1/integrations/sms/inbound.
  const [inboundResult, setInboundResult] = useState<any>(null);

  // =========================================================================
  // Sector Emergency Broadcast State
  // =========================================================================

  // Explanation: Targeted geographic operational sector for emergency broadcast.
  const [broadcastSector, setBroadcastSector] = useState("Sector 4 - Guwahati Basin");
  // Explanation: Title classification of the hazard.
  const [broadcastHazard, setBroadcastHazard] = useState("Flash Flood Warning");
  // Explanation: Actionable evacuation or shelter instruction for citizens.
  const [broadcastInstruction, setBroadcastInstruction] = useState(
    "Route-88 Bridge Breached. Water rising. Move to Primary School high ground. Detour via Boat Ramp active."
  );
  // Explanation: True while broadcast request is being processed.
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  // Explanation: Broadcast receipt confirmation from /v1/integrations/sms/broadcast.
  const [broadcastResult, setBroadcastResult] = useState<any>(null);

  // =========================================================================
  // Satellite Burst Lab State
  // =========================================================================

  // Explanation: Canonical event ID to encode into satellite burst.
  const [satEventId, setSatEventId] = useState("EVT-A9F8");
  // Explanation: Domain category code.
  const [satCategory, setSatCategory] = useState("RESCUE");
  // Explanation: Severity rating.
  const [satSeverity, setSatSeverity] = useState("CRITICAL");
  // Explanation: Estimated casualties at risk.
  const [satPeople, setSatPeople] = useState(5);
  // Explanation: WGS84 latitude coordinate.
  const [satLat, setSatLat] = useState(26.1856);
  // Explanation: WGS84 longitude coordinate.
  const [satLon, setSatLon] = useState(91.7483);
  // Explanation: Compact description string (max 24 characters).
  const [satDesc, setSatDesc] = useState("ROOFTOP FLOOD");
  // Explanation: Encoded satellite burst output object from /v1/integrations/sms/compact/encode.
  const [encodedBurst, setEncodedBurst] = useState<any>(null);

  // Explanation: Input wire string for satellite burst decoder.
  const [decodeInput, setDecodeInput] = useState("SHV:1:EVT-A9F8:RES:CRIT:5:26.186,91.748:ROOFTOP FLOOD:1B3E42D7");
  // Explanation: Reconstituted incident object from /v1/integrations/sms/compact/decode.
  const [decodedResult, setDecodedResult] = useState<any>(null);

  // =========================================================================
  // Transmission Logs State
  // =========================================================================

  // Explanation: Historical array of message transmissions.
  const [logs, setLogs] = useState<any[]>([]);
  // Explanation: True while logs are refreshing.
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  /**
   * Briefing:
   *     Fetches transmission logs from /v1/integrations/sms/logs.
   */
  const fetchLogs = async () => {
    setIsLoadingLogs(true);
    try {
      const data = await api.getSmsLogs();
      setLogs(data || []);
    } catch (err) {
      console.warn("Could not fetch SMS logs:", err);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  // Explanation: Fetch logs on initial component mount.
  useEffect(() => {
    fetchLogs();
  }, []);

  /**
   * Briefing:
   *     Submits simulated citizen SMS to backend inbound processing endpoint.
   */
  const handleInboundSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsIngesting(true);
    try {
      const res = await api.processInboundSms(inboundPhone, inboundText, inboundGateway);
      setInboundResult(res);
      fetchLogs();
    } catch (err: any) {
      alert("Failed to process inbound SMS: " + err.message);
    } finally {
      setIsIngesting(false);
    }
  };

  /**
   * Briefing:
   *     Dispatches sector-wide emergency SMS broadcast.
   */
  const handleBroadcastSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsBroadcasting(true);
    try {
      const res = await api.broadcastSectorAlert({
        sector_name: broadcastSector,
        hazard_type: broadcastHazard,
        instruction: broadcastInstruction,
      });
      setBroadcastResult(res);
      fetchLogs();
    } catch (err: any) {
      alert("Failed to broadcast alert: " + err.message);
    } finally {
      setIsBroadcasting(false);
    }
  };

  /**
   * Briefing:
   *     Encodes structured incident data into 140-byte compact satellite burst string.
   */
  const handleEncodeSatellite = async () => {
    try {
      const res = await api.encodeSatelliteBurst({
        event_id: satEventId,
        category: satCategory,
        severity: satSeverity,
        people_at_risk: Number(satPeople),
        latitude: Number(satLat),
        longitude: Number(satLon),
        short_desc: satDesc,
      });
      setEncodedBurst(res);
      setDecodeInput(res.burst_string);
    } catch (err: any) {
      alert("Encoding failed: " + err.message);
    }
  };

  /**
   * Briefing:
   *     Decodes a satellite burst wire string and verifies CRC32 checksum integrity.
   */
  const handleDecodeSatellite = async () => {
    try {
      const res = await api.decodeSatelliteBurst(decodeInput);
      setDecodedResult(res);
    } catch (err: any) {
      alert("Decoding failed: " + err.message);
    }
  };

  // Explanation: Character length calculation tracking standard GSM 160-character single segment limits.
  const charCount = `SHIVI ALERT [${broadcastSector.split(" - ")[0]}]: ${broadcastHazard.toUpperCase()}. ${broadcastInstruction.trim()} Dial 112/1070.`.length;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 lg:px-8 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-all font-medium"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to COP</span>
            </Link>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-500 p-[2px]">
              <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center shadow-sm">
                <Radio className="w-4 h-4 text-amber-600" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-wider text-slate-900">DISASTER SMS & SATELLITE GATEWAY</h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                  ZERO-DATA RELAY
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Cellular GSM • CDAC CAP v1.2 Webhook • Satellite 140B Burst Framing
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              GSM Modem: ACTIVE
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 p-4 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>Carrier Radio Channel</span>
              <Radio className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-lg font-bold text-slate-900">GSM 900/1800</div>
            <div className="text-[11px] text-emerald-600 font-semibold mt-1">Multi-Carrier Relay Ready</div>
          </div>

          <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>Auto-Reply Triage</span>
              <Sparkles className="w-4 h-4 text-purple-600" />
            </div>
            <div className="text-lg font-bold text-slate-900">NLP Deterministic</div>
            <div className="text-[11px] text-purple-600 font-semibold mt-1">English, Hindi & Assamese</div>
          </div>

          <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>Satellite Burst Budget</span>
              <Satellite className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-lg font-bold text-slate-900">&le; 140 Bytes</div>
            <div className="text-[11px] text-amber-600 font-semibold mt-1">IEEE 802.3 CRC-32 Frame</div>
          </div>

          <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>Total Transmissions</span>
              <Activity className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-lg font-bold text-slate-900">{logs.length} Logged</div>
            <div className="text-[11px] text-amber-600 font-semibold mt-1">Audit Ledger Chained</div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center border-b border-slate-200 gap-4">
          <button
            onClick={() => setActiveTab("inbound")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === "inbound"
                ? "border-amber-500 text-amber-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Inbound Citizen SOS
          </button>
          <button
            onClick={() => setActiveTab("broadcast")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === "broadcast"
                ? "border-amber-500 text-amber-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Send className="w-4 h-4" />
            Sector Emergency Broadcast
          </button>
          <button
            onClick={() => setActiveTab("satellite")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === "satellite"
                ? "border-amber-500 text-amber-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Satellite className="w-4 h-4" />
            140B Satellite Burst Lab
          </button>
          <button
            onClick={() => setActiveTab("logs")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === "logs"
                ? "border-amber-500 text-amber-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Clock className="w-4 h-4" />
            Transmission Logs
          </button>
        </div>

        {/* Tab 1: Inbound Citizen Emergency SOS */}
        {activeTab === "inbound" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
                <PhoneCall className="w-4 h-4 text-amber-600" />
                Simulate Citizen Emergency SMS Ingestion
              </h2>
              <p className="text-xs text-slate-600 mb-4">
                Test how the backend parses unstructured citizen distress SMS, extracts casualties & coordinates, computes priority, and generates automated safety advice.
              </p>

              {/* Presets */}
              <div className="flex flex-wrap gap-2 mb-4">
                <button
                  type="button"
                  onClick={() => {
                    setInboundText("SOS RESCUE 6 SECTOR 4 TRAPPED ROOFTOP RAPID FLOOD WATER RISE");
                    setInboundPhone("+919876543212");
                  }}
                  className="text-[11px] px-2.5 py-1 rounded bg-amber-50 text-amber-800 hover:bg-amber-100 border border-amber-200 font-medium"
                >
                  Preset: 6 Trapped Sector 4
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setInboundText("बाढ़ में 4 लोग फंसे हैं तुरंत नाव चाहिए सेक्टर 2 ब्रह्मपुत्र");
                    setInboundPhone("+919876543215");
                  }}
                  className="text-[11px] px-2.5 py-1 rounded bg-purple-50 text-purple-800 hover:bg-purple-100 border border-purple-200 font-medium"
                >
                  Preset: Hindi Distress (4 लोग)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setInboundText("CRITICAL MEDICAL 2 INJURED GPS 26.1433, 91.7898 DISPUR CLINIC");
                    setInboundPhone("+919876543216");
                  }}
                  className="text-[11px] px-2.5 py-1 rounded bg-orange-50 text-orange-800 hover:bg-orange-100 border border-orange-200 font-medium"
                >
                  Preset: GPS Coordinates
                </button>
              </div>

              <form onSubmit={handleInboundSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Citizen Sender Phone Number</label>
                  <input
                    type="text"
                    value={inboundPhone}
                    onChange={(e) => setInboundPhone(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 font-mono focus:bg-white focus:border-amber-500 focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Inbound SMS Body (Unstructured Text)</label>
                  <textarea
                    rows={3}
                    value={inboundText}
                    onChange={(e) => setInboundText(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Gateway Channel</label>
                    <select
                      value={inboundGateway}
                      onChange={(e) => setInboundGateway(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                    >
                      <option value="GSM_GATEWAY">GSM 900/1800 Modem</option>
                      <option value="TWILIO">Twilio Disaster Webhook</option>
                      <option value="CDAC_CAP">C-DOT / CDAC CAP Gateway</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isIngesting}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold text-sm shadow-md shadow-amber-500/20 transition-all flex items-center justify-center gap-2"
                >
                  <Send className={`w-4 h-4 ${isIngesting ? "animate-spin" : ""}`} />
                  {isIngesting ? "Ingesting & Parsing..." : "Ingest Citizen Emergency SMS"}
                </button>
              </form>
            </div>

            {/* Inbound Result Card */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                Live Incident Resolution & Auto-Reply Dispatch
              </h2>
              <p className="text-xs text-slate-600 mb-4">
                Shows parsed entities, calculated priority score, and the life-safety response SMS transmitted back to the citizen.
              </p>

              {inboundResult ? (
                <div className="space-y-4">
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-800 font-mono">
                        {inboundResult.local_reference}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-700 border border-red-200 font-bold">
                        P{inboundResult.priority_score.toFixed(0)} • {inboundResult.category}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500">Location:</span>{" "}
                        <span className="text-slate-900 font-medium">{inboundResult.location_name}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Casualties:</span>{" "}
                        <span className="text-slate-900 font-medium">{inboundResult.people_at_risk} at Risk</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Coordinates:</span>{" "}
                        <span className="text-slate-900 font-mono">{inboundResult.latitude.toFixed(4)}, {inboundResult.longitude.toFixed(4)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Severity:</span>{" "}
                        <span className="text-amber-800 font-semibold">{inboundResult.severity}</span>
                      </div>
                    </div>
                  </div>

                  {/* Outbound SMS Text */}
                  <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-4">
                    <div className="flex items-center justify-between text-xs text-amber-800 font-semibold mb-1">
                      <span>AUTOMATED LIFE-SAFETY SMS REPLY</span>
                      <span className="font-mono text-slate-500">{inboundResult.auto_reply_sms.length}/160 Chars</span>
                    </div>
                    <div className="text-xs text-slate-800 font-mono bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                      "{inboundResult.auto_reply_sms}"
                    </div>
                    <div className="text-[11px] text-emerald-700 font-medium mt-2 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Dispatched via GSM Modem to {inboundResult.sender_phone}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-xs text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                  <MessageSquare className="w-8 h-8 text-slate-300 mb-2" />
                  Submit an inbound SMS to inspect live entity extraction and auto-reply dispatch.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Sector Broadcast */}
        {activeTab === "broadcast" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
                <Send className="w-4 h-4 text-amber-600" />
                Dispatch Emergency Sector Broadcast
              </h2>
              <p className="text-xs text-slate-600 mb-4">
                Transmits targeted SMS alerts to all citizen and volunteer phones within an affected geographic sector.
              </p>

              {/* Template presets */}
              <div className="flex flex-wrap gap-2 mb-4">
                <button
                  type="button"
                  onClick={() => {
                    setBroadcastSector("Sector 4 - Guwahati Basin");
                    setBroadcastHazard("Flash Flood Evacuation");
                    setBroadcastInstruction("Route-88 Bridge Breached. Water rising. Move to Primary School High Ground. Detour via Boat Ramp active.");
                  }}
                  className="text-[11px] px-2.5 py-1 rounded bg-amber-50 text-amber-800 hover:bg-amber-100 border border-amber-200 font-medium"
                >
                  Preset: Route-88 Breach Evacuation
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setBroadcastSector("Sector 2 - Brahmaputra Flood Wall");
                    setBroadcastHazard("Contaminated Water Advisory");
                    setBroadcastInstruction("Flood water mixed with supply lines. Boil water for 10 mins. Medical kits at Sector 2 Camp.");
                  }}
                  className="text-[11px] px-2.5 py-1 rounded bg-orange-50 text-orange-800 hover:bg-orange-100 border border-orange-200 font-medium"
                >
                  Preset: Boil Water Advisory
                </button>
              </div>

              <form onSubmit={handleBroadcastSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Target Geographic Sector</label>
                  <select
                    value={broadcastSector}
                    onChange={(e) => setBroadcastSector(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                  >
                    <option value="Sector 4 - Guwahati Basin">Sector 4 - Guwahati Basin (High Risk)</option>
                    <option value="Sector 2 - Brahmaputra Flood Wall">Sector 2 - Flood Wall (Inundated)</option>
                    <option value="Sector 1 - Dispur Medical Center">Sector 1 - Dispur Center</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Hazard Title</label>
                  <input
                    type="text"
                    value={broadcastHazard}
                    onChange={(e) => setBroadcastHazard(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-slate-700">Actionable Instruction</label>
                    <span className={`text-[11px] font-mono ${charCount <= 160 ? "text-emerald-700" : "text-red-600 font-bold"}`}>
                      {charCount}/160 Chars {charCount <= 160 ? "(1 Segment)" : "(Multi-part SMS)"}
                    </span>
                  </div>
                  <textarea
                    rows={3}
                    value={broadcastInstruction}
                    onChange={(e) => setBroadcastInstruction(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={isBroadcasting}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white font-bold text-sm shadow-md shadow-red-500/20 transition-all flex items-center justify-center gap-2"
                >
                  <Send className={`w-4 h-4 ${isBroadcasting ? "animate-spin" : ""}`} />
                  {isBroadcasting ? "Broadcasting..." : "Broadcast Emergency SMS Alert"}
                </button>
              </form>
            </div>

            {/* Broadcast Result */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                Transmission Status & Cell Broadcast Ledger
              </h2>
              <p className="text-xs text-slate-600 mb-4">
                Verified delivery receipts and carrier queuing state across cellular towers.
              </p>

              {broadcastResult ? (
                <div className="space-y-4">
                  <div className="bg-slate-50 p-4 rounded-xl border border-emerald-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-emerald-800">
                        {broadcastResult.broadcast_id}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">
                        {broadcastResult.delivery_status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-800 font-mono bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                      "{broadcastResult.primary_sms_text}"
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                      <div>Recipients Queued: <span className="text-slate-900 font-bold">{broadcastResult.recipients_queued} Phones</span></div>
                      <div>GSM Segment: <span className="text-emerald-700 font-bold">Single (160B)</span></div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-xs text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                  <Send className="w-8 h-8 text-slate-300 mb-2" />
                  Dispatch an alert to view broadcast delivery status and character count metrics.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Satellite 140B Burst Lab */}
        {activeTab === "satellite" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Encoder */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
                <Satellite className="w-4 h-4 text-amber-600" />
                Satellite 140-Byte Burst Encoder
              </h2>
              <p className="text-xs text-slate-600 mb-4">
                Compresses incident envelopes into compact alphanumeric bursts for Iridium, Garmin inReach, or C-DOT satellite communicators with CRC-32 checksums.
              </p>

              <div className="grid grid-cols-2 gap-3 mb-3 text-xs">
                <div>
                  <label className="text-slate-600 block mb-1 font-semibold">Event ID</label>
                  <input
                    type="text"
                    value={satEventId}
                    onChange={(e) => setSatEventId(e.target.value)}
                    className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded font-mono text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-slate-600 block mb-1 font-semibold">Category</label>
                  <select
                    value={satCategory}
                    onChange={(e) => setSatCategory(e.target.value)}
                    className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                  >
                    <option value="RESCUE">RESCUE</option>
                    <option value="MEDICAL">MEDICAL</option>
                    <option value="HAZARD">HAZARD</option>
                    <option value="RELIEF">RELIEF</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-600 block mb-1 font-semibold">Severity</label>
                  <select
                    value={satSeverity}
                    onChange={(e) => setSatSeverity(e.target.value)}
                    className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-600 block mb-1 font-semibold">People at Risk</label>
                  <input
                    type="number"
                    value={satPeople}
                    onChange={(e) => setSatPeople(Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded font-mono text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-slate-600 block mb-1 font-semibold">Latitude</label>
                  <input
                    type="number"
                    step="0.001"
                    value={satLat}
                    onChange={(e) => setSatLat(Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded font-mono text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-slate-600 block mb-1 font-semibold">Longitude</label>
                  <input
                    type="number"
                    step="0.001"
                    value={satLon}
                    onChange={(e) => setSatLon(Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded font-mono text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="text-xs text-slate-600 block mb-1 font-semibold">Short Description (&le; 24 chars)</label>
                <input
                  type="text"
                  value={satDesc}
                  onChange={(e) => setSatDesc(e.target.value)}
                  className="w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <button
                type="button"
                onClick={handleEncodeSatellite}
                className="w-full py-2 px-3 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs shadow-md transition-all"
              >
                Encode Compact Satellite Burst
              </button>

              {encodedBurst && (
                <div className="mt-4 bg-slate-50 p-3 rounded-lg border border-amber-200 text-xs font-mono space-y-1">
                  <div className="text-slate-500 font-semibold">WIRE STRING:</div>
                  <div className="text-amber-900 font-bold break-all select-all">{encodedBurst.burst_string}</div>
                  <div className="flex items-center justify-between text-[11px] text-slate-600 pt-2 border-t border-slate-200">
                    <span>Length: {encodedBurst.byte_length} Bytes / 140B</span>
                    <span className="text-emerald-700 font-bold">CRC32: {encodedBurst.crc32_checksum}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Decoder */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                Satellite Burst Decoder & CRC Verification
              </h2>
              <p className="text-xs text-slate-600 mb-4">
                Validates and reconstitutes an incoming 140-byte satellite burst packet back into an operational event.
              </p>

              <div className="mb-4">
                <label className="text-xs text-slate-600 block mb-1 font-semibold">Satellite Wire Burst String</label>
                <textarea
                  rows={2}
                  value={decodeInput}
                  onChange={(e) => setDecodeInput(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-amber-900 focus:bg-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <button
                type="button"
                onClick={handleDecodeSatellite}
                className="w-full py-2 px-3 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-bold text-xs shadow-md transition-all mb-4"
              >
                Decode & Verify Checksum
              </button>

              {decodedResult && (
                <div className="bg-slate-50 p-4 rounded-lg border border-emerald-200 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 font-mono">{decodedResult.event_id}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${decodedResult.crc32_valid ? "bg-emerald-100 text-emerald-800 border border-emerald-200" : "bg-red-100 text-red-800 border border-red-200"}`}>
                      {decodedResult.crc32_valid ? "CRC-32 VALID" : "CRC-32 CORRUPTED"}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-slate-700">
                    <div>Category: <span className="text-amber-800 font-bold">{decodedResult.category}</span></div>
                    <div>Severity: <span className="text-orange-800 font-bold">{decodedResult.severity}</span></div>
                    <div>Casualties: <span className="text-slate-900 font-bold">{decodedResult.people_at_risk}</span></div>
                    <div>Coordinates: <span className="text-slate-900 font-mono">{decodedResult.latitude}, {decodedResult.longitude}</span></div>
                  </div>

                  <div className="pt-2 border-t border-slate-200 text-slate-600">
                    Description: <span className="text-slate-900 font-medium">{decodedResult.short_desc}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 4: Logs */}
        {activeTab === "logs" && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Transmission Audit Ledger</h2>
                <p className="text-xs text-slate-500">Complete log of inbound citizen SOS, outbound replies, and broadcasts.</p>
              </div>
              <button
                onClick={fetchLogs}
                disabled={isLoadingLogs}
                className="flex items-center gap-1 text-xs text-amber-600 hover:text-amber-700 font-bold"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingLogs ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>

            {logs.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-xs">No transmissions recorded yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-700 border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Time</th>
                      <th className="p-2.5">Direction</th>
                      <th className="p-2.5">Phone / Recipient</th>
                      <th className="p-2.5">Message Content</th>
                      <th className="p-2.5">Reference</th>
                      <th className="p-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {logs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="p-2.5 text-slate-500 whitespace-nowrap font-mono text-[11px]">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="p-2.5">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                              log.direction === "INBOUND"
                                ? "bg-amber-100 text-amber-800 border-amber-200"
                                : log.direction === "BROADCAST"
                                ? "bg-orange-100 text-orange-800 border-orange-200"
                                : "bg-emerald-100 text-emerald-800 border-emerald-200"
                            }`}
                          >
                            {log.direction}
                          </span>
                        </td>
                        <td className="p-2.5 font-mono text-slate-700">{log.sender_or_recipient}</td>
                        <td className="p-2.5 max-w-md truncate text-slate-800 font-mono text-[11px]">{log.text}</td>
                        <td className="p-2.5 text-slate-500 font-mono text-[11px]">{log.related_ref || "-"}</td>
                        <td className="p-2.5">
                          <span className="text-emerald-700 text-[10px] font-semibold">{log.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
