"use client";

import React from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Lock,
  Camera,
  FileCheck,
  Shield,
  Clock,
  X,
  Radio,
  ArrowRight,
} from "lucide-react";
import { SimulationResponse } from "../services/api";

interface SimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: SimulationResponse | null;
  loading: boolean;
}

export function SimulationModal({
  isOpen,
  onClose,
  result,
  loading,
}: SimulationModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-[#121826] border border-[#1E293B] rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1E293B] bg-[#0B0F19]/60">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">
                ShiVi P0 Verified Context Loop — Live Execution Trace
              </h3>
              <p className="text-xs text-gray-400">
                End-to-end transactional disaster coordination across all 5 non-negotiable invariants
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-white hover:bg-[#1E293B] transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          {loading ? (
            <div className="py-16 text-center space-y-4">
              <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mx-auto" />
              <div className="space-y-1">
                <p className="font-medium text-white text-base">
                  Executing 9-Step Disaster Coordination Loop...
                </p>
                <p className="text-xs text-gray-400 max-w-md mx-auto">
                  Exercising offline outbox commits, vector clocks, Causal Conflict Engine safety freezes,
                  adjudication, cryptographic photo proofs, and immutable audit reconstruction.
                </p>
              </div>
            </div>
          ) : result ? (
            <>
              {/* Summary Banner */}
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-bold text-emerald-300 text-sm">
                      P0 Verified Context Loop Completed Successfully (100% Integrity)
                    </h4>
                    <p className="text-xs text-emerald-400/80">
                      Simulation ID: <span className="font-mono">{result.simulation_id.slice(0, 12)}...</span> •
                      Executed at: {new Date(result.executed_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono px-2.5 py-1 bg-black/40 rounded-lg text-emerald-300 border border-emerald-500/30">
                    STATUS: {result.status}
                  </span>
                </div>
              </div>

              {/* 9-Step Timeline */}
              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Sequential Operational Timeline (9 Stages)
                </h4>

                <div className="space-y-3">
                  {result.steps.map((s) => (
                    <div
                      key={s.step}
                      className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 transition-all hover:border-gray-700"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <span className="w-6 h-6 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                            {s.step}
                          </span>
                          <div className="space-y-1">
                            <h5 className="text-sm font-semibold text-white flex items-center gap-2">
                              {s.title}
                              {s.step === 5 && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1">
                                  <Lock className="w-2.5 h-2.5" /> SAFETY FREEZE ACTIVE
                                </span>
                              )}
                              {s.step === 6 && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                  HUMAN ADJUDICATED
                                </span>
                              )}
                              {s.step === 7 && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center gap-1">
                                  <Camera className="w-2.5 h-2.5" /> SHA-256 PROOF
                                </span>
                              )}
                            </h5>
                            <p className="text-xs text-gray-300">{s.detail}</p>
                          </div>
                        </div>
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-1" />
                      </div>

                      {/* Payload Metadata Inspector */}
                      {s.payload && Object.keys(s.payload).length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-[#1E293B]/60 text-[11px] font-mono text-gray-400 flex flex-wrap gap-x-4 gap-y-1">
                          {Object.entries(s.payload).map(([k, v]) => (
                            <span key={k}>
                              <span className="text-gray-500">{k}:</span>{" "}
                              <span className="text-blue-300">
                                {typeof v === "object" ? JSON.stringify(v) : String(v)}
                              </span>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Result Artifacts Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 space-y-2">
                  <span className="text-xs text-gray-400 font-semibold uppercase">Incident Resolution</span>
                  <div className="space-y-1 text-xs">
                    <p className="text-white font-medium">{result.incident.title}</p>
                    <p className="text-gray-400">
                      ID: <span className="font-mono text-gray-300">{result.incident.id}</span>
                    </p>
                    <p className="text-gray-400">
                      Priority Score:{" "}
                      <span className="font-bold text-amber-400">{result.incident.priority_score}/100</span>
                    </p>
                    <p className="text-gray-400">
                      Final Status:{" "}
                      <span className="font-bold text-emerald-400">{result.incident.status}</span>
                    </p>
                  </div>
                </div>

                <div className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 space-y-2">
                  <span className="text-xs text-gray-400 font-semibold uppercase">Conflict Adjudication</span>
                  <div className="space-y-1 text-xs">
                    <p className="text-white font-medium">Entity: {result.conflict.entity_id}</p>
                    <p className="text-gray-400">
                      Adjudicated Value:{" "}
                      <span className="font-bold text-red-400">{result.conflict.resolved_value}</span>
                    </p>
                    <p className="text-gray-400">
                      Reason: <span className="text-gray-300">{result.conflict.reason}</span>
                    </p>
                    <p className="text-gray-400">
                      Evidence SHA-256:{" "}
                      <span className="font-mono text-cyan-300">
                        {result.evidence.sha256_hash.slice(0, 20)}...
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <p className="text-center text-gray-400 py-12 text-sm">No simulation data available.</p>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#1E293B] bg-[#0B0F19]/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-all shadow-md shadow-blue-600/30"
          >
            Close Trace Inspector
          </button>
        </div>
      </div>
    </div>
  );
}

export default SimulationModal;
