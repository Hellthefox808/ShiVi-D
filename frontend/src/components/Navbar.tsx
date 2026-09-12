/**
 * ShiVi Operations Console - Tactical Header & Mission Bar
 * ==========================================================
 *
 * Briefing:
 *     Top navigation bar (`Navbar`) for the ShiVi Common Operational Picture (COP).
 *     Houses platform identity, backend live connection health indicator, multi-bearer network mode
 *     selector (Cellular/Cloud, BLE Mesh, Blackout), quick links to the SMS gateway, AI advisor drawer toggle,
 *     and the scenario-based disaster drill simulation menu.
 *
 * Reason:
 *     During emergency coordination, the operator needs instant visibility into whether the dashboard
 *     is receiving live telemetry or operating from local cache, the ability to test multi-bearer failovers,
 *     and one-click initiation of scenario drills across different disaster dynamics.
 */

"use client";

import React from "react";
import Link from "next/link";
import {
  Shield,
  Radio,
  Wifi,
  WifiOff,
  Play,
  RotateCcw,
  Sparkles,
  Layers,
  MessageSquare,
  ChevronDown,
} from "lucide-react";

/**
 * Briefing:
 *     Component properties controlling navigation bar state and drill handlers.
 */
interface NavbarProps {
  // Explanation: True if the backend FastAPI /health probe succeeds; false if in standalone fallback.
  backendConnected: boolean;
  // Explanation: Currently selected network bearer simulation mode.
  connectivityMode: "cloud" | "mesh" | "offline";
  // Explanation: Callback invoked when changing active connectivity mode.
  onConnectivityChange: (mode: "cloud" | "mesh" | "offline") => void;
  // Explanation: Trigger for the default P0 flash flood simulation drill.
  onRunSimulation: () => void;
  // Explanation: Handler resetting database state to initial conditions.
  onResetState: () => void;
  // Explanation: Handler opening/closing the NDMA AI SOP Advisory drawer.
  onToggleAiDrawer: () => void;
  // Explanation: Boolean flag indicating if a simulation drill is actively running.
  isSimulating: boolean;
  // Explanation: Optional handler to run a specific disaster scenario by ID.
  onRunScenario?: (scenarioId: string) => void;
}

/**
 * Briefing:
 *     Tactical header component providing mission status indicators and drill triggers.
 *
 * Reason:
 *     Acts as the command anchor across all subviews. Features a sticky top-bar with
 *     backdrop blur to remain accessible while scrolling through dense incident and task feeds.
 *
 * @param props Configuration and action handler properties.
 */
