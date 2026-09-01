"""
Tests for Distributed Asset Allocation & Contention Resolution Engine
Verifies resolution of "The Distributed Asset Lock Loophole"
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.modules.assets.allocation_engine import DistributedAssetAllocationEngine, ContentionResolutionResult


def test_physical_possession_beats_virtual_reservation():
    claim_remote = {
        "claimant_id": "lead-alpha",
        "incident_id": "INC-ALPHA-01",
        "task_id": "TASK-01",
        "claim_type": "VIRTUAL_RESERVATION",
        "priority_score": 85.0,
        "claimed_at": datetime.now(timezone.utc),
    }

    claim_physical = {
        "claimant_id": "lead-bravo",
        "incident_id": "INC-BRAVO-02",
        "task_id": "TASK-02",
        "claim_type": "PHYSICAL_POSSESSION",
        "proof_data": {"proof_type": "NFC_TAP", "nfc_uid": "TAG-GEN-77"},
        "priority_score": 60.0,
        "claimed_at": datetime.now(timezone.utc) + timedelta(minutes=5),
    }

    substitutes = [
        {"id": "gen-02", "asset_code": "GEN-PUMP-02", "current_location_name": "Sector 3 Staging Depot"}
    ]

    result = DistributedAssetAllocationEngine.resolve_contention(
        asset_code="GEN-PUMP-01",
        claim_a=claim_remote,
        claim_b=claim_physical,
        available_substitutes=substitutes,
    )

    # Physical possession must win
    assert result.winner_claimant_id == "lead-bravo"
    assert "Verified Physical Custody" in result.winner_reason
    assert result.loser_claimant_id == "lead-alpha"

    # Loser must NOT be deadlocked; receives automated substitute
    assert result.substitute_provided is True
    assert result.substitute_asset_code == "GEN-PUMP-02"
    assert "CONTINGENCY ALLOCATION" in result.contingency_action_notice


def test_priority_score_breaks_dual_virtual_claims():
    claim_icu = {
        "claimant_id": "lead-hospital",
        "incident_id": "INC-HOSPITAL-ICU",
        "task_id": "TASK-ICU",
        "claim_type": "VIRTUAL_RESERVATION",
        "priority_score": 95.0,  # Critical ICU power
        "claimed_at": datetime.now(timezone.utc) + timedelta(minutes=2),
    }

    claim_drainage = {
        "claimant_id": "lead-roadway",
        "incident_id": "INC-DRAINAGE",
        "task_id": "TASK-DRAIN",
        "claim_type": "VIRTUAL_RESERVATION",
        "priority_score": 45.0,  # Street water drainage
        "claimed_at": datetime.now(timezone.utc),
    }

    substitutes = [
        {"id": "gen-03", "asset_code": "GEN-PUMP-03", "current_location_name": "Central Depot"}
    ]

    result = DistributedAssetAllocationEngine.resolve_contention(
        asset_code="GEN-PUMP-01",
        claim_a=claim_drainage,
        claim_b=claim_icu,
        available_substitutes=substitutes,
    )

    # High life-safety priority must win
    assert result.winner_claimant_id == "lead-hospital"
    assert "Life-Safety Priority Precedence" in result.winner_reason
    assert result.loser_claimant_id == "lead-roadway"
    assert result.substitute_provided is True
    assert result.substitute_asset_code == "GEN-PUMP-03"


def test_causal_timestamp_breaks_equal_priority_claims():
    t_early = datetime.now(timezone.utc)
    t_late = t_early + timedelta(minutes=10)

    claim_1 = {
        "claimant_id": "lead-one",
        "incident_id": "INC-01",
        "task_id": "TASK-01",
        "claim_type": "VIRTUAL_RESERVATION",
        "priority_score": 70.0,
        "claimed_at": t_early,
    }

    claim_2 = {
        "claimant_id": "lead-two",
        "incident_id": "INC-02",
        "task_id": "TASK-02",
        "claim_type": "VIRTUAL_RESERVATION",
        "priority_score": 70.0,
        "claimed_at": t_late,
    }

    result = DistributedAssetAllocationEngine.resolve_contention(
        asset_code="AMBULANCE-01",
        claim_a=claim_1,
        claim_b=claim_2,
        available_substitutes=[],
    )

    assert result.winner_claimant_id == "lead-one"
    assert "Causal First-Claim Invariant" in result.winner_reason
    assert result.loser_claimant_id == "lead-two"
    assert result.substitute_provided is False
    assert "RESOURCE SHORTAGE ALERT" in result.contingency_action_notice
