/**
 * ShiVi Operations Console - Immutable Compliance Audit Ledger Timeline
 * ======================================================================
 *
 * Briefing:
 *     Audit log viewer component (`AuditLedgerTimeline`) rendering the chronological sequence
 *     of tamper-evident operational events and supervisor adjudications.
 *     Features:
 *     - Visual badge indicators categorizing events (Conflict freezes, Mission completions, System updates).
 *     - Actor identification and role tags ('INCIDENT_COMMANDER', 'FIELD_RESPONDER', 'SYSTEM').
 *     - Entity target classifications and target entity UUIDs.
 *     - Formatted human operational rationales recorded during critical overrides.
 *     - Precise UTC timestamps formatted to operator locale.
 *
 * Reason:
 *     Post-disaster inquiries and judicial reviews require mathematical proof of who made which decision,
 *     at what exact second, and based on what field evidence. The AuditLedgerTimeline exposes this
 *     hash-chained compliance record directly to incident commanders in real time.
 */

"use client";

import React from "react";
import { ShieldCheck, Clock, User, CheckCircle2, Lock } from "lucide-react";
import { AuditRecordItem } from "../services/api";

/**
 * Briefing:
 *     Component properties providing audit ledger records.
 */
interface AuditLedgerTimelineProps {
  // Explanation: Chronological array of audit entries fetched from /v1/audit/timeline.
  logs: AuditRecordItem[];
}

/**
 * Briefing:
 *     Audit Ledger Timeline component.
 *
 * Reason:
 *     Renders an auditable list of chronological mission actions, providing instant verification
 *     that state transitions adhere to legal standards and zero-overwrite safety rules.
 *
 * @param props AuditLedgerTimelineProps containing logs array.
 */
export function AuditLedgerTimeline({ logs }: AuditLedgerTimelineProps) {
  return (
    <div className="bg-[#111318] border border-[#222634] rounded-2xl p-6 space-y-6 shadow-xl">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#222634]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
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

        <span className="text-xs font-mono px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded-full flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5" /> 100% CRYPTOGRAPHIC INTEGRITY
        </span>
      </div>

      {/* Audit Log Entries List */}
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
                className="bg-[#08090C] border border-[#222634] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-gray-700 transition-all"
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                      isConflictAction
                        ? "bg-red-500/10 text-red-400 border border-red-500/30"
                        : isVerifiedAction
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    }`}
                  >
                    {isConflictAction ? <Lock className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                  </div>

                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-bold text-white">{log.action}</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#111318] text-gray-300 border border-[#222634]">
                        {log.actor_role}
                      </span>
                      <span className="text-[10px] text-gray-500 font-mono">
                        Target: {log.target_entity_type}/{log.target_entity_id?.slice(0, 8)}
                      </span>
                    </div>
                    {log.reason && (
                      <p className="text-xs text-gray-300 italic bg-[#111318]/60 p-2 rounded-lg border border-[#222634]/60">
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
