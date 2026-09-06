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

export default function SmsGatewayPage() {
  const [activeTab, setActiveTab] = useState<"inbound" | "broadcast" | "satellite" | "logs">("inbound");

  // Inbound SMS Simulator State
  const [inboundPhone, setInboundPhone] = useState("+919876543212");
  const [inboundText, setInboundText] = useState("SOS RESCUE 6 SECTOR 4 TRAPPED ROOFTOP RAPID FLOOD WATER RISE");
  const [inboundGateway, setInboundGateway] = useState("GSM_GATEWAY");
  const [isIngesting, setIsIngesting] = useState(false);
  const [inboundResult, setInboundResult] = useState<any>(null);

  // Broadcast State
  const [broadcastSector, setBroadcastSector] = useState("Sector 4 - Guwahati Basin");
  const [broadcastHazard, setBroadcastHazard] = useState("Flash Flood Warning");
  const [broadcastInstruction, setBroadcastInstruction] = useState("Route-88 Bridge Breached. Water rising. Move to Primary School high ground. Detour via Boat Ramp active.");
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [broadcastResult, setBroadcastResult] = useState<any>(null);

  // Satellite Burst Lab State
  const [satEventId, setSatEventId] = useState("EVT-A9F8");
  const [satCategory, setSatCategory] = useState("RESCUE");
  const [satSeverity, setSatSeverity] = useState("CRITICAL");
  const [satPeople, setSatPeople] = useState(5);
  const [satLat, setSatLat] = useState(26.1856);
  const [satLon, setSatLon] = useState(91.7483);
  const [satDesc, setSatDesc] = useState("ROOFTOP FLOOD");
  const [encodedBurst, setEncodedBurst] = useState<any>(null);

  const [decodeInput, setDecodeInput] = useState("SHV:1:EVT-A9F8:RES:CRIT:5:26.186,91.748:ROOFTOP FLOOD:1B3E42D7");
  const [decodedResult, setDecodedResult] = useState<any>(null);

  // Logs State
  const [logs, setLogs] = useState<any[]>([]);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

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

  useEffect(() => {
    fetchLogs();
  }, []);

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

  const handleDecodeSatellite = async () => {
    try {
      const res = await api.decodeSatelliteBurst(decodeInput);
      setDecodedResult(res);
    } catch (err: any) {
      alert("Decoding failed: " + err.message);
    }
  };

  const charCount = `SHIVI ALERT [${broadcastSector.split(" - ")[0]}]: ${broadcastHazard.toUpperCase()}. ${broadcastInstruction.trim()} Dial 112/1070.`.length;

  return (
    <div className="min-h-screen bg-[#070B13] text-gray-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-[#0B0F19]/90 backdrop-blur-md border-b border-[#1E293B] px-4 lg:px-8 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white px-2.5 py-1.5 rounded-lg bg-[#121826] border border-[#1E293B] transition-all"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to COP</span>
            </Link>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 p-[2px]">
              <div className="w-full h-full bg-[#0B0F19] rounded-[10px] flex items-center justify-center">
                <Radio className="w-4 h-4 text-cyan-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-wider text-white">DISASTER SMS & SATELLITE GATEWAY</h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  ZERO-DATA RELAY
                </span>
              </div>
              <p className="text-[11px] text-gray-400">
                Cellular GSM • CDAC CAP v1.2 Webhook • Satellite 140B Burst Framing
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              GSM Modem: ACTIVE
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 p-4 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-[#0F172A] border border-[#1E293B] p-4 rounded-xl">
            <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
              <span>Carrier Radio Channel</span>
              <Radio className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-lg font-bold text-white">GSM 900/1800</div>
            <div className="text-[11px] text-emerald-400 mt-1">Multi-Carrier Relay Ready</div>
          </div>

          <div className="bg-[#0F172A] border border-[#1E293B] p-4 rounded-xl">
            <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
              <span>Auto-Reply Triage</span>
              <Sparkles className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-lg font-bold text-white">NLP Deterministic</div>
            <div className="text-[11px] text-purple-400 mt-1">English, Hindi & Assamese</div>
          </div>

          <div className="bg-[#0F172A] border border-[#1E293B] p-4 rounded-xl">
            <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
              <span>Satellite Burst Budget</span>
              <Satellite className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-lg font-bold text-white">&le; 140 Bytes</div>
            <div className="text-[11px] text-amber-400 mt-1">IEEE 802.3 CRC-32 Frame</div>
          </div>

          <div className="bg-[#0F172A] border border-[#1E293B] p-4 rounded-xl">
            <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
              <span>Total Transmissions</span>
              <Activity className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-lg font-bold text-white">{logs.length} Logged</div>
            <div className="text-[11px] text-blue-400 mt-1">Audit Ledger Chained</div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center border-b border-[#1E293B] gap-4">
          <button
            onClick={() => setActiveTab("inbound")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === "inbound"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Inbound Citizen SOS
          </button>
          <button
            onClick={() => setActiveTab("broadcast")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === "broadcast"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            <Send className="w-4 h-4" />
            Sector Emergency Broadcast
          </button>
          <button
            onClick={() => setActiveTab("satellite")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === "satellite"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            <Satellite className="w-4 h-4" />
            140B Satellite Burst Lab
          </button>
          <button
            onClick={() => setActiveTab("logs")}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === "logs"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            <Clock className="w-4 h-4" />
            Transmission Logs
          </button>
        </div>

        {/* Tab 1: Inbound SMS */}
        {activeTab === "inbound" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                <PhoneCall className="w-4 h-4 text-cyan-400" />
                Simulate Citizen Emergency SMS Ingestion
              </h2>
              <p className="text-xs text-gray-400 mb-4">
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
                  className="text-[11px] px-2.5 py-1 rounded bg-[#1E293B] text-cyan-300 hover:bg-[#334155] border border-cyan-500/20"
                >
                  Preset: 6 Trapped Sector 4
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setInboundText("बाढ़ में 4 लोग फंसे हैं तुरंत नाव चाहिए सेक्टर 2 ब्रह्मपुत्र");
                    setInboundPhone("+919876543215");
                  }}
                  className="text-[11px] px-2.5 py-1 rounded bg-[#1E293B] text-purple-300 hover:bg-[#334155] border border-purple-500/20"
                >
                  Preset: Hindi Distress (4 लोग)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setInboundText("CRITICAL MEDICAL 2 INJURED GPS 26.1433, 91.7898 DISPUR CLINIC");
                    setInboundPhone("+919876543216");
                  }}
                  className="text-[11px] px-2.5 py-1 rounded bg-[#1E293B] text-amber-300 hover:bg-[#334155] border border-amber-500/20"
                >
                  Preset: GPS Coordinates
                </button>
              </div>

              <form onSubmit={handleInboundSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">Citizen Sender Phone Number</label>
                  <input
                    type="text"
                    value={inboundPhone}
                    onChange={(e) => setInboundPhone(e.target.value)}
                    className="w-full px-3 py-2 bg-[#070B13] border border-[#1E293B] rounded-lg text-sm text-white font-mono focus:border-cyan-500 focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">Inbound SMS Body (Unstructured Text)</label>
                  <textarea
                    rows={3}
                    value={inboundText}
                    onChange={(e) => setInboundText(e.target.value)}
                    className="w-full px-3 py-2 bg-[#070B13] border border-[#1E293B] rounded-lg text-sm text-white focus:border-cyan-500 focus:outline-none"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-300 mb-1">Gateway Channel</label>
                    <select
                      value={inboundGateway}
                      onChange={(e) => setInboundGateway(e.target.value)}
                      className="w-full px-3 py-2 bg-[#070B13] border border-[#1E293B] rounded-lg text-sm text-white focus:border-cyan-500 focus:outline-none"
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
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-2"
                >
                  <Send className={`w-4 h-4 ${isIngesting ? "animate-spin" : ""}`} />
                  {isIngesting ? "Ingesting & Parsing..." : "Ingest Citizen Emergency SMS"}
                </button>
              </form>
            </div>

            {/* Inbound Result Card */}
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                Live Incident Resolution & Auto-Reply Dispatch
              </h2>
              <p className="text-xs text-gray-400 mb-4">
                Shows parsed entities, calculated priority score, and the life-safety response SMS transmitted back to the citizen.
              </p>

              {inboundResult ? (
                <div className="space-y-4">
                  <div className="bg-[#070B13] p-4 rounded-xl border border-[#1E293B] space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-cyan-400 font-mono">
                        {inboundResult.local_reference}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30 font-bold">
                        P{inboundResult.priority_score.toFixed(0)} • {inboundResult.category}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-400">Location:</span>{" "}
                        <span className="text-white font-medium">{inboundResult.location_name}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Casualties:</span>{" "}
                        <span className="text-white font-medium">{inboundResult.people_at_risk} at Risk</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Coordinates:</span>{" "}
                        <span className="text-white font-mono">{inboundResult.latitude.toFixed(4)}, {inboundResult.longitude.toFixed(4)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Severity:</span>{" "}
                        <span className="text-amber-400 font-semibold">{inboundResult.severity}</span>
                      </div>
                    </div>
                  </div>

                  {/* Outbound SMS Text */}
                  <div className="bg-[#121826] border border-cyan-500/30 rounded-xl p-4">
                    <div className="flex items-center justify-between text-xs text-cyan-400 font-semibold mb-1">
                      <span>AUTOMATED LIFE-SAFETY SMS REPLY</span>
                      <span className="font-mono">{inboundResult.auto_reply_sms.length}/160 Chars</span>
                    </div>
                    <div className="text-xs text-gray-200 font-mono bg-[#070B13] p-3 rounded-lg border border-[#1E293B]">
                      "{inboundResult.auto_reply_sms}"
                    </div>
                    <div className="text-[11px] text-emerald-400 mt-2 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Dispatched via GSM Modem to {inboundResult.sender_phone}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center text-gray-500 text-xs text-center border border-dashed border-[#1E293B] rounded-xl">
                  <MessageSquare className="w-8 h-8 text-gray-600 mb-2" />
                  Submit an inbound SMS to inspect live entity extraction and auto-reply dispatch.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Sector Broadcast */}
        {activeTab === "broadcast" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                <Send className="w-4 h-4 text-cyan-400" />
                Dispatch Emergency Sector Broadcast
              </h2>
              <p className="text-xs text-gray-400 mb-4">
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
                  className="text-[11px] px-2.5 py-1 rounded bg-[#1E293B] text-cyan-300 hover:bg-[#334155] border border-cyan-500/20"
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
                  className="text-[11px] px-2.5 py-1 rounded bg-[#1E293B] text-amber-300 hover:bg-[#334155] border border-amber-500/20"
                >
                  Preset: Boil Water Advisory
                </button>
              </div>

              <form onSubmit={handleBroadcastSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">Target Geographic Sector</label>
                  <select
                    value={broadcastSector}
                    onChange={(e) => setBroadcastSector(e.target.value)}
                    className="w-full px-3 py-2 bg-[#070B13] border border-[#1E293B] rounded-lg text-sm text-white focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="Sector 4 - Guwahati Basin">Sector 4 - Guwahati Basin (High Risk)</option>
                    <option value="Sector 2 - Brahmaputra Flood Wall">Sector 2 - Flood Wall (Inundated)</option>
                    <option value="Sector 1 - Dispur Medical Center">Sector 1 - Dispur Center</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 mb-1">Hazard Title</label>
                  <input
                    type="text"
                    value={broadcastHazard}
                    onChange={(e) => setBroadcastHazard(e.target.value)}
                    className="w-full px-3 py-2 bg-[#070B13] border border-[#1E293B] rounded-lg text-sm text-white focus:border-cyan-500 focus:outline-none"
                    required
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-gray-300">Actionable Instruction</label>
                    <span className={`text-[11px] font-mono ${charCount <= 160 ? "text-emerald-400" : "text-red-400 font-bold"}`}>
                      {charCount}/160 Chars {charCount <= 160 ? "(1 Segment)" : "(Multi-part SMS)"}
                    </span>
                  </div>
                  <textarea
                    rows={3}
                    value={broadcastInstruction}
                    onChange={(e) => setBroadcastInstruction(e.target.value)}
                    className="w-full px-3 py-2 bg-[#070B13] border border-[#1E293B] rounded-lg text-sm text-white focus:border-cyan-500 focus:outline-none"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={isBroadcasting}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white font-bold text-sm shadow-lg shadow-red-500/20 transition-all flex items-center justify-center gap-2"
                >
                  <Send className={`w-4 h-4 ${isBroadcasting ? "animate-spin" : ""}`} />
                  {isBroadcasting ? "Broadcasting..." : "Broadcast Emergency SMS Alert"}
                </button>
              </form>
            </div>

            {/* Broadcast Result */}
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                Transmission Status & Cell Broadcast Ledger
              </h2>
              <p className="text-xs text-gray-400 mb-4">
                Verified delivery receipts and carrier queuing state across cellular towers.
              </p>

              {broadcastResult ? (
                <div className="space-y-4">
                  <div className="bg-[#070B13] p-4 rounded-xl border border-emerald-500/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        {broadcastResult.broadcast_id}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">
                        {broadcastResult.delivery_status}
                      </span>
                    </div>

                    <div className="text-xs text-gray-300 font-mono bg-[#121826] p-3 rounded-lg border border-[#1E293B]">
                      "{broadcastResult.primary_sms_text}"
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                      <div>Recipients Queued: <span className="text-white font-bold">{broadcastResult.recipients_queued} Phones</span></div>
                      <div>GSM Segment: <span className="text-emerald-400 font-bold">Single (160B)</span></div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex flex-col items-center justify-center text-gray-500 text-xs text-center border border-dashed border-[#1E293B] rounded-xl">
                  <Send className="w-8 h-8 text-gray-600 mb-2" />
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
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                <Satellite className="w-4 h-4 text-amber-400" />
                Satellite 140-Byte Burst Encoder
              </h2>
              <p className="text-xs text-gray-400 mb-4">
                Compresses incident envelopes into compact alphanumeric bursts for Iridium, Garmin inReach, or C-DOT satellite communicators with CRC-32 checksums.
              </p>

              <div className="grid grid-cols-2 gap-3 mb-3 text-xs">
                <div>
                  <label className="text-gray-400 block mb-1">Event ID</label>
                  <input
                    type="text"
                    value={satEventId}
                    onChange={(e) => setSatEventId(e.target.value)}
                    className="w-full px-2 py-1.5 bg-[#070B13] border border-[#1E293B] rounded font-mono text-white"
                  />
                </div>
                <div>
                  <label className="text-gray-400 block mb-1">Category</label>
                  <select
                    value={satCategory}
                    onChange={(e) => setSatCategory(e.target.value)}
                    className="w-full px-2 py-1.5 bg-[#070B13] border border-[#1E293B] rounded text-white"
                  >
                    <option value="RESCUE">RESCUE</option>
                    <option value="MEDICAL">MEDICAL</option>
                    <option value="HAZARD">HAZARD</option>
                    <option value="RELIEF">RELIEF</option>
                  </select>
                </div>
                <div>
                  <label className="text-gray-400 block mb-1">Severity</label>
                  <select
                    value={satSeverity}
                    onChange={(e) => setSatSeverity(e.target.value)}
                    className="w-full px-2 py-1.5 bg-[#070B13] border border-[#1E293B] rounded text-white"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                  </select>
                </div>
                <div>
                  <label className="text-gray-400 block mb-1">People at Risk</label>
                  <input
                    type="number"
                    value={satPeople}
                    onChange={(e) => setSatPeople(Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-[#070B13] border border-[#1E293B] rounded font-mono text-white"
                  />
                </div>
                <div>
                  <label className="text-gray-400 block mb-1">Latitude</label>
                  <input
                    type="number"
                    step="0.001"
                    value={satLat}
                    onChange={(e) => setSatLat(Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-[#070B13] border border-[#1E293B] rounded font-mono text-white"
                  />
                </div>
                <div>
                  <label className="text-gray-400 block mb-1">Longitude</label>
                  <input
                    type="number"
                    step="0.001"
                    value={satLon}
                    onChange={(e) => setSatLon(Number(e.target.value))}
                    className="w-full px-2 py-1.5 bg-[#070B13] border border-[#1E293B] rounded font-mono text-white"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="text-xs text-gray-400 block mb-1">Short Description (&le; 24 chars)</label>
                <input
                  type="text"
                  value={satDesc}
                  onChange={(e) => setSatDesc(e.target.value)}
                  className="w-full px-2 py-1.5 bg-[#070B13] border border-[#1E293B] rounded text-xs text-white"
                />
              </div>

              <button
                type="button"
                onClick={handleEncodeSatellite}
                className="w-full py-2 px-3 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow-md transition-all"
              >
                Encode Compact Satellite Burst
              </button>

              {encodedBurst && (
                <div className="mt-4 bg-[#070B13] p-3 rounded-lg border border-amber-500/30 text-xs font-mono space-y-1">
                  <div className="text-gray-400">WIRE STRING:</div>
                  <div className="text-amber-300 break-all select-all">{encodedBurst.burst_string}</div>
                  <div className="flex items-center justify-between text-[11px] text-gray-400 pt-2 border-t border-[#1E293B]">
                    <span>Length: {encodedBurst.byte_length} Bytes / 140B</span>
                    <span className="text-emerald-400 font-bold">CRC32: {encodedBurst.crc32_checksum}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Decoder */}
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6">
              <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                Satellite Burst Decoder & CRC Verification
              </h2>
              <p className="text-xs text-gray-400 mb-4">
                Validates and reconstitutes an incoming 140-byte satellite burst packet back into an operational event.
              </p>

              <div className="mb-4">
                <label className="text-xs text-gray-400 block mb-1">Satellite Wire Burst String</label>
                <textarea
                  rows={2}
                  value={decodeInput}
                  onChange={(e) => setDecodeInput(e.target.value)}
                  className="w-full px-3 py-2 bg-[#070B13] border border-[#1E293B] rounded-lg text-xs font-mono text-amber-300 focus:outline-none"
                />
              </div>

              <button
                type="button"
                onClick={handleDecodeSatellite}
                className="w-full py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md transition-all mb-4"
              >
                Decode & Verify Checksum
              </button>

              {decodedResult && (
                <div className="bg-[#070B13] p-4 rounded-lg border border-emerald-500/30 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white font-mono">{decodedResult.event_id}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${decodedResult.crc32_valid ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                      {decodedResult.crc32_valid ? "CRC-32 VALID" : "CRC-32 CORRUPTED"}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-gray-300">
                    <div>Category: <span className="text-cyan-400 font-bold">{decodedResult.category}</span></div>
                    <div>Severity: <span className="text-amber-400 font-bold">{decodedResult.severity}</span></div>
                    <div>Casualties: <span className="text-white font-bold">{decodedResult.people_at_risk}</span></div>
                    <div>Coordinates: <span className="text-white font-mono">{decodedResult.latitude}, {decodedResult.longitude}</span></div>
                  </div>

                  <div className="pt-2 border-t border-[#1E293B] text-gray-400">
                    Description: <span className="text-gray-200">{decodedResult.short_desc}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 4: Logs */}
        {activeTab === "logs" && (
          <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-white">Transmission Audit Ledger</h2>
                <p className="text-xs text-gray-400">Complete log of inbound citizen SOS, outbound replies, and broadcasts.</p>
              </div>
              <button
                onClick={fetchLogs}
                disabled={isLoadingLogs}
                className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingLogs ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>

            {logs.length === 0 ? (
              <div className="py-12 text-center text-gray-500 text-xs">No transmissions recorded yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#070B13] text-gray-400 border-b border-[#1E293B]">
                    <tr>
                      <th className="p-2.5">Time</th>
                      <th className="p-2.5">Direction</th>
                      <th className="p-2.5">Phone / Recipient</th>
                      <th className="p-2.5">Message Content</th>
                      <th className="p-2.5">Reference</th>
                      <th className="p-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1E293B]">
                    {logs.map((log) => (
                      <tr key={log.id} className="hover:bg-[#121826]">
                        <td className="p-2.5 text-gray-400 whitespace-nowrap font-mono text-[11px]">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="p-2.5">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              log.direction === "INBOUND"
                                ? "bg-cyan-500/20 text-cyan-400"
                                : log.direction === "BROADCAST"
                                ? "bg-amber-500/20 text-amber-400"
                                : "bg-emerald-500/20 text-emerald-400"
                            }`}
                          >
                            {log.direction}
                          </span>
                        </td>
                        <td className="p-2.5 font-mono text-gray-300">{log.sender_or_recipient}</td>
                        <td className="p-2.5 max-w-md truncate text-gray-200 font-mono text-[11px]">{log.text}</td>
                        <td className="p-2.5 text-gray-400 font-mono text-[11px]">{log.related_ref || "-"}</td>
                        <td className="p-2.5">
                          <span className="text-emerald-400 text-[10px] font-semibold">{log.status}</span>
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
