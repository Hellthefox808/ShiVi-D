"""
ShiVi Resilience, Deadlock Mitigation, Circuit Breaker & Loop Prevention Engine
"""
import asyncio
import random
import time
import logging
from typing import Callable, Any, TypeVar, Optional, Dict, List
from functools import wraps
from enum import Enum
from pydantic import BaseModel
from datetime import datetime, timezone

logger = logging.getLogger("shivi.resilience")

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Failing, fast-reject requests
    HALF_OPEN = "HALF_OPEN" # Testing canary requests


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted on an open circuit breaker."""
    pass


class LoopDetectedException(Exception):
    """Raised when a cyclic event sync or infinite propagation loop is detected."""
    pass


class PoisonPillException(Exception):
    """Raised when an unprocessable message is quarantined to the Dead Letter Queue."""
    pass


class DeadlockRetryPolicy:
    """
    Executes database operations with exponential backoff and full jitter
    to resolve transient concurrency deadlocks and lock contention.
    """
    @staticmethod
    async def execute_with_retry(
        func: Callable[..., Any],
        *args: Any,
        max_retries: int = 5,
        base_delay_ms: int = 20,
        max_delay_ms: int = 500,
        **kwargs: Any,
    ) -> Any:
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                is_deadlock = any(
                    sig in err_str
                    for sig in [
                        "deadlock",
                        "database is locked",
                        "lock not available",
                        "could not obtain lock",
                        "40p01",
                        "55p03",
                    ]
                )
                if not is_deadlock or attempt == max_retries:
                    raise e

                last_exception = e
                # Full Jitter Backoff Formula: sleep = random(0, min(max_delay, base_delay * 2^attempt))
                backoff_cap = min(max_delay_ms, base_delay_ms * (2 ** attempt))
                jitter_sleep = random.uniform(base_delay_ms / 1000.0, backoff_cap / 1000.0)
                logger.warning(
                    f"[DEADLOCK_RETRY] Concurrency contention detected (attempt {attempt}/{max_retries}). "
                    f"Retrying in {jitter_sleep * 1000:.1f}ms..."
                )
                await asyncio.sleep(jitter_sleep)

        raise last_exception or RuntimeError("Exceeded maximum deadlock retry attempts.")


class CircuitBreaker:
    """
    Protects integrations, database gateways, and network sync from cascading failure loops.
    """
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 10.0,
        success_threshold: int = 1,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time > self.recovery_timeout_seconds:
                logger.info(f"[CIRCUIT_BREAKER] {self.name} transitioned from OPEN to HALF_OPEN (probing canary).")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        return True

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info(f"[CIRCUIT_BREAKER] {self.name} recovered. State: CLOSED.")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            self.failure_count = 0

    def record_failure(self):
        self.last_failure_time = time.time()
        self.failure_count += 1
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            logger.error(f"[CIRCUIT_BREAKER] {self.name} failure threshold reached ({self.failure_count}). State: OPEN.")
            self.state = CircuitState.OPEN

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if not self.can_execute():
            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.name}' is OPEN. Fast-failing request to prevent cascading failure."
            )
        try:
            res = await func(*args, **kwargs)
            self.record_success()
            return res
        except Exception as e:
            self.record_failure()
            raise e


class DeadLetterQueueEntry(BaseModel):
    id: str
    tenant_id: str
    event_id: str
    payload: Dict[str, Any]
    error_message: str
    quarantined_at: datetime
    retry_count: int


class DeadLetterQueue:
    """
    Isolates poisoned/malformed payloads to prevent tight retry spin loops.
    """
    _quarantine: List[DeadLetterQueueEntry] = []

    @classmethod
    def isolate_poison_pill(
        cls,
        tenant_id: str,
        event_id: str,
        payload: Dict[str, Any],
        error: str,
        retry_count: int = 3,
    ) -> DeadLetterQueueEntry:
        entry = DeadLetterQueueEntry(
            id=f"DLQ-{int(time.time()*1000)}-{event_id[:8]}",
            tenant_id=tenant_id,
            event_id=event_id,
            payload=payload,
            error_message=error,
            quarantined_at=datetime.now(timezone.utc),
            retry_count=retry_count,
        )
        cls._quarantine.append(entry)
        logger.error(f"[DLQ_QUARANTINE] Event {event_id} isolated into Dead Letter Queue. Reason: {error}")
        return entry

    @classmethod
    def get_quarantined_entries(cls) -> List[DeadLetterQueueEntry]:
        return list(cls._quarantine)

    @classmethod
    def clear_quarantine(cls):
        cls._quarantine.clear()


class LoopGuard:
    """
    Prevents cyclic causal sync loops and unbounded event ping-ponging across mesh nodes.
    """
    MAX_SYNC_HOPS = 5

    @classmethod
    def check_event_loop(
        cls,
        event_id: str,
        origin_device_id: str,
        target_device_id: str,
        hop_count: int = 0,
        traversed_nodes: Optional[List[str]] = None,
    ) -> bool:
        """
        Validates whether an event transmission forms a closed causal loop.
        Returns True if safe; raises LoopDetectedException if a cycle is detected.
        """
        if hop_count > cls.MAX_SYNC_HOPS:
            raise LoopDetectedException(
                f"Event {event_id} exceeded maximum allowed causal sync hops ({cls.MAX_SYNC_HOPS}). Terminating propagation loop."
            )

        if origin_device_id == target_device_id and hop_count > 0:
            raise LoopDetectedException(
                f"Causal cycle detected: Event {event_id} looped back to origin node {origin_device_id}."
            )

        if traversed_nodes and target_device_id in traversed_nodes:
            raise LoopDetectedException(
                f"Causal cycle detected: Node {target_device_id} has already processed event {event_id} in path {traversed_nodes}."
            )

        return True


class DeterministicLockOrdering:
    """
    Eliminates database deadlocks by enforcing lexicographical key ordering
    for all multi-resource locking operations.
    """
    @staticmethod
    def get_ordered_keys(*resource_ids: str) -> List[str]:
        """
        Sorts arbitrary resource IDs into a global deterministic order.
        Any transaction locking resources A and B will always lock in sequence: min(A, B) -> max(A, B).
        """
        return sorted([r for r in resource_ids if r])


class ResiliencyManager:
    """Central manager for circuit breakers, DLQ queues, and lock coordination."""
    _circuits: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get_circuit_breaker(cls, service_name: str) -> CircuitBreaker:
        if service_name not in cls._circuits:
            cls._circuits[service_name] = CircuitBreaker(service_name)
        return cls._circuits[service_name]

    @classmethod
    def get_circuit_state(cls, service_name: str) -> str:
        cb = cls.get_circuit_breaker(service_name)
        return cb.state.value

    @classmethod
    def get_dlq_metrics(cls) -> Dict[str, Any]:
        entries = DeadLetterQueue.get_quarantined_entries()
        return {
            "total_quarantined": len(entries),
            "quarantined_event_ids": [e.event_id for e in entries],
        }
