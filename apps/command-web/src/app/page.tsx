"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  AlertTriangle,
  Radio,
  MapPin,
  CheckCircle2,
  Users,
  Clock,
  FileCheck,
  RotateCcw,
  Navigation,
  ChevronRight,
  Camera,
  Flame,
  Droplets,
  HelpCircle,
  Lock,
  ArrowRight
} from "lucide-react";

export default function CommandCenter() {
  // State for tabs and interactive demo controls
  const [selectedIncident, setSelectedIncident] = useState<string | null>("INC-01");
  const [conflictResolved, setConflictResolved] = useState<boolean>(false);
  const [resolutionReason, setResolutionReason] = useState<string>(
    "Drone aerial survey & volunteer ground reports confirm bridge railing collapse under 4ft flood surge. Route-88 closed."
  );
  const [activeTab, setActiveTab] = useState<"cop" | "conflicts" | "evidence" | "audit">("cop");

  // Simulated live state
  const [incidents, setIncidents] = useState([
    {
      id: "INC-01",
      localRef: "INC-SECTOR4-991",
      title: "3 Stranded Civilians on Rooftop",
      category: "RESCUE",
      severity: "CRITICAL",
      priorityScore: 92.4,
      peopleAtRisk: 3,
      location: "Sector 4 Bridge, Brahmaputra Basin",
      status: "IN_PROGRESS",
      assignedTo: "Vikram Singh (SDRF Team Lead)",
      routeId: "ROUTE-88",
      isRouteBlocked: !conflictResolved,
      breakdown: {
        severity: 24.0,
        people: 18.5,
        urgency: 15.0,
        category: 15.0,
        confidence: 19.9,
      }
    },
    {
      id: "INC-02",
      localRef: "INC-WARD2-104",
      title: "Drinking Water Contamination in Relief Camp",
      category: "SUPPLY",
      severity: "HIGH",
      priorityScore: 78.1,
      peopleAtRisk: 45,
      location: "Relief Camp #3, North Guwahati",
      status: "TRIAGED",
      assignedTo: "Unassigned",
      routeId: "ROUTE-12",
      isRouteBlocked: false,
      breakdown: {
        severity: 20.0,
        people: 22.0,
        urgency: 12.0,
        category: 10.0,
        confidence: 14.1,
      }
    },
    {
      id: "INC-03",
      localRef: "INC-MED-808",
      title: "Elderly Diabetic Patient Insulin Depletion",
      category: "MEDICAL",
      severity: "MEDIUM",
      priorityScore: 64.5,
      peopleAtRisk: 1,
      location: "House 42, Ward 9",
      status: "REPORTED",
      assignedTo: "Unassigned",
      routeId: "ROUTE-04",
      isRouteBlocked: false,
      breakdown: {
        severity: 15.0,
        people: 5.0,
        urgency: 15.0,
        category: 15.0,
        confidence: 14.5,
      }
    }
  ]);

  const [auditLogs, setAuditLogs] = useState([
    {
      id: "aud-01",
      time: "21:10:04",
      actor: "Citizen Das (citizen-device-alpha)",
      action: "OFFLINE_REPORT_COMMITTED",
      details: "Incident INC-01 saved locally in SQLite outbox with photo evidence.",
      type: "info"
    },
    {
      id: "aud-02",
      time: "21:12:30",
      actor: "Sync Gateway",
      action: "CAUSAL_DELTA_SYNC_ACCEPTED",
      details: "Batch of 1 events ingested with idempotency key validation.",
      type: "success"
    },
    {
      id: "aud-03",
      time: "21:14:12",
      actor: "Commander Sharma (SUPERVISOR)",
      action: "TASK_ASSIGNED",
      details: "Assigned Evacuate Task on ROUTE-88 to Vikram Singh (SDRF).",
      type: "info"
    },
    {
      id: "aud-04",
      time: "21:15:00",
      actor: "Domain Conflict Engine",
      action: "PROTECTED_CONFLICT_FREEZE",
      details: "Concurrent contradiction detected on ROUTE-88: Device A (USABLE) vs Device B (BLOCKED). State set to UNCERTAIN. Automation frozen.",
      type: "danger"
    }
  ]);

  const handleResolveConflict = () => {
    setConflictResolved(true);
    setAuditLogs(prev => [
      {
        id: `aud-${Date.now()}`,
        time: new Date().toLocaleTimeString(),
        actor: "Commander Sharma (SUPERVISOR)",
        action: "CONFLICT_ADJUDICATED_RESOLVED",
        details: `Adjudicated ROUTE-88 to BLOCKED. Reason: ${resolutionReason}`,
        type: "success"
      },
      ...prev
    ]);
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#0B0F19] text-slate-100">
      {/* Top Ambient Navigation & State Banner */}
      <header className="border-b border-slate-800 bg-[#0F172A]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-black text-xl shadow-[0_0_20px_rgba(59,130,246,0.25)]">
            SV
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                ShiVi Command Center
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-mono font-medium border border-blue-500/30">
                  v3.0 EOC
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              Assam State Disaster Management Authority (ASDMA) • District 01 Flood Response
            </p>
          </div>
        </div>

        {/* Global Live Status Badges */}
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 bg-slate-900/80 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-slate-400">Causal Sync:</span>
            <span className="text-emerald-400 font-semibold">ONLINE (0 PENDING)</span>
          </div>

          <div className="flex items-center gap-2">
            {!conflictResolved ? (
              <div className="flex items-center gap-2 bg-rose-500/10 border border-rose-500/30 text-rose-400 px-3 py-1.5 rounded-lg text-xs font-semibold animate-pulse">
                <AlertTriangle className="h-4 w-4" />
                <span>1 LIFE-SAFETY CONFLICT OPEN</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-3 py-1.5 rounded-lg text-xs font-semibold">
                <CheckCircle2 className="h-4 w-4" />
                <span>ALL CONFLICTS ADJUDICATED</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Primary 3-Column Layout */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 max-w-[1920px] mx-auto w-full">
        {/* LEFT COLUMN: Explainable Priority Queue (Col 3) */}
        <section className="lg:col-span-3 flex flex-col gap-4">
          <div className="bg-[#121826] border border-slate-800 rounded-xl p-4 flex flex-col h-full shadow-lg">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Flame className="h-4 w-4 text-orange-400" />
                Priority Incident Queue
              </h2>
              <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                {incidents.length} Active
              </span>
            </div>

            <div className="flex flex-col gap-3 overflow-y-auto pr-1">
              {incidents.map((inc) => (
                <div
                  key={inc.id}
                  onClick={() => setSelectedIncident(inc.id)}
                  className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
                    selectedIncident === inc.id
                      ? "bg-blue-950/40 border-blue-500/60 shadow-[0_0_15px_rgba(59,130,246,0.15)]"
                      : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <span className="text-xs font-mono text-slate-400">{inc.localRef}</span>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${
                          inc.severity === "CRITICAL"
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                            : inc.severity === "HIGH"
                            ? "bg-orange-500/20 text-orange-400 border border-orange-500/40"
                            : "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        }`}
                      >
                        {inc.severity}
                      </span>
                      <span className="text-xs font-bold font-mono text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded">
                        {inc.priorityScore}
                      </span>
                    </div>
                  </div>

                  <h3 className="text-sm font-semibold text-white line-clamp-1">{inc.title}</h3>
                  <p className="text-xs text-slate-400 flex items-center gap-1 mt-1">
                    <MapPin className="h-3 w-3 text-slate-500" />
                    {inc.location}
                  </p>

                  <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-400 flex items-center gap-1">
                      <Users className="h-3 w-3 text-slate-500" />
                      {inc.peopleAtRisk} Stranded
                    </span>
                    <span
                      className={`font-mono text-[11px] font-semibold ${
                        inc.isRouteBlocked ? "text-rose-400" : "text-emerald-400"
                      }`}
                    >
                      {inc.isRouteBlocked ? "⚠️ Route Frozen" : "✓ Active"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CENTER COLUMN: Common Operational Picture & Map / Conflict Adjudication (Col 6) */}
        <section className="lg:col-span-6 flex flex-col gap-4">
          {/* Navigation Sub-Tabs */}
          <div className="flex items-center gap-2 bg-[#121826] p-1.5 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab("cop")}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                activeTab === "cop"
                  ? "bg-blue-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Navigation className="h-3.5 w-3.5" />
              Common Operational Map
            </button>
            <button
              onClick={() => setActiveTab("conflicts")}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                activeTab === "conflicts"
                  ? "bg-rose-600 text-white shadow animate-pulse"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Conflict Review ({conflictResolved ? "0" : "1"})
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                activeTab === "audit"
                  ? "bg-slate-700 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileCheck className="h-3.5 w-3.5" />
              Audit Ledger
            </button>
          </div>

          {/* TAB 1: COP Geospatial Simulation View */}
          {activeTab === "cop" && (
            <div className="bg-[#121826] border border-slate-800 rounded-xl p-4 flex-1 flex flex-col min-h-[460px] shadow-lg relative overflow-hidden">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-blue-500 animate-ping"></span>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Brahmaputra Basin Live Sector Map
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-slate-400">MapLibre GL Vector Engine</span>
              </div>

              {/* Map Canvas Mock with Real Coordinates & Polygons */}
              <div className="flex-1 bg-slate-950 rounded-lg border border-slate-800 relative flex items-center justify-center overflow-hidden p-6">
                <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px]"></div>

                {/* Flood Zone Polygon */}
                <div className="absolute top-1/4 left-1/4 w-72 h-48 bg-blue-500/10 border border-blue-400/30 rounded-3xl -rotate-6 flex items-center justify-center">
                  <span className="text-[10px] font-mono font-bold text-blue-300 uppercase tracking-widest bg-blue-950/80 px-2 py-0.5 rounded border border-blue-500/30">
                    Flood Inundation Level 3 (NDEM)
                  </span>
                </div>

                {/* Route-88 Path Visualization */}
                <div className="absolute top-1/2 left-10 right-10 h-1.5 bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 opacity-60"></div>

                {/* Incident Marker (Sector 4) */}
                <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-10">
                  <div className="p-2 rounded-full bg-rose-600 text-white shadow-[0_0_20px_rgba(225,29,72,0.6)] animate-bounce">
                    <AlertTriangle className="h-5 w-5" />
                  </div>
                  <div className="mt-1 bg-slate-900/90 border border-slate-700 px-2.5 py-1 rounded text-center backdrop-blur shadow">
                    <p className="text-[11px] font-bold text-white">INC-01: 3 People Stranded</p>
                    <p className="text-[9px] text-slate-400 font-mono">26.1856° N, 91.7483° E</p>
                  </div>
                </div>

                {/* Route-88 Hazard Status Overlay Banner */}
                <div className="absolute bottom-4 left-4 right-4 bg-slate-900/95 border border-slate-800 p-3 rounded-lg flex items-center justify-between backdrop-blur">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-lg ${
                        conflictResolved
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : "bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse"
                      }`}
                    >
                      <AlertTriangle className="h-4 w-4" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white flex items-center gap-2">
                        Arterial Route-88 Status:{" "}
                        <span
                          className={`font-mono ${
                            conflictResolved ? "text-rose-400" : "text-amber-400"
                          }`}
                        >
                          {conflictResolved ? "CONFIRMED BLOCKED" : "UNCERTAIN (CONFLICT PENDING)"}
                        </span>
                      </h4>
                      <p className="text-[11px] text-slate-400">
                        {conflictResolved
                          ? "Alternate Sector 4 Boat Ramp deployed. Traffic restricted."
                          : "Concurrent updates from Device A & B. Automation frozen."}
                      </p>
                    </div>
                  </div>

                  {!conflictResolved && (
                    <button
                      onClick={() => setActiveTab("conflicts")}
                      className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-all shadow"
                    >
                      Review Conflict →
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Protected Conflict Adjudication Panel */}
          {activeTab === "conflicts" && (
            <div className="bg-[#121826] border border-rose-900/50 rounded-xl p-5 flex-1 flex flex-col shadow-xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-rose-500" />
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      Life-Safety Conflict Adjudication (Case #CF-ROUTE88)
                    </h3>
                    <p className="text-xs text-slate-400">
                      Entity: <span className="font-mono text-slate-200">ROUTE-88</span> • Field:{" "}
                      <span className="font-mono text-slate-200">status</span>
                    </p>
                  </div>
                </div>
                <span
                  className={`text-xs font-mono font-bold px-2.5 py-1 rounded ${
                    conflictResolved
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                      : "bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse"
                  }`}
                >
                  {conflictResolved ? "STATUS: RESOLVED" : "STATUS: OPEN & FROZEN"}
                </span>
              </div>

              {/* Contradictory Claims Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
                {/* Claim A */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3.5 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-mono text-slate-400">Claim 1 (Device A)</span>
                      <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                        VALUE: USABLE
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-medium">Actor: Vikram Singh (SDRF Lead)</p>
                    <p className="text-[11px] text-slate-500 font-mono">Time: 21:14:20 UTC • Seq: #10</p>
                    <div className="mt-3 p-2 bg-slate-950 rounded border border-slate-800 flex items-center gap-2 text-xs text-slate-400">
                      <Camera className="h-4 w-4 text-blue-400" />
                      <span>Photo Attached (SHA-256 Verified)</span>
                    </div>
                  </div>
                </div>

                {/* Claim B */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3.5 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-mono text-slate-400">Claim 2 (Device B)</span>
                      <span className="text-xs font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30">
                        VALUE: BLOCKED
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 font-medium">Actor: Ananya Das (Ward Volunteer)</p>
                    <p className="text-[11px] text-slate-500 font-mono">Time: 21:14:48 UTC • Seq: #5</p>
                    <div className="mt-3 p-2 bg-slate-950 rounded border border-slate-800 text-xs text-slate-400">
                      Note: "Bridge railing submerged in 4ft water flow"
                    </div>
                  </div>
                </div>
              </div>

              {/* Supervisor Resolution Form */}
              <div className="mt-auto pt-3 border-t border-slate-800 flex flex-col gap-3">
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Mandatory Operational Justification (Logged to Immutable Audit)
                </label>
                <textarea
                  value={resolutionReason}
                  onChange={(e) => setResolutionReason(e.target.value)}
                  disabled={conflictResolved}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 resize-none h-16"
                />

                <div className="flex items-center justify-end gap-3">
                  {!conflictResolved ? (
                    <>
                      <button
                        onClick={handleResolveConflict}
                        className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs px-4 py-2 rounded-lg transition-all shadow-[0_0_15px_rgba(225,29,72,0.3)] flex items-center gap-2"
                      >
                        <Lock className="h-3.5 w-3.5" />
                        Authorize Status: BLOCKED (Declare Impassable)
                      </button>
                    </>
                  ) : (
                    <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 rounded-lg">
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Resolution Synced to All Field Devices</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Immutable Audit Timeline */}
          {activeTab === "audit" && (
            <div className="bg-[#121826] border border-slate-800 rounded-xl p-5 flex-1 flex flex-col shadow-lg">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <FileCheck className="h-4 w-4 text-blue-400" />
                  Cryptographic Audit Trail
                </h3>
                <span className="text-[11px] font-mono text-slate-500">Append-Only Ledger</span>
              </div>

              <div className="flex flex-col gap-2.5 overflow-y-auto max-h-[380px] pr-1">
                {auditLogs.map((log) => (
                  <div
                    key={log.id}
                    className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg text-xs flex flex-col gap-1"
                  >
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className="text-slate-400">{log.time}</span>
                      <span className="text-blue-400 font-bold">{log.action}</span>
                    </div>
                    <p className="text-slate-200 font-medium">{log.details}</p>
                    <p className="text-[10px] text-slate-500 font-mono">Actor: {log.actor}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* RIGHT COLUMN: Explainable Breakdown & Verification Gates (Col 3) */}
        <section className="lg:col-span-3 flex flex-col gap-4">
          <div className="bg-[#121826] border border-slate-800 rounded-xl p-4 flex flex-col h-full shadow-lg">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <HelpCircle className="h-4 w-4 text-blue-400" />
              Explainable Triage Model
            </h2>

            {/* Explainable Factor Breakdown */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 flex flex-col gap-2.5 mb-4">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 font-medium">Multi-Factor Score</span>
                <span className="font-bold font-mono text-blue-400 text-sm">92.4 / 100</span>
              </div>

              <div className="flex flex-col gap-1.5 text-[11px]">
                <div className="flex justify-between text-slate-400">
                  <span>Severity (Critical)</span>
                  <span className="font-mono text-slate-200">24.0 / 30</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-rose-500 h-full w-[80%]"></div>
                </div>

                <div className="flex justify-between text-slate-400 mt-1">
                  <span>People at Risk (3)</span>
                  <span className="font-mono text-slate-200">18.5 / 25</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-orange-500 h-full w-[74%]"></div>
                </div>

                <div className="flex justify-between text-slate-400 mt-1">
                  <span>Urgency Window (&lt;1h)</span>
                  <span className="font-mono text-slate-200">15.0 / 15</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-amber-500 h-full w-[100%]"></div>
                </div>
              </div>
            </div>

            {/* Task Verification Gate */}
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <FileCheck className="h-3.5 w-3.5 text-emerald-400" />
              Supervisor Verification Gate
            </h3>

            <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 flex flex-col gap-2.5 text-xs">
              <p className="text-slate-300 font-semibold">Evacuation Task Verification</p>
              <div className="flex items-center gap-2 text-[11px] text-slate-400">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                <span>Rescue Photo Uploaded (SHA-256 Check Passed)</span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-slate-400">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                <span>3 Civilians Admitted to Camp 4</span>
              </div>

              <button
                disabled={!conflictResolved}
                className={`mt-2 py-2 px-3 rounded-lg font-bold text-xs flex items-center justify-center gap-2 transition-all ${
                  conflictResolved
                    ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)] cursor-pointer"
                    : "bg-slate-800 text-slate-500 cursor-not-allowed"
                }`}
              >
                <CheckCircle2 className="h-4 w-4" />
                Authorize & Verify Task Closure
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
