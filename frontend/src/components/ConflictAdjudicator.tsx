/**
 * ShiVi Operations Console - Causal Conflict Adjudication Studio
 * ===============================================================
 *
 * Briefing:
 *     Human supervisor adjudication panel (`ConflictAdjudicator`) enforcing the ShiVi
 *     "Causal Safety Freeze" invariant. When field teams operating asynchronously over degraded
 *     mesh links report conflicting ground-truth observations on life-safety entities (such as
 *     Route 101 being USABLE vs BLOCKED), automatic reconciliation is halted.
 *     This component provides:
 *     - Real-time contradiction queue displaying open vs resolved safety freezes.
 *     - Side-by-side comparison of competing field claims (actor ID, device ID, timestamp, notes, photos).
 *     - Visibility into dependent operational tasks that are currently suspended to protect human lives.
 *     - Authoritative adjudication form requiring human justification recorded in the immutable audit ledger.
 *
 * Reason:
 *     In disaster search-and-rescue, algorithmic arbitration (such as Last-Write-Wins or vector clocks alone)
 *     is fatal if an outdated observation silences an alert about a collapsed bridge. The ConflictAdjudicator
 *     keeps human commanders in the loop, guaranteeing that safety freezes are only unlocked by certified
 *     supervisors with documented rationales.
 */

"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  Lock,
  Unlock,
  CheckCircle2,
  Camera,
  FileText,
  Clock,
  UserCheck,
  ShieldAlert,
} from "lucide-react";
import { ConflictCaseItem } from "../services/api";

/**
 * Briefing:
 *     Component properties controlling the adjudication queue and resolution handler.
 */
interface ConflictAdjudicatorProps {
  // Explanation: List of active and historical conflict cases fetched from /v1/conflicts.
  conflicts: ConflictCaseItem[];
  // Explanation: Callback invoking /v1/conflicts/{id}/resolve with chosen canonical value and rationale.
  onResolve: (conflictId: string, value: string, reason: string) => Promise<void>;
  // Explanation: Optional callback to trigger a live route contradiction for testing and drills.
  onTriggerDispute?: () => Promise<void>;
  // Explanation: True while asynchronous adjudication is being committed to backend storage.
  isResolving: boolean;
}

