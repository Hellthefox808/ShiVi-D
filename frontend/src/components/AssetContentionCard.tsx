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
    <div className="bg-[#111318] border border-[#222634] rounded-2xl p-6 space-y-6 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-48 h-48 bg-amber-500/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none" />

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <LifeBuoy className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-white text-base">
                Physical Possession Leases & Deadlock Prevention
              </h3>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                INVARIANT 4
              </span>
            </div>
            <p className="text-xs text-gray-400">
              NFC / QR / GPS Proximity (≤15m) overrides virtual reservations with automated substitute allocation
            </p>
          </div>
        </div>

        <button
          onClick={() => setResolved(!resolved)}
          className={`text-xs font-semibold px-4 py-2 rounded-xl transition-all flex items-center gap-2 ${
            resolved
              ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
              : "bg-[#08090C] text-gray-300 border border-[#222634] hover:bg-[#222634]"
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
              ? "bg-[#08090C] border-[#222634] opacity-80"
              : "bg-amber-500/5 border-amber-500/30"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-gray-200">Squad Alpha (SDRF Team 1)</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
              VIRTUAL RESERVATION
            </span>
          </div>
          <div className="text-xs space-y-1 text-gray-400">
            <p>
              Requested: <span className="font-semibold text-white">Inflatable Motorized Rescue Boat #4</span>
            </p>
            <p>Mode: Cloud Push reservation 15 minutes ago (Remote)</p>
            {resolved && (
              <div className="mt-3 p-2 bg-amber-950/30 border border-amber-500/30 rounded-lg text-amber-300">
                <span className="font-bold flex items-center gap-1 text-[11px]">
                  <Sparkles className="w-3 h-3" /> Auto-Substituted: Boat #5 Assigned
                </span>
                <span className="text-[10px] text-gray-400">
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
              ? "bg-emerald-500/10 border-emerald-500/40 shadow-lg shadow-emerald-500/10"
              : "bg-[#08090C] border-[#222634]"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-gray-200">Squad Bravo (NDRF Team 4)</span>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                resolved
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold"
                  : "bg-gray-800 text-gray-400"
              }`}
            >
              PHYSICAL NFC PROOF
            </span>
          </div>
          <div className="text-xs space-y-1 text-gray-400">
            <p>
              Requested: <span className="font-semibold text-white">Inflatable Motorized Rescue Boat #4</span>
            </p>
            <p>Proof: NFC Tag Tap (UID: 04-A1-B2-C3) + GPS Proximity (6.2m)</p>
            {resolved && (
              <div className="mt-3 p-2 bg-emerald-950/40 border border-emerald-500/30 rounded-lg text-emerald-300">
                <span className="font-bold flex items-center gap-1 text-[11px]">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Custody Lease Granted (60 mins)
                </span>
                <span className="text-[10px] text-emerald-400/80">
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