export function Navbar({
  backendConnected,
  connectivityMode,
  onConnectivityChange,
  onRunSimulation,
  onResetState,
  onToggleAiDrawer,
  isSimulating,
  onRunScenario,
}: NavbarProps) {
  // Explanation: Local state toggling the scenario drill selection dropdown menu.
  const [showDrillMenu, setShowDrillMenu] = React.useState(false);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 lg:px-8 py-3 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Logo & Platform Info */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 via-orange-500 to-yellow-400 p-[2px] shadow-md shadow-amber-500/20">
            <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center">
              <Shield className="w-5 h-5 text-amber-600" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black tracking-wider text-slate-900">SHIVI</h1>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                शिवी • IOC v1.0
              </span>
              <span
                className={`flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full border ${
                  backendConnected
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold"
                    : "bg-amber-50 text-amber-800 border-amber-200 font-semibold"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    backendConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
                  }`}
                />
                {backendConnected ? "LIVE CORE API" : "STANDALONE CACHE"}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 hidden sm:block font-medium">
              Local-First Disaster Coordination & Common Operational Picture (COP)
            </p>
          </div>
        </div>

        {/* Multi-Bearer Mesh & Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Bearer Connectivity Selector */}
          <div className="flex items-center bg-slate-100 border border-slate-200 rounded-xl p-1 text-xs">
            <button
              onClick={() => onConnectivityChange("cloud")}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg transition-all ${
                connectivityMode === "cloud"
                  ? "bg-white text-amber-900 font-bold shadow-sm border border-amber-200"
                  : "text-slate-600 hover:text-slate-900"
              }`}
              title="Full Cellular 4G/5G and Cloud Connectivity"
            >
              <Wifi className="w-3.5 h-3.5 text-amber-600" />
              <span className="hidden md:inline">Cellular / Cloud</span>
            </button>
            <button
              onClick={() => onConnectivityChange("mesh")}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg transition-all ${
                connectivityMode === "mesh"
                  ? "bg-white text-orange-900 font-bold shadow-sm border border-orange-200"
                  : "text-slate-600 hover:text-slate-900"
              }`}
              title="Offline BLE 5.0 & Wi-Fi Direct Mesh Gossip"
            >
              <Radio className="w-3.5 h-3.5 text-orange-600" />
              <span className="hidden md:inline">BLE Mesh</span>
            </button>
            <button
              onClick={() => onConnectivityChange("offline")}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg transition-all ${
                connectivityMode === "offline"
                  ? "bg-red-600 text-white font-bold shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
              title="Radio Blackout: Local SQLite Outbox Storage"
            >
              <WifiOff className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Blackout</span>
            </button>
          </div>

          {/* SMS Gateway Link */}
          <Link
            href="/sms"
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 transition-all shadow-sm"
            title="Emergency SMS & Satellite Broadcast Gateway"
          >
            <MessageSquare className="w-3.5 h-3.5 text-amber-600" />
            <span className="hidden sm:inline">SMS Gateway</span>
          </Link>

          {/* AI Advisory Drawer Button */}
          <button
            onClick={onToggleAiDrawer}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span className="hidden sm:inline">AI Advisor</span>
          </button>

          {/* Reset Demo State Button */}
          <button
            onClick={onResetState}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-white text-slate-700 border border-slate-200 hover:bg-slate-100 transition-all shadow-sm"
            title="Reset database to fresh default accounts"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            <span className="hidden sm:inline">Reset</span>
          </button>

          {/* Run Live P0 Disaster Simulation Button Group */}
          <div className="relative flex items-center shadow-sm">
            <button
              onClick={onRunSimulation}
              disabled={isSimulating}
              className={`flex items-center gap-2 text-xs font-bold px-3.5 py-2 rounded-l-xl transition-all ${
                isSimulating
                  ? "bg-amber-100 text-amber-800 cursor-not-allowed opacity-75"
                  : "bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 shadow-sm active:scale-95"
              }`}
              title="Run P0 Disaster Loop (Flash Flood & Route-88 Safety Freeze)"
            >
              <Play className={`w-3.5 h-3.5 fill-current ${isSimulating ? "animate-spin" : ""}`} />
              <span>{isSimulating ? "Simulating..." : "Run Drill"}</span>
            </button>
            <button
              onClick={() => setShowDrillMenu(!showDrillMenu)}
              disabled={isSimulating}
              className={`px-2 py-2 rounded-r-xl border-l border-amber-400/50 text-slate-950 font-bold transition-all ${
                isSimulating
                  ? "bg-amber-100 text-amber-800 cursor-not-allowed opacity-75"
                  : "bg-orange-500 hover:bg-orange-400"
              }`}
              title="Select Specific Disaster Drill Scenario"
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {/* Dropdown Menu */}
            {showDrillMenu && (
              <div className="absolute right-0 top-full mt-2 w-72 bg-white border border-slate-200 rounded-xl shadow-xl p-2 z-50 animate-in fade-in zoom-in-95">
                <span className="text-[10px] text-slate-500 uppercase font-mono px-2.5 py-1 block font-semibold">
                  Select Disaster Drill Scenario
                </span>
                <button
                  onClick={() => {
                    setShowDrillMenu(false);
                    if (onRunScenario) {
                      onRunScenario("scenario-flood-contradiction");
                    } else {
                      onRunSimulation();
                    }
                  }}
                  className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-amber-50 text-xs flex flex-col gap-0.5 transition-all"
                >
                  <span className="font-bold text-amber-700">1. Flash Flood & Route Freeze</span>
                  <span className="text-[11px] text-slate-500">Contradiction, Safety Freeze & Supervisor Adjudication</span>
                </button>
                <button
                  onClick={() => {
                    setShowDrillMenu(false);
                    if (onRunScenario) {
                      onRunScenario("scenario-asset-contention");
                    } else {
                      onRunSimulation();
                    }
                  }}
                  className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-orange-50 text-xs flex flex-col gap-0.5 transition-all"
                >
                  <span className="font-bold text-orange-700">2. Asset Contention & NFC Lease</span>
                  <span className="text-[11px] text-slate-500">Multi-Team USAR Cutter Contention & Zero Deadlock</span>
                </button>
                <button
                  onClick={() => {
                    setShowDrillMenu(false);
                    if (onRunScenario) {
                      onRunScenario("scenario-replay-attack");
                    } else {
                      onRunSimulation();
                    }
                  }}
                  className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-red-50 text-xs flex flex-col gap-0.5 transition-all"
                >
                  <span className="font-bold text-red-700">3. Adversarial Poison & Anti-Replay</span>
                  <span className="text-[11px] text-slate-500">Tampered Packet Detection & Nonce Replay Drop</span>
                </button>
                <button
                  onClick={() => {
                    setShowDrillMenu(false);
                    if (onRunScenario) {
                      onRunScenario("scenario-sms-triage");
                    } else {
                      onRunSimulation();
                    }
                  }}
                  className="w-full text-left px-2.5 py-2 rounded-lg hover:bg-emerald-50 text-xs flex flex-col gap-0.5 transition-all"
                >
                  <span className="font-bold text-emerald-700">4. Multilingual SMS Triage</span>
                  <span className="text-[11px] text-slate-500">Austere Ingestion, NLP Entity Extraction & Task Dispatch</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