export function ConflictAdjudicator({
  conflicts,
  onResolve,
  onTriggerDispute,
  isResolving,
}: ConflictAdjudicatorProps) {
  // Explanation: Filter toggle between OPEN freezes and historical resolutions.
  const [filterMode, setFilterMode] = useState<"OPEN" | "ALL">("OPEN");
  // Explanation: True while trigger dispute request is processing.
  const [isTriggering, setIsTriggering] = useState<boolean>(false);

  const displayedConflicts =
    filterMode === "OPEN"
      ? conflicts.filter((c) => c.status === "OPEN")
      : conflicts;

  // Explanation: Currently selected conflict case UUID for detailed inspection.
  const [selectedConflictId, setSelectedConflictId] = useState<string | null>(
    displayedConflicts.length > 0 ? displayedConflicts[0].id : (conflicts.length > 0 ? conflicts[0].id : null)
  );

  // Explanation: Ensure selected conflict synchronizes whenever conflicts or filter mode updates.
  React.useEffect(() => {
    if (displayedConflicts.length > 0) {
      if (!selectedConflictId || !displayedConflicts.some((c) => c.id === selectedConflictId)) {
        setSelectedConflictId(displayedConflicts[0].id);
      }
    } else if (conflicts.length > 0) {
      if (!selectedConflictId || !conflicts.some((c) => c.id === selectedConflictId)) {
        setSelectedConflictId(conflicts[0].id);
      }
    } else {
      setSelectedConflictId(null);
    }
  }, [conflicts, displayedConflicts, selectedConflictId]);

  // Explanation: Authoritative state value chosen by supervisor ('BLOCKED' or 'USABLE').
  const [resolvedValue, setResolvedValue] = useState<string>("BLOCKED");
  // Explanation: Mandatory operational justification string entered by the commander.
  const [reason, setReason] = useState<string>(
    "Drone aerial survey & volunteer ground reports confirm bridge railing collapse under 4ft flood surge. Route-88 closed."
  );

  // Explanation: Finds the active conflict case object matching selectedConflictId.
  const activeConflict =
    conflicts.find((c) => c.id === selectedConflictId) || displayedConflicts[0] || conflicts[0] || null;

  /**
   * Briefing:
   *     Submits authoritative resolution to backend adjudication endpoint.
   */
  const handleResolveClick = async () => {
    if (!activeConflict) return;
    await onResolve(activeConflict.id, resolvedValue, reason);
  };

  const handleTriggerClick = async () => {
    if (!onTriggerDispute) return;
    setIsTriggering(true);
    try {
      await onTriggerDispute();
      setFilterMode("OPEN");
    } finally {
      setIsTriggering(false);
    }
  };

  const openCount = conflicts.filter((c) => c.status === "OPEN").length;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#111318] border border-amber-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">
                  Causal Conflict Engine & Safety Freeze Studio
                </h3>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1">
                  <Lock className="w-3 h-3" /> ZERO SILENT OVERWRITES
                </span>
              </div>
              <p className="text-xs text-gray-400 max-w-2xl">
                When disconnected mesh nodes submit contradictory life-safety observations, Last-Write-Wins (LWW) is
                strictly prohibited. Dependent dispatch tasks are automatically frozen until human adjudication.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleTriggerClick}
              disabled={isTriggering}
              className="px-3.5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-amber-500/20 disabled:opacity-50"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{isTriggering ? "Triggering..." : "+ Simulate Field Contradiction"}</span>
            </button>
            <div className="text-right pl-3 border-l border-[#222634]">
              <span className="text-[11px] text-gray-400 uppercase font-semibold block">Active Freezes</span>
              <span className="text-2xl font-black text-red-400">
                {openCount}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-[#222634] pb-2 text-xs font-bold">
        <button
          onClick={() => setFilterMode("OPEN")}
          className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
            filterMode === "OPEN"
              ? "bg-red-500/20 text-red-400 border border-red-500/40"
              : "text-gray-400 hover:text-white"
          }`}
        >
          <Lock className="w-3.5 h-3.5" />
          <span>Active Safety Freezes ({openCount})</span>
        </button>
        <button
          onClick={() => setFilterMode("ALL")}
          className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
            filterMode === "ALL"
              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
              : "text-gray-400 hover:text-white"
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>All Cases / Audit History ({conflicts.length})</span>
        </button>
      </div>

      {displayedConflicts.length === 0 ? (
        <div className="bg-[#111318] border border-[#222634] rounded-2xl p-12 text-center space-y-4">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
          <h4 className="text-base font-bold text-white">No Active Contradictions in this View</h4>
          <p className="text-xs text-gray-400 max-w-md mx-auto">
            All mesh nodes have converged. You can click "+ Simulate Field Contradiction" to generate a live life-safety dispute on Route-88 for supervisor adjudication testing.
          </p>
          {onTriggerDispute && (
            <button
              onClick={handleTriggerClick}
              disabled={isTriggering}
              className="px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs inline-flex items-center gap-2 transition-all shadow-md shadow-amber-500/20"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>Simulate Route-88 Contradiction Now</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Conflict Cases List */}
          <div className="bg-[#111318] border border-[#222634] rounded-2xl p-4 space-y-3">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-2">
              Contradiction Queue ({displayedConflicts.length})
            </h4>
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {displayedConflicts.map((c) => {
                const isOpen = c.status === "OPEN";
                const isSelected = activeConflict?.id === c.id;
                return (
                  <button
                    key={c.id}
                    onClick={() => setSelectedConflictId(c.id)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      isSelected
                        ? "bg-amber-500/10 border-amber-500/50 shadow-md"
                        : "bg-[#08090C] border-[#222634] hover:border-gray-700"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-xs font-bold text-white font-mono">{c.entity_id}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isOpen
                            ? "bg-red-500/20 text-red-400 border border-red-500/30"
                            : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        }`}
                      >
                        {isOpen ? "SAFETY FROZEN" : "RESOLVED"}
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-400">
                      Field: <span className="text-gray-300 font-mono">{c.conflicting_field}</span> • Claims:{" "}
                      {c.claims.length}
                    </p>
                    <p className="text-[11px] text-red-400 flex items-center gap-1 mt-1">
                      <Lock className="w-2.5 h-2.5" /> {c.frozen_dependencies.length} dependent task locked
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Conflict Adjudication Panel */}
          {activeConflict && (
            <div className="lg:col-span-2 bg-[#111318] border border-[#222634] rounded-2xl p-6 space-y-6">
              {/* Conflict Summary Header */}
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#222634]">
                <div>
                  <h4 className="text-base font-bold text-white flex items-center gap-2">
                    <span>Route Contradiction: {activeConflict.entity_id}</span>
                    <span className="text-xs font-mono text-gray-400">({activeConflict.id.slice(0, 8)})</span>
                  </h4>
                  <p className="text-xs text-gray-400">
                    Two independent field nodes submitted incompatible state assertions for{" "}
                    <span className="font-mono text-amber-400">{activeConflict.conflicting_field}</span>.
                  </p>
                </div>
                <div>
                  {activeConflict.status === "OPEN" ? (
                    <span className="text-xs font-bold px-3 py-1 bg-red-500/10 text-red-400 border border-red-500/30 rounded-full flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5" /> Safety Freeze Active
                    </span>
                  ) : (
                    <span className="text-xs font-bold px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Adjudicated ({activeConflict.resolved_value})
                    </span>
                  )}
                </div>
              </div>

              {/* Side-by-Side Conflicting Claims */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {activeConflict.claims.map((claim, idx) => {
                  const isUsable = claim.value.toUpperCase() === "USABLE";
                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border ${
                        isUsable
                          ? "bg-emerald-500/5 border-emerald-500/30"
                          : "bg-red-500/5 border-red-500/30"
                      } space-y-3`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-gray-300">
                          {idx === 0 ? "Claim A (Field Team 1)" : "Claim B (Field Team 2)"}
                        </span>
                        <span
                          className={`text-xs font-bold font-mono px-2 py-0.5 rounded-lg ${
                            isUsable
                              ? "bg-emerald-500/20 text-emerald-400"
                              : "bg-red-500/20 text-red-400"
                          }`}
                        >
                          {claim.value}
                        </span>
                      </div>

                      <div className="space-y-1.5 text-xs text-gray-400">
                        <p>
                          <span className="text-gray-500">Device ID:</span>{" "}
                          <span className="font-mono text-gray-300">{claim.device_id}</span>
                        </p>
                        <p>
                          <span className="text-gray-500">Actor ID:</span>{" "}
                          <span className="font-mono text-gray-300">{claim.actor_id.slice(0, 16)}...</span>
                        </p>
                        <p className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-gray-500" />
                          <span>{new Date(claim.occurred_at).toLocaleTimeString()}</span>
                        </p>
                        {claim.notes && (
                          <p className="text-red-300 bg-red-950/30 p-2 rounded-lg border border-red-500/20 mt-2">
                            "{claim.notes}"
                          </p>
                        )}
                        {claim.evidence_ids && claim.evidence_ids.length > 0 && (
                          <div className="flex items-center gap-1 text-[11px] text-amber-400 pt-1">
                            <Camera className="w-3 h-3" />
                            <span>Photo Evidence Attached ({claim.evidence_ids.length})</span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Dependent Suspended Operations */}
              <div className="bg-[#08090C] border border-red-500/20 rounded-xl p-4 space-y-2">
                <span className="text-xs font-semibold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5" /> Suspended Dependent Tasks ({activeConflict.frozen_dependencies.length})
                </span>
                <p className="text-xs text-gray-400">
                  Task dispatch on Route-88 is halted. Teams cannot be routed through this sector until an authorized
                  Incident Commander submits an evidence-backed adjudication.
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  {activeConflict.frozen_dependencies.map((tid) => (
                    <span
                      key={tid}
                      className="font-mono text-[11px] px-2.5 py-1 bg-red-500/10 text-red-300 border border-red-500/30 rounded-lg"
                    >
                      Task: {tid.slice(0, 12)}...
                    </span>
                  ))}
                </div>
              </div>

              {/* Human Adjudication Form (Only if OPEN) */}
              {activeConflict.status === "OPEN" ? (
                <div className="space-y-4 pt-2 border-t border-[#222634]">
                  <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Authorized Incident Commander Adjudication
                  </h4>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1.5">
                        Authoritative Resolution Value
                      </label>
                      <div className="flex gap-3">
                        <button
                          type="button"
                          onClick={() => setResolvedValue("BLOCKED")}
                          className={`flex-1 py-2.5 rounded-xl text-xs font-bold border transition-all ${
                            resolvedValue === "BLOCKED"
                              ? "bg-red-600 text-white border-red-500 shadow-md shadow-red-600/30"
                              : "bg-[#08090C] text-gray-400 border-[#222634] hover:text-white"
                          }`}
                        >
                          CONFIRM ROUTE BLOCKED (Impassable)
                        </button>
                        <button
                          type="button"
                          onClick={() => setResolvedValue("USABLE")}
                          className={`flex-1 py-2.5 rounded-xl text-xs font-bold border transition-all ${
                            resolvedValue === "USABLE"
                              ? "bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/30"
                              : "bg-[#08090C] text-gray-400 border-[#222634] hover:text-white"
                          }`}
                        >
                          CONFIRM ROUTE USABLE (Passable)
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1.5">
                        Mandatory Operational Rationale (Recorded in Cryptographic Audit Ledger)
                      </label>
                      <textarea
                        rows={2}
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        className="w-full bg-[#08090C] border border-[#222634] rounded-xl px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-amber-500 transition-all"
                        placeholder="State ground survey, drone telemetry, or volunteer rationale..."
                      />
                    </div>

                    <button
                      type="button"
                      onClick={handleResolveClick}
                      disabled={isResolving || !reason.trim()}
                      className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-black text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-amber-500/30 transition-all disabled:opacity-50"
                    >
                      <Unlock className="w-4 h-4" />
                      {isResolving ? "Committing Adjudication..." : "Authorize Adjudication & Unlock Tasks"}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Adjudicated Rationale Recorded</span>
                  </div>
                  <p className="text-xs text-gray-300 italic">"{activeConflict.resolution_reason}"</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ConflictAdjudicator;
