"""
ShiVi Distributed Physical Asset Allocation Engine
==================================================

Briefing:
    Solves the "Distributed Asset Lock Loophole" in disaster response logistics.
    In field operations, physical equipment (de-watering pumps, zodiac rescue boats,
    mobile generators, emergency ambulances) is strictly scarce. When partitioned edge
    devices synchronize, multiple rescue teams may concurrently claim the same asset.

Reason:
    Standard database locks or Last-Write-Wins algorithms fail catastrophically:
    - A team with physical custody of a pump at an active breach could have their digital
      lease revoked by a remote commander who submitted a database update 1 second later.
    - Alternatively, conflicting reservations cause deadlocks where both squads wait for
      confirmation, delaying life-saving rescue.

The ShiVi 4-Step Contention Resolution Invariant:
    1. Physical Possession Proof Beats Virtual Reservation:
       A responder with physical proximity proof (NFC tap, QR scan, GPS proximity ≤ 15m)
       always retains the asset over a remote virtual reservation.
    2. Life-Safety Priority Precedence:
       If both (or neither) possess physical proof, the incident with the higher calculated
       life-safety priority score (delta ≥ 5.0 pts) wins custody.
    3. Causal First-Timestamp Fallback:
       If priorities are within 5.0 points, the earliest causal timestamp prevails.
    4. Zero-Deadlock Substitute Dispatch:
       The losing squad is never left stranded; the engine automatically re-assigns the closest
       available substitute resource from the local equipment depot, ensuring continuous operations.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContentionResolutionResult:
    """
    Briefing:
        Structured result returned by the `DistributedAssetAllocationEngine.resolve_contention()` algorithm.

    Reason:
        Transmits full adjudication details to callers: winner identity, loser identity, operational
        justification rationale, substitute equipment assignment, and a contingency dispatch notice.
    """
    # Explanation: UUID of the contested primary physical asset
    primary_asset_id: str
    # Explanation: Equipment identification code (e.g. 'PUMP-75HP-01')
    primary_asset_code: str
    # Explanation: User UUID of the winning responder
    winner_claimant_id: str
    # Explanation: Incident UUID that retains the asset
    winner_incident_id: str
    # Explanation: Task UUID that retains the asset
    winner_task_id: str
    # Explanation: Written algorithmic justification explaining why the winner prevailed
    winner_reason: str
    
    # Explanation: User UUID of the losing claimant
    loser_claimant_id: str
    # Explanation: Incident UUID of the superseded claim
    loser_incident_id: str
    # Explanation: Task UUID of the superseded claim
    loser_task_id: str
    
    # Explanation: True if an alternate resource was automatically reassigned to the losing team
    substitute_provided: bool
    # Explanation: Database UUID of the substitute equipment (None if depot exhausted)
    substitute_asset_id: Optional[str]
    # Explanation: Asset code of substitute equipment (e.g. 'PUMP-75HP-04')
    substitute_asset_code: Optional[str]
    # Explanation: Physical depot or staging area where substitute is located
    substitute_location: Optional[str]
    # Explanation: Operational notification broadcast to field radios and command dashboards
    contingency_action_notice: str


class DistributedAssetAllocationEngine:
    """
    Briefing:
        Deterministic contention resolution engine for physical equipment in disconnected operations.

    Reason:
        Executes without human bottleneck, applying physical custody proof, life-safety priority,
        and automated substitute allocation to eliminate dispatch deadlocks.
    """

    @staticmethod
    def resolve_contention(
        asset_code: str,
        claim_a: Dict[str, Any],
        claim_b: Dict[str, Any],
        available_substitutes: List[Dict[str, Any]],
    ) -> ContentionResolutionResult:
        """
        Briefing:
            Resolves two conflicting claims on the same physical equipment without deadlocking.

        Reason:
            Implements the 4-step contention invariant:
            1. Physical Proof Check: PHYSICAL_POSSESSION > VIRTUAL_RESERVATION.
            2. Priority Differential: If difference in priority_score >= 5.0, higher score wins.
            3. Timestamp Tie-Breaker: Earlier claimed_at wins.
            4. Automatic Substitute Allocation: Re-routes losing squad to next available asset.

        Parameters:
            asset_code: Human-readable code of contested asset (e.g. 'BOAT-ZODIAC-02').
            claim_a: Existing active claim dictionary.
            claim_b: Inbound competing claim dictionary.
            available_substitutes: List of unassigned assets in the same category from the depot.

        Returns:
            `ContentionResolutionResult` detailing winning and substitute allocations.
        """
        # Explanation: Step 1 - Evaluate Physical Possession Proof
        proof_a = claim_a.get("claim_type") == "PHYSICAL_POSSESSION"
        proof_b = claim_b.get("claim_type") == "PHYSICAL_POSSESSION"

        winner = None
        loser = None
        reason = ""

        if proof_a and not proof_b:
            winner, loser = claim_a, claim_b
            reason = f"Verified Physical Custody: {claim_a['claimant_id']} validated physical possession (NFC/QR/Proximity) on {asset_code}."
        elif proof_b and not proof_a:
            winner, loser = claim_b, claim_a
            reason = f"Verified Physical Custody: {claim_b['claimant_id']} validated physical possession (NFC/QR/Proximity) on {asset_code}."
        else:
            # Explanation: Step 2 - Both have physical proof OR both are virtual -> Evaluate Priority Score
            score_a = float(claim_a.get("priority_score", 50.0))
            score_b = float(claim_b.get("priority_score", 50.0))

            if abs(score_a - score_b) >= 5.0:
                if score_a > score_b:
                    winner, loser = claim_a, claim_b
                    reason = f"Life-Safety Priority Precedence: Incident {claim_a['incident_id']} (Priority {score_a:.1f}) exceeds {claim_b['incident_id']} (Priority {score_b:.1f})."
                else:
                    winner, loser = claim_b, claim_a
                    reason = f"Life-Safety Priority Precedence: Incident {claim_b['incident_id']} (Priority {score_b:.1f}) exceeds {claim_a['incident_id']} (Priority {score_a:.1f})."
            else:
                # Explanation: Step 3 - Priority within delta threshold -> Causal First-Timestamp Wins
                time_a = claim_a.get("claimed_at") or datetime.min
                time_b = claim_b.get("claimed_at") or datetime.min
                if time_a <= time_b:
                    winner, loser = claim_a, claim_b
                    reason = f"Causal First-Claim Invariant: Claim A arrived/occurred earlier ({time_a})."
                else:
                    winner, loser = claim_b, claim_a
                    reason = f"Causal First-Claim Invariant: Claim B arrived/occurred earlier ({time_b})."

        # Explanation: Step 4 - Automated Substitute Resource Dispatch for the losing party
        substitute_asset_id = None
        substitute_asset_code = None
        substitute_location = None
        substitute_provided = False

        if available_substitutes:
            best_sub = available_substitutes[0]
            substitute_asset_id = best_sub.get("id")
            substitute_asset_code = best_sub.get("asset_code")
            substitute_location = best_sub.get("current_location_name", "Nearest Sector Depot")
            substitute_provided = True
            notice = (
                f"CONTINGENCY ALLOCATION: {asset_code} retained by {winner['claimant_id']} ({winner['incident_id']}). "
                f"Squad {loser['claimant_id']} has been automatically assigned substitute {substitute_asset_code} "
                f"from {substitute_location}. Zero operation stall."
            )
        else:
            notice = (
                f"RESOURCE SHORTAGE ALERT: {asset_code} retained by {winner['claimant_id']}. "
                f"No identical substitute available in local depot. Incident Commander alerted for mutual aid dispatch."
            )

        return ContentionResolutionResult(
            primary_asset_id=claim_a.get("asset_id", "asset-01"),
            primary_asset_code=asset_code,
            winner_claimant_id=winner["claimant_id"],
            winner_incident_id=winner["incident_id"],
            winner_task_id=winner["task_id"],
            winner_reason=reason,
            loser_claimant_id=loser["claimant_id"],
            loser_incident_id=loser["incident_id"],
            loser_task_id=loser["task_id"],
            substitute_provided=substitute_provided,
            substitute_asset_id=substitute_asset_id,
            substitute_asset_code=substitute_asset_code,
            substitute_location=substitute_location,
            contingency_action_notice=notice,
        )
