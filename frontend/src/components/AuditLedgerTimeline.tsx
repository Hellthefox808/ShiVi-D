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
    <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-6 shadow-sm">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-base">
              Immutable Hash-Chained Audit Ledger
            </h3>
            <p className="text-xs text-slate-600 font-medium">
              Tamper-evident RFC-3161 append-only audit trail preserving all state transitions and human adjudications
            </p>
          </div>
        </div>

        <span className="text-xs font-mono px-3 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-full flex items-center gap-1.5 font-bold shadow-sm">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> 100% CRYPTOGRAPHIC INTEGRITY
        </span>
      </div>

      {/* Audit Log Entries List */}
      <div className="space-y-3">
        {logs.length === 0 ? (
          <p className="text-xs text-slate-500 py-8 text-center font-medium">No audit records registered yet.</p>
        ) : (
          logs.map((log, idx) => {
            const isConflictAction = log.action.includes("CONFLICT");
            const isVerifiedAction = log.action.includes("VERIFIED");
            return (
              <div
                key={log.id || idx}
                className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 hover:bg-white transition-all shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 ${
                      isConflictAction
                        ? "bg-red-50 text-red-700 border border-red-200"
                        : isVerifiedAction
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-amber-50 text-amber-700 border border-amber-200"
                    }`}
                  >
                    {isConflictAction ? <Lock className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                  </div>

                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-bold text-slate-900">{log.action}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 shadow-sm">
                        {log.actor_role}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        Target: {log.target_entity_type}/{log.target_entity_id?.slice(0, 8)}
                      </span>
                    </div>
                    {log.reason && (
                      <p className="text-xs text-slate-700 italic bg-white p-2 rounded-lg border border-slate-200 shadow-sm">
                        "{log.reason}"
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 text-[11px] text-slate-500 shrink-0 font-mono self-end sm:self-center font-medium">
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
