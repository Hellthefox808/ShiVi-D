"""
ShiVi Causal Conflict Resolution & Safety Freeze Engine
Encapsulates causal event merge logic, contradiction detection, and automatic safety locks.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class ConflictEvaluationResult:
    has_conflict: bool
    conflict_type: Optional[str]  # e.g., "LIFE_SAFETY_CONTRADICTION", "CONCURRENT_FIELD_MUTATION"
    conflicting_field: Optional[str]
    frozen_entities: List[str]
    preserved_claims: List[Dict[str, Any]]
    recommended_action: str


class CausalConflictEngine:
    """
    Causal Conflict Resolution Engine:
    Detects concurrent conflicting mutations across distributed edge devices
    and triggers immediate safety freezes on high-consequence fields.
    """

    LIFE_SAFETY_FIELDS = {"status", "is_route_blocked", "hazard_level", "structural_integrity"}
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
        Evaluates whether an incoming mutation creates an operational safety conflict
        with the current materialized state.
        """
        if current_value == incoming_value or current_value in [None, "UNKNOWN"]:
            return ConflictEvaluationResult(
                has_conflict=False,
                conflict_type=None,
                conflicting_field=None,
                frozen_entities=[],
                preserved_claims=[],
                recommended_action="APPLY_MUTATION",
            )

        # Check for direct life-safety contradiction
        pair = (str(current_value).upper(), str(incoming_value).upper())
        if field_name in cls.LIFE_SAFETY_FIELDS and pair in cls.CONTRADICTORY_VALUE_PAIRS:
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

        # General concurrent field mutation
        return ConflictEvaluationResult(
            has_conflict=False,
            conflict_type="LWW_APPLIED",
            conflicting_field=field_name,
            frozen_entities=[],
            preserved_claims=[],
            recommended_action="APPLY_LWW",
        )
