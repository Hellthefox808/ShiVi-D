"""
ShiVi Causal Conflict Resolution & Safety Freeze Engine
=======================================================

Briefing:
    Encapsulates the deterministic conflict evaluation and safety freeze algorithms
    used across the ShiVi distributed architecture. As field devices reconnect after
    prolonged radio partitions (such as passing from an underground shelter to high ground),
    they upload outbox event queues that may disagree with the current canonical state.

Reason:
    In standard software, optimistic concurrency or Last-Write-Wins (LWW) silently overwrites
    earlier records. In a search-and-rescue mission, if Team Alpha marks Route 101 as 'BLOCKED'
    due to a landslide at 10:00 AM, and Team Beta (whose phone clock drifted or was out of sync)
    reports Route 101 as 'USABLE' at 10:05 AM based on an outdated observation, applying LWW
    would falsely report the road as open, directing rescue trucks into danger.
    The CausalConflictEngine enforces ShiVi's "Causal Safety Freeze" invariant:
    contradictions on life-safety fields are quarantined immediately for human adjudication.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class ConflictEvaluationResult:
    """
    Briefing:
        Structured result returned by `CausalConflictEngine.evaluate_mutation()`.

    Reason:
        Provides callers (such as the synchronization pipeline or API routers) with
        actionable decision metadata:
        - `has_conflict`: Boolean flag indicating if a safety contradiction was triggered.
        - `conflict_type`: Classification tag (e.g., 'LIFE_SAFETY_CONTRADICTION', 'LWW_APPLIED').
        - `conflicting_field`: Attribute name that experienced the collision.
        - `frozen_entities`: List of entity IDs that must be immediately locked.
        - `preserved_claims`: Competing assertions preserved for supervisor review.
        - `recommended_action`: Direct operational instruction ('TRIGGER_SAFETY_FREEZE', 'APPLY_MUTATION', 'APPLY_LWW').
    """
    # Explanation: True if an irreconcilable life-safety conflict exists
    has_conflict: bool
    # Explanation: Categorical classification of the conflict event
    conflict_type: Optional[str]  # e.g., "LIFE_SAFETY_CONTRADICTION", "CONCURRENT_FIELD_MUTATION"
    # Explanation: Name of the field attribute undergoing collision
    conflicting_field: Optional[str]
    # Explanation: Array of entity IDs that must enter safety-freeze state
    frozen_entities: List[str]
    # Explanation: Preserved evidence and telemetry from both competing parties
    preserved_claims: List[Dict[str, Any]]
    # Explanation: Recommended handling pipeline instruction
    recommended_action: str


class CausalConflictEngine:
    """
    Briefing:
        Core conflict evaluation engine for distributed disaster operations.

    Reason:
        Inspects incoming field mutations against materialized canonical state. Distinguishes
        between harmless concurrent updates (which resolve deterministically via LWW) and
        life-safety contradictions (which trigger automatic safety freezes).
    """

    # Explanation: Specific attributes where automated reconciliation could cause physical harm or death.
    # Mutations conflicting on these fields trigger an immediate hard freeze.
    LIFE_SAFETY_FIELDS = {"status", "is_route_blocked", "hazard_level", "structural_integrity"}

    # Explanation: Opposing semantic states that represent mutually exclusive operational realities.
    CONTRADICTORY_VALUE_PAIRS = {
        ("USABLE", "BLOCKED"),
        ("BLOCKED", "USABLE"),
        ("SAFE", "HAZARDOUS"),
        ("HAZARDOUS", "SAFE"),
        ("OPEN", "CLOSED"),
    }

    @classmethod
    def evaluate_mutation(
        cls,
        entity_type: str,
        entity_id: str,
        current_value: Any,
        incoming_value: Any,
        field_name: str,
        actor_id: str,
        device_id: str,
        occurred_at: datetime,
        evidence_ids: Optional[List[str]] = None,
    ) -> ConflictEvaluationResult:
        """
        Briefing:
            Evaluates whether an incoming mutation creates an operational safety conflict
            with the existing materialized entity state.

        Reason:
            1. If values match or current state is unknown/empty, mutation applies cleanly.
            2. If values contradict on a designated `LIFE_SAFETY_FIELD` (e.g. USABLE vs BLOCKED),
               creates a `ConflictEvaluationResult` with `TRIGGER_SAFETY_FREEZE`, freezing the entity
               and bundling both claims for human supervisor review.
            3. If values differ on non-safety fields (e.g. description or notes), recommends
               `APPLY_LWW` (Last-Write-Wins based on physical event timestamp).

        Parameters:
            entity_type: Category of entity ('route_observation', 'task', 'incident').
            entity_id: Unique identifier of the specific target entity.
            current_value: Current value stored in the database.
            incoming_value: New value proposed by the incoming event envelope.
            field_name: Name of the property being modified (e.g., 'status').
            actor_id: User UUID who generated the incoming mutation.
            device_id: Hardware device ID that recorded the event.
            occurred_at: Timestamp when the field observation was recorded.
            evidence_ids: Optional list of photographic/cryptographic evidence UUIDs supporting the claim.

        Returns:
            `ConflictEvaluationResult` detailing whether to apply the mutation, apply LWW,
            or trigger a safety freeze.
        """
        # Explanation: Identical values or initial values require no conflict handling
        if current_value == incoming_value or current_value in [None, "UNKNOWN"]:
            return ConflictEvaluationResult(
                has_conflict=False,
                conflict_type=None,
                conflicting_field=None,
                frozen_entities=[],
                preserved_claims=[],
                recommended_action="APPLY_MUTATION",
            )

        # Explanation: Check for direct life-safety contradiction pairs
        pair = (str(current_value).upper(), str(incoming_value).upper())
        if field_name in cls.LIFE_SAFETY_FIELDS and pair in cls.CONTRADICTORY_VALUE_PAIRS:
            # Explanation: Preserve evidence from both sides of the contradiction
            preserved_claims = [
                {
                    "actor_id": "existing_state",
                    "device_id": "server_canonical",
                    "value": current_value,
                },
                {
                    "actor_id": actor_id,
                    "device_id": device_id,
                    "value": incoming_value,
                    "occurred_at": occurred_at.isoformat() if hasattr(occurred_at, "isoformat") else str(occurred_at),
                    "evidence_ids": evidence_ids or [],
                },
            ]
            return ConflictEvaluationResult(
                has_conflict=True,
                conflict_type="LIFE_SAFETY_CONTRADICTION",
                conflicting_field=field_name,
                frozen_entities=[entity_id],
                preserved_claims=preserved_claims,
                recommended_action="TRIGGER_SAFETY_FREEZE",
            )

        # Explanation: Standard non-safety mutation resolves via deterministic timestamp ordering (LWW)
        return ConflictEvaluationResult(
            has_conflict=False,
            conflict_type="LWW_APPLIED",
            conflicting_field=field_name,
            frozen_entities=[],
            preserved_claims=[],
            recommended_action="APPLY_LWW",
        )
