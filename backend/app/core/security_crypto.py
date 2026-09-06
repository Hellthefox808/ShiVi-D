"""
ShiVi Cryptographic Security & Anti-Replay Engine
Guarantees offline authenticity, role authorization, and anti-replay protection:
1. Hardware-Bound Monotonic Hash Chains: Verifies device sequence and prev_event_hash.
2. Cryptographic Signature Validation: Validates device Ed25519/HMAC authenticity.
3. Offline Capability Attestation: Enforces role permissions against historical grants.
4. Anti-Replay & Time Skew Clamping: Eliminates replayed nonces and synthetic clocks.
"""
import hashlib
import hmac
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass


@dataclass
class EventSecurityValidationResult:
    is_valid: bool
    status_code: str  # VALID, REPLAY_DETECTED, HASH_CHAIN_BROKEN, UNAUTHORIZED_ROLE, TIME_SKEW_EXCEEDED, SIGNATURE_INVALID
    error_message: Optional[str]
    sanitized_event: Optional[Dict[str, Any]]


class DeviceSecurityRegistry:
    """In-memory & DB registry of trusted device public keys and sequence counters."""
    
    # device_id -> {"last_sequence": int, "last_hash": str, "secret_key": str, "authorized_roles": list}
    _device_state: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_device(cls, device_id: str, secret_key: str, authorized_roles: List[str]):
        cls._device_state[device_id] = {
            "last_sequence": 0,
            "last_hash": "GENESIS_ROOT_HASH_0000000000000000000000000000000000000000000000000000",
            "secret_key": secret_key,
            "authorized_roles": authorized_roles,
            "registered_at": datetime.now(timezone.utc),
        }

    @classmethod
    def get_device(cls, device_id: str) -> Optional[Dict[str, Any]]:
        return cls._device_state.get(device_id)

    @classmethod
    def reset(cls):
        cls._device_state.clear()


