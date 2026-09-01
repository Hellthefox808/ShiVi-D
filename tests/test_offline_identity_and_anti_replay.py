"""
Tests for Offline Identity Security, Cryptographic Hash Chains, and Anti-Replay Protection
Verifies resolution of "The Replay Attack & Identity Spoofing Loophole"
"""
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.core.security_crypto import (
    DeviceSecurityRegistry,
    OfflineSecurityValidator,
    EventSecurityValidationResult,
)


@pytest.fixture(autouse=True)
def setup_security_registry():
    DeviceSecurityRegistry.reset()
    DeviceSecurityRegistry.register_device(
        device_id="sdrf-phone-01",
        secret_key="secret_hardware_key_sdrf_01",
        authorized_roles=["RESPONDER"],
    )
    DeviceSecurityRegistry.register_device(
        device_id="citizen-phone-09",
        secret_key="secret_hardware_key_citizen_09",
        authorized_roles=["CITIZEN"],
    )


def test_reject_privilege_escalation_from_offline_citizen():
    """Citizens cannot forge task assignment or supervisor verifications."""
    seen_ids = set()
    malicious_event = {
        "event_id": "EVT-MALICIOUS-01",
        "tenant_id": "tenant-01",
        "actor_id": "citizen-attacker",
        "device_id": "citizen-phone-09",
        "device_sequence": 1,
        "event_type": "TASK_COMPLETION_VERIFIED",  # Unauthorized role action!
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "prev_event_hash": "GENESIS_ROOT_HASH_0000000000000000000000000000000000000000000000000000",
    }

    result = OfflineSecurityValidator.validate_offline_event(
        event=malicious_event,
        actor_role="CITIZEN",
        seen_event_ids=seen_ids,
    )

    assert result.is_valid is False
    assert result.status_code == "UNAUTHORIZED_ROLE"
    assert result.error_message is not None
    assert "Privilege escalation blocked" in result.error_message


def test_anti_replay_duplicate_event_id():
    """Identical event ID submitted twice is detected and blocked."""
    seen_ids = set()
    event = {
        "event_id": "EVT-REPLAY-99",
        "tenant_id": "tenant-01",
        "actor_id": "responder-01",
        "device_id": "sdrf-phone-01",
        "device_sequence": 1,
        "event_type": "TASK_ON_SITE",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "prev_event_hash": "GENESIS_ROOT_HASH_0000000000000000000000000000000000000000000000000000",
    }

    # First admission -> Valid
    res1 = OfflineSecurityValidator.validate_offline_event(event, "RESPONDER", seen_ids)
    assert res1.is_valid is True
    assert res1.status_code == "VALID"

    # Second admission (Replay Attack) -> Blocked
    res2 = OfflineSecurityValidator.validate_offline_event(event, "RESPONDER", seen_ids)
    assert res2.is_valid is False
    assert res2.status_code == "REPLAY_DETECTED"


def test_monotonic_sequence_violation():
    """Device cannot replay an older sequence number."""
    seen_ids = set()
    event_seq2 = {
        "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
        "tenant_id": "tenant-01",
        "actor_id": "responder-01",
        "device_id": "sdrf-phone-01",
        "device_sequence": 2,
        "event_type": "TASK_ON_SITE",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "prev_event_hash": "GENESIS_ROOT_HASH_0000000000000000000000000000000000000000000000000000",
    }
    OfflineSecurityValidator.validate_offline_event(event_seq2, "RESPONDER", seen_ids)

    # Attempt to replay sequence 1 after sequence 2 has been accepted
    event_seq1 = {
        "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
        "tenant_id": "tenant-01",
        "actor_id": "responder-01",
        "device_id": "sdrf-phone-01",
        "device_sequence": 1,
        "event_type": "TASK_EN_ROUTE",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "prev_event_hash": "GENESIS_ROOT_HASH_0000000000000000000000000000000000000000000000000000",
    }
    result = OfflineSecurityValidator.validate_offline_event(event_seq1, "RESPONDER", seen_ids)
    assert result.is_valid is False
    assert result.status_code == "REPLAY_DETECTED"
    assert result.error_message is not None
    assert "Monotonic sequence violation" in result.error_message


def test_detect_tampered_cryptographic_signature():
    """Event with invalid signature (tampered payload) is rejected."""
    seen_ids = set()
    event = {
        "event_id": "EVT-SIGNED-01",
        "tenant_id": "tenant-01",
        "actor_id": "responder-01",
        "device_id": "sdrf-phone-01",
        "device_sequence": 1,
        "event_type": "TASK_ON_SITE",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "prev_event_hash": "GENESIS_ROOT_HASH_0000000000000000000000000000000000000000000000000000",
        "signature": "forged_invalid_signature_hash_12345",
    }

    result = OfflineSecurityValidator.validate_offline_event(event, "RESPONDER", seen_ids)
    assert result.is_valid is False
    assert result.status_code == "SIGNATURE_INVALID"


def test_detect_future_clock_skew_tampering():
    """Event dated hours in the future is rejected."""
    seen_ids = set()
    future_time = (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat()
    event = {
        "event_id": "EVT-FUTURE-01",
        "tenant_id": "tenant-01",
        "actor_id": "responder-01",
        "device_id": "sdrf-phone-01",
        "device_sequence": 1,
        "event_type": "TASK_ON_SITE",
        "occurred_at": future_time,
        "prev_event_hash": "GENESIS_ROOT_HASH_0000000000000000000000000000000000000000000000000000",
    }

    result = OfflineSecurityValidator.validate_offline_event(event, "RESPONDER", seen_ids)
    assert result.is_valid is False
    assert result.status_code == "TIME_SKEW_EXCEEDED"
    assert result.error_message is not None
    assert "Clock tampering rejected" in result.error_message


def test_valid_signed_event_sequence():
    """Legitimate sequence of signed events progresses smoothly."""
    seen_ids = set()
    secret_key = "secret_hardware_key_sdrf_01"

    # Event 1
    event_1 = {
        "event_id": "EVT-GENUINE-01",
        "tenant_id": "tenant-01",
        "actor_id": "responder-01",
        "device_id": "sdrf-phone-01",
        "device_sequence": 1,
        "event_type": "TASK_EN_ROUTE",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "prev_event_hash": "GENESIS_ROOT_HASH_0000000000000000000000000000000000000000000000000000",
    }
    event_1["signature"] = OfflineSecurityValidator.compute_event_signature(secret_key, event_1)

    res1 = OfflineSecurityValidator.validate_offline_event(event_1, "RESPONDER", seen_ids)
    assert res1.is_valid is True
    assert res1.status_code == "VALID"
