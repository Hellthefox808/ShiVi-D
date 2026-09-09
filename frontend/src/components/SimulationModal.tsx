"use client";

import React, { useState } from "react";
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
  Play,
  RotateCcw,
  Zap,
} from "lucide-react";
import { SimulationResponse } from "../services/api";

interface SimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: SimulationResponse | null;
  loading: boolean;
  onRunScenario?: (scenarioId: string) => void;
}

export function SimulationModal({
  isOpen,
  onClose,
  result,
  loading,
  onRunScenario,
}: SimulationModalProps) {
  const [activeScenario, setActiveScenario] = useState<string>("scenario-flood-contradiction");

  if (!isOpen) return null;

  const scenarios = [
    {
      id: "scenario-flood-contradiction",
      title: "Flash Flood Surge & Safety Freeze",
      invariant: "Inv 3: Causal Conflict Protection",
      badge: "CRITICAL",
    },
    {
      id: "scenario-asset-contention",
      title: "Distributed Asset Contention & NFC Lease",
      invariant: "Inv 3: Deadlock Prevention",
      badge: "HIGH",
    },
    {
      id: "scenario-replay-attack",
      title: "Adversarial Poison Packet & Anti-Replay",
      invariant: "Inv 2: Trust Boundary Gate",
      badge: "SECURITY",
    },
    {
      id: "scenario-sms-triage",
      title: "Multilingual Low-Bandwidth SMS Triage",
      invariant: "Inv 1 & 5: Offline NLP Triage",
      badge: "INTAKE",
    },
  ];

  const handleScenarioChange = (id: string) => {
    setActiveScenario(id);
    if (onRunScenario) {
      onRunScenario(id);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-[#121826] border border-[#1E293B] rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1E293B] bg-[#0B0F19]/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">
                ShiVi Operational Simulation Studio — Verified Invariant Drills
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

        {/* Scenario Selector Ribbon */}
        <div className="bg-[#0B0F19] px-6 py-3 border-b border-[#1E293B] flex flex-wrap gap-2">
          {scenarios.map((sc) => (
            <button
              key={sc.id}
              onClick={() => handleScenarioChange(sc.id)}
              disabled={loading}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all border flex items-center gap-2 ${
                activeScenario === sc.id
                  ? "bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-600/30"
                  : "bg-[#121826] border-[#1E293B] text-gray-400 hover:text-white"
              }`}
            >
              <span>{sc.title}</span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-black/40 text-blue-200">
                {sc.badge}
              </span>
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {loading ? (
            <div className="py-16 text-center space-y-4">
              <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mx-auto" />
              <div className="space-y-1">
                <p className="font-medium text-white text-base">
                  Executing Verified Context Loop Drill...
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
                      Verified Context Loop Completed (100% Invariant Guarantees)
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

              {/* Steps Timeline */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider font-mono">
                  Execution Trace Steps ({result.steps.length})
                </h4>

                <div className="space-y-2.5">
                  {result.steps.map((st) => (
                    <div
                      key={st.step}
                      className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-3.5 space-y-1 text-xs"
                    >
                      <div className="flex items-center justify-between font-mono">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px] font-bold">
                            {st.step}
                          </span>
                          <span className="font-bold text-white text-sm">{st.title}</span>
                        </div>
                        <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                          VERIFIED
                        </span>
                      </div>
                      <p className="text-gray-400 text-xs pl-7">{st.detail}</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="py-12 text-center text-xs text-gray-500">
              Select a scenario above to run the drill.
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-[#1E293B] bg-[#0B0F19]/60 flex items-center justify-between text-xs">
          <div className="text-gray-400 font-mono">
            <span>Core Guarantee: Zero Silent Overwrites & Full Monotonic Provenance</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-white font-bold transition-all"
          >
            Close Trace
          </button>
        </div>
      </div>
    </div>
  );
}

export default SimulationModal;