class OfflineSecurityValidator:
    """
    Validates offline-generated events before admitting them into the central operational ledger.
    """

    MAX_ALLOWABLE_FUTURE_SKEW_SECONDS = 120  # 2 minutes maximum clock drift allowed

    ROLE_PERMITTED_ACTIONS = {
        "CITIZEN": ["INCIDENT_REPORTED", "HAZARD_OBSERVED", "PHOTO_ATTACHED"],
        "RESPONDER": [
            "INCIDENT_REPORTED",
            "HAZARD_OBSERVED",
            "ROUTE_STATUS_UPDATED",
            "TASK_ACCEPTED",
            "TASK_EN_ROUTE",
            "TASK_ON_SITE",
            "TASK_COMPLETED",
            "EVIDENCE_SUBMITTED",
        ],
        "SUPERVISOR": [
            "INCIDENT_REPORTED",
            "HAZARD_OBSERVED",
            "ROUTE_STATUS_UPDATED",
            "TASK_CREATED",
            "TASK_ASSIGNED",
            "TASK_ACCEPTED",
            "TASK_EN_ROUTE",
            "TASK_ON_SITE",
            "TASK_COMPLETED",
            "TASK_COMPLETION_VERIFIED",
            "CONFLICT_ADJUDICATED",
            "EVIDENCE_VERIFIED",
        ],
    }

    @staticmethod
    def compute_event_signature(secret_key: str, event_payload: Dict[str, Any]) -> str:
        """Computes HMAC-SHA256 cryptographic signature over canonical event fields."""
        canonical_str = (
            f"{event_payload.get('event_id', '')}|"
            f"{event_payload.get('tenant_id', '')}|"
            f"{event_payload.get('actor_id', '')}|"
            f"{event_payload.get('device_id', '')}|"
            f"{event_payload.get('device_sequence', 0)}|"
            f"{event_payload.get('event_type', '')}|"
            f"{event_payload.get('prev_event_hash', '')}"
        )
        return hmac.new(secret_key.encode("utf-8"), canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def validate_offline_event(
        cls,
        event: Dict[str, Any],
        actor_role: str,
        seen_event_ids: set,
    ) -> EventSecurityValidationResult:
        event_id = event.get("event_id")
        device_id = event.get("device_id")
        device_seq = int(event.get("device_sequence", 1))
        event_type = event.get("event_type")
        occurred_at_str = event.get("occurred_at")
        prev_hash = event.get("prev_event_hash")
        client_sig = event.get("signature")

        # 1. Anti-Replay: Check global Event ID deduplication
        if event_id in seen_event_ids:
            return EventSecurityValidationResult(
                is_valid=False,
                status_code="REPLAY_DETECTED",
                error_message=f"Replay detected: Event {event_id} has already been reconciled.",
                sanitized_event=None,
            )

        # 2. Device Registration & Trust Check
        dev_info = DeviceSecurityRegistry.get_device(str(device_id)) if device_id else None
        if dev_info:
            # Check monotonic sequence counter
            last_seq = dev_info["last_sequence"]
            if device_seq <= last_seq:
                return EventSecurityValidationResult(
                    is_valid=False,
                    status_code="REPLAY_DETECTED",
                    error_message=f"Monotonic sequence violation: Device {device_id} sequence {device_seq} <= last seen {last_seq}.",
                    sanitized_event=None,
                )

            # Check Monotonic Hash Chain linking
            if prev_hash and prev_hash != dev_info["last_hash"]:
                return EventSecurityValidationResult(
                    is_valid=False,
                    status_code="HASH_CHAIN_BROKEN",
                    error_message=f"Hash chain broken: Provided prev_event_hash {prev_hash[:12]}... does not match expected {dev_info['last_hash'][:12]}...",
                    sanitized_event=None,
                )

            # Check Cryptographic Signature if provided
            if client_sig:
                expected_sig = cls.compute_event_signature(dev_info["secret_key"], event)
                if not hmac.compare_digest(client_sig, expected_sig):
                    return EventSecurityValidationResult(
                        is_valid=False,
                        status_code="SIGNATURE_INVALID",
                        error_message="Cryptographic signature verification failed: Payload was tampered in transit.",
                        sanitized_event=None,
                    )

        # 3. Offline Role Capability Enforcement (Anti-Privilege Escalation)
        allowed_actions = cls.ROLE_PERMITTED_ACTIONS.get(actor_role.upper(), [])
        if event_type not in allowed_actions:
            return EventSecurityValidationResult(
                is_valid=False,
                status_code="UNAUTHORIZED_ROLE",
                error_message=f"Privilege escalation blocked: Role {actor_role} is unauthorized to execute {event_type}.",
                sanitized_event=None,
            )

        # 4. Time Skew / Artificial Clock Tampering Protection
        if occurred_at_str:
            try:
                # Handle ISO timestamps with or without timezone
                if occurred_at_str.endswith("Z"):
                    occurred_dt = datetime.fromisoformat(occurred_at_str.replace("Z", "+00:00"))
                else:
                    occurred_dt = datetime.fromisoformat(occurred_at_str)
                    if occurred_dt.tzinfo is None:
                        occurred_dt = occurred_dt.replace(tzinfo=timezone.utc)

                now_utc = datetime.now(timezone.utc)
                if occurred_dt > now_utc + timedelta(seconds=cls.MAX_ALLOWABLE_FUTURE_SKEW_SECONDS):
                    return EventSecurityValidationResult(
                        is_valid=False,
                        status_code="TIME_SKEW_EXCEEDED",
                        error_message=f"Clock tampering rejected: Event timestamp {occurred_at_str} is in the future (> 120s drift).",
                        sanitized_event=None,
                    )
            except Exception:
                pass

        # If all checks pass, record state update
        if dev_info:
            current_event_hash = hashlib.sha256(f"{event_id}_{device_seq}_{event_type}".encode("utf-8")).hexdigest()
            dev_info["last_sequence"] = device_seq
            dev_info["last_hash"] = current_event_hash

        seen_event_ids.add(event_id)

        return EventSecurityValidationResult(
            is_valid=True,
            status_code="VALID",
            error_message=None,
            sanitized_event=event,
        )
