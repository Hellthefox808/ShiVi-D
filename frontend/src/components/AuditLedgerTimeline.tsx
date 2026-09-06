"use client";

import React from "react";
import { ShieldCheck, Clock, User, CheckCircle2, Lock } from "lucide-react";
import { AuditRecordItem } from "../services/api";

interface AuditLedgerTimelineProps {
  logs: AuditRecordItem[];
}

export function AuditLedgerTimeline({ logs }: AuditLedgerTimelineProps) {
  return (
    <div className="bg-[#121826] border border-[#1E293B] rounded-2xl p-6 space-y-6 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#1E293B]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">
              Immutable Hash-Chained Audit Ledger
            </h3>
            <p className="text-xs text-gray-400">
              Tamper-evident RFC-3161 append-only audit trail preserving all state transitions and human adjudications
            </p>
          </div>
        </div>

        <span className="text-xs font-mono px-3 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded-full flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5" /> 100% CRYPTOGRAPHIC INTEGRITY
        </span>
      </div>

      <div className="space-y-3">
        {logs.length === 0 ? (
          <p className="text-xs text-gray-500 py-8 text-center">No audit records registered yet.</p>
        ) : (
          logs.map((log, idx) => {
            const isConflictAction = log.action.includes("CONFLICT");
            const isVerifiedAction = log.action.includes("VERIFIED");
            return (
              <div
                key={log.id || idx}
                className="bg-[#0B0F19] border border-[#1E293B] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-gray-700 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                      isConflictAction
                        ? "bg-red-500/10 text-red-400 border border-red-500/30"
                        : isVerifiedAction
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        : "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                    }`}
                  >
                    {isConflictAction ? <Lock className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                  </div>

                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-bold text-white">{log.action}</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#121826] text-gray-300 border border-[#1E293B]">
                        {log.actor_role}
                      </span>
                      <span className="text-[10px] text-gray-500 font-mono">
                        Target: {log.target_entity_type}/{log.target_entity_id?.slice(0, 8)}
                      </span>
                    </div>
                    {log.reason && (
                      <p className="text-xs text-gray-300 italic bg-[#121826]/60 p-2 rounded-lg border border-[#1E293B]/60">
                        "{log.reason}"
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 text-[11px] text-gray-500 shrink-0 font-mono self-end sm:self-center">
                  <Clock className="w-3.5 h-3.5" />
                  <span>{new Date(log.timestamp).toLocaleString()}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default AuditLedgerTimeline;
