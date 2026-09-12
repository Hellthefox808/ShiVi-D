/**
 * ShiVi Operations Console - Physical Asset Contention & Custody Card
 * ====================================================================
 *
 * Briefing:
 *     Interactive demonstrator component (`AssetContentionCard`) showcasing the ShiVi
 *     "Physical Asset Custody & Zero-Deadlock Substitution" invariant (Invariant 4).
 *     Illustrates a real-world disaster contention scenario:
 *     - Squad Alpha holds a remote virtual reservation for Inflatable Motorized Rescue Boat #4.
 *     - Squad Bravo physically arrives at the boat ramp, taps the hardware NFC tag (or scans QR)
 *       within 6.2 meters GPS proximity.
 *     - The distributed allocation engine awards physical possession to Squad Bravo ($C_p > C_v$)
 *       and immediately auto-dispatches an equivalent substitute asset (Boat #5) to Squad Alpha,
 *       eliminating circular wait states and radio arguments.
 *
 * Reason:
 *     In disaster operations, digital reservations cannot seize equipment that is already being
 *     physically operated on the floodbank. Enforcing cryptographic proof-of-possession with automatic
 *     substitute rerouting guarantees continuous field velocity with zero operational deadlock.
 */

"use client";

import React, { useState } from "react";
import {
  LifeBuoy,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Radio,
  Layers,
  Sparkles,
} from "lucide-react";

/**
 * Briefing:
 *     Physical Asset Contention Card component.
 *
 * Reason:
 *     Visualizes the arbitration logic between remote virtual intent and verified physical custody,
 *     allowing operators to interactively simulate contention resolution and auto-substitution.
 */
export function AssetContentionCard() {
  // Explanation: State toggle indicating whether the contention event has been resolved by the allocation engine.
  const [resolved, setResolved] = useState<boolean>(false);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 space-y-6 shadow-sm relative overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
            <LifeBuoy className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-900 text-base">
                Physical Possession Leases & Deadlock Prevention
              </h3>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                INVARIANT 4
              </span>
            </div>
            <p className="text-xs text-slate-600 font-medium">
              NFC / QR / GPS Proximity (≤15m) overrides virtual reservations with automated substitute allocation
            </p>
          </div>
        </div>

        <button
          onClick={() => setResolved(!resolved)}
          className={`text-xs font-bold px-4 py-2 rounded-xl transition-all flex items-center gap-2 shadow-sm ${
            resolved
              ? "bg-emerald-600 text-white shadow-emerald-600/20"
              : "bg-slate-100 text-slate-700 border border-slate-200 hover:bg-slate-200"
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          {resolved ? "Contention Resolved (NFC Lease Active)" : "Simulate Contention Event"}
        </button>
      </div>

      {/* Scenario Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Squad Alpha Claim */}
        <div
          className={`p-4 rounded-xl border transition-all ${
            resolved
              ? "bg-slate-50 border-slate-200 opacity-80"
              : "bg-amber-50/60 border-amber-200"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-900">Squad Alpha (SDRF Team 1)</span>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
              VIRTUAL RESERVATION
            </span>
          </div>
          <div className="text-xs space-y-1 text-slate-600">
            <p>
              Requested: <span className="font-bold text-slate-900">Inflatable Motorized Rescue Boat #4</span>
            </p>
            <p>Mode: Cloud Push reservation 15 minutes ago (Remote)</p>
            {resolved && (
              <div className="mt-3 p-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-900">
                <span className="font-bold flex items-center gap-1 text-[11px] text-amber-800">
                  <Sparkles className="w-3 h-3" /> Auto-Substituted: Boat #5 Assigned
                </span>
                <span className="text-[10px] text-slate-600">
                  Zero mission delay. Displaced team seamlessly re-routed to alternate craft.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Squad Bravo Claim */}
        <div
          className={`p-4 rounded-xl border transition-all ${
            resolved
              ? "bg-emerald-50/70 border-emerald-300 shadow-sm"
              : "bg-slate-50 border-slate-200"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-900">Squad Bravo (NDRF Team 4)</span>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                resolved
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold"
                  : "bg-slate-200 text-slate-700 font-semibold"
              }`}
            >
              PHYSICAL NFC PROOF
            </span>
          </div>
          <div className="text-xs space-y-1 text-slate-600">
            <p>
              Requested: <span className="font-bold text-slate-900">Inflatable Motorized Rescue Boat #4</span>
            </p>
            <p>Proof: NFC Tag Tap (UID: 04-A1-B2-C3) + GPS Proximity (6.2m)</p>
            {resolved && (
              <div className="mt-3 p-2 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900">
                <span className="font-bold flex items-center gap-1 text-[11px] text-emerald-800">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Custody Lease Granted (60 mins)
                </span>
                <span className="text-[10px] text-emerald-700">
                  Physical possession verified on ground. Cryptographic lease signed by responder device.
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AssetContentionCard;
