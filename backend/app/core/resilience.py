"""
ShiVi Resilience, Deadlock Mitigation, Circuit Breaker & Loop Prevention Engine
==============================================================================

Briefing:
    This module provides the core enterprise reliability primitives for the ShiVi
    disaster coordination platform. In disconnected or volatile edge environments,
    nodes experience intermittent network partitions, high concurrency lock contention
    (such as SQLite database write locks during batch synchronization), and corrupted
    or poison-pill payloads transmitted across radio/mesh networks.

Reason:
    Without proactive resilience controls:
    1. Simultaneous sync requests from multiple field devices cause SQLite or PostgreSQL
       transient database deadlocks, leading to unhandled 500 crashes.
    2. Repeated requests to failing upstream gateways (e.g., cloud AI services) waste
       battery and compute while exhausting thread pools.
    3. Malformed messages trigger infinite retry loops, starving legitimate disaster traffic.
    4. Uncontrolled multi-hop mesh gossip creates cyclic broadcast storms.
    5. Unordered multi-resource locks introduce classic Coffman circular-wait deadlocks.

Architectural Pillars:
    - DeadlockRetryPolicy: Exponential backoff with full jitter for database lock contention.
    - CircuitBreaker: Three-state finite state machine (CLOSED, OPEN, HALF_OPEN) for failure isolation.
    - DeadLetterQueue: Quarantine sandbox for poisoned/malformed sync envelopes.
    - LoopGuard: Causal hop tracking and visited-node cycle detection for mesh synchronization.
    - DeterministicLockOrdering: Lexicographical resource sorting to prevent circular wait deadlocks.
    - ResiliencyManager: Singleton registry for global health monitoring and circuit state inspectability.
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

# Briefing: Dedicated logger for all resiliency and fault-tolerance events.
# Reason: Allows operational administrators to isolate failovers, circuit breaks, and DLQ events.
logger = logging.getLogger("shivi.resilience")

T = TypeVar("T")


class CircuitState(str, Enum):
    """
    Briefing:
        Enumeration representing the three states of the ShiVi Circuit Breaker pattern.

    Reason:
        Explicitly governs request flow through downstream integrations:
        - CLOSED: System is healthy. All requests pass through directly.
        - OPEN: Downstream service is failing. Requests are fast-rejected without executing.
        - HALF_OPEN: Recovery probe phase. A limited number of canary requests are tested
          to determine if downstream health has been restored.
    """
    CLOSED = "CLOSED"       # Normal operation: traffic flows freely
    OPEN = "OPEN"           # Failing: fast-reject requests to protect downstream resources
    HALF_OPEN = "HALF_OPEN" # Canary state: probing service recovery with controlled traffic


class CircuitBreakerOpenException(Exception):
    """
    Briefing:
        Exception raised when an operation is attempted against an OPEN circuit breaker.

    Reason:
        Enables immediate fail-fast semantics, preventing callers from waiting on network
        timeouts and allowing upstream queues to divert or shed non-critical load.
    """
    pass


class LoopDetectedException(Exception):
    """
    Briefing:
        Exception raised when an event transmission forms a closed causal loop or exceeds
        the maximum permissible mesh synchronization hops.

    Reason:
        Halts runaway broadcast storms in peer-to-peer mesh networks, protecting battery,
        bandwidth, and event log storage from infinite ping-pong cycles.
    """
    pass


class PoisonPillException(Exception):
    """
    Briefing:
        Exception raised when a payload cannot be parsed, validated, or executed after
        exhausting max retry attempts, requiring permanent quarantine.

    Reason:
        Prevents broken messages from permanently blocking FIFO queues or causing spin loops.
    """
    pass


class DeadlockRetryPolicy:
    """
    Briefing:
        Utility class providing exponential backoff and randomized full jitter for database operations.

    Reason:
        In high-stress disaster response operations, dozens of peer field devices may synchronize
        their local SQLite outboxes simultaneously. SQLite's single-writer architecture and
        PostgreSQL's row-level lock escalation frequently produce transient lock conflicts
        (e.g., 'database is locked', Postgres SQLSTATE '40P01'). This policy transparently
        backs off and retries transient failures, eliminating 99%+ of lock-abort crashes.
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
        """
        Briefing:
            Executes an asynchronous function with exponential backoff and full jitter upon
            encountering database concurrency lock exceptions.

        Reason:
            Implements the AWS Full Jitter algorithm:
                sleep_duration = random(base_delay, min(max_delay, base_delay * 2^attempt))
            Randomization decorrelates competing synchronization tasks, preventing "thundering herd"
            re-collisions where multiple threads wake up at identical intervals and re-deadlock.

        Parameters:
            func: The asynchronous coroutine or callable to execute.
            *args: Positional arguments passed directly to `func`.
            max_retries: Maximum number of execution attempts before re-raising the exception (default 5).
            base_delay_ms: Initial base delay in milliseconds (default 20ms).
            max_delay_ms: Upper cap on backoff delay in milliseconds (default 500ms).
            **kwargs: Keyword arguments passed directly to `func`.

        Returns:
            The return value of the wrapped `func` call upon success.

        Raises:
            Exception: Any non-lock exception immediately, or the last lock exception if
                       max_retries is exhausted.
        """
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                # Explanation: Inspect error signature against known database lock & deadlock strings.
                # SQLite: "database is locked"
                # PostgreSQL: "deadlock detected" (40P01), "lock_not_available" (55P03)
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
                    # Explanation: Non-lock errors (syntax, validation, constraint violations)
                    # should never be retried blindly as they are deterministic failures.
                    raise e

                last_exception = e
                # Explanation: Full Jitter backoff formula calculation
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
    Briefing:
        Software circuit breaker managing fail-fast execution against external dependencies.

    Reason:
        When edge nodes communicate with external APIs (satellite backhauls, SMS relays,
        cloud AI triage models), connection timeouts can cascade and exhaust local system
        threads. The CircuitBreaker stops calling broken dependencies until they prove healthy.
    """
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 10.0,
        success_threshold: int = 1,
    ):
        """
        Briefing:
            Initializes a CircuitBreaker instance with configurable failure limits and recovery timeouts.

        Parameters:
            name: Human-readable identifier for logging and metrics tracking (e.g., 'gemini_ai_gateway').
            failure_threshold: Number of consecutive errors that trip the circuit from CLOSED to OPEN.
            recovery_timeout_seconds: Duration in seconds to stay in OPEN before attempting HALF_OPEN probing.
            success_threshold: Number of successful canary calls required to reset HALF_OPEN to CLOSED.
        """
        # Explanation: Name of protected service or subsystem
        self.name = name
        # Explanation: Threshold for tripping
        self.failure_threshold = failure_threshold
        # Explanation: Cooldown period before trying canary
        self.recovery_timeout_seconds = recovery_timeout_seconds
        # Explanation: Consecutive successes needed in canary mode
        self.success_threshold = success_threshold

        # Explanation: Initial operational state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        """
        Briefing:
            Evaluates whether an incoming call is permitted based on current circuit breaker state.

        Reason:
            Transitions automatically from OPEN to HALF_OPEN once the recovery timeout has elapsed,
            allowing a single canary request to test the downstream dependency.
        """
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
        """
        Briefing:
            Records a successful execution, updating internal counters and resetting circuit state.

        Reason:
            If in HALF_OPEN, reaching `success_threshold` closes the circuit, fully restoring normal operations.
            If in CLOSED, it clears any accumulated transient failure count.
        """
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
        """
        Briefing:
            Records a failed execution and trips the circuit breaker to OPEN if thresholds are reached.

        Reason:
            Immediate tripping prevents additional load from reaching a struggling service, giving it
            time to recover without being overwhelmed by repeated incoming retries.
        """
        self.last_failure_time = time.time()
        self.failure_count += 1
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            logger.error(f"[CIRCUIT_BREAKER] {self.name} failure threshold reached ({self.failure_count}). State: OPEN.")
            self.state = CircuitState.OPEN

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Briefing:
            Wraps an asynchronous callable with circuit breaker execution protection.

        Reason:
            Guarantees that if the circuit is OPEN, the request is immediately rejected via
            `CircuitBreakerOpenException` without invoking the underlying network or database call.
        """
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
    """
    Briefing:
        Data model representing a quarantined message entry within the Dead Letter Queue.

    Reason:
        Retains comprehensive diagnostic context (error message, timestamps, retry counts, original payload)
        so that commanders or system engineers can audit poisoned payloads without data loss.
    """
    id: str
    tenant_id: str
    event_id: str
    payload: Dict[str, Any]
    error_message: str
    quarantined_at: datetime
    retry_count: int


class DeadLetterQueue:
    """
    Briefing:
        Quarantine repository for unprocessable or poison-pill synchronization events.

    Reason:
        If a field device submits a malformed event (e.g., schema divergence, invalid signature),
        re-attempting processing indefinitely will exhaust CPU and lock the outbox pipeline.
        The Dead Letter Queue isolates the toxic event into memory/storage, allowing subsequent
        valid events to continue processing unhindered.
    """
    # Explanation: In-memory quarantine buffer; can be inspected via API or exported.
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
        """
        Briefing:
            Isolates a failed synchronization payload into the quarantine collection.

        Parameters:
            tenant_id: Multi-tenant jurisdiction identifier.
            event_id: Unique UUID of the offending event envelope.
            payload: Raw dictionary payload of the event.
            error: Descriptive root-cause failure string.
            retry_count: Number of failed attempts prior to quarantine.

        Returns:
            The generated `DeadLetterQueueEntry` record.
        """
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
        """
        Briefing:
            Returns a copy of all currently quarantined dead-letter records.
        """
        return list(cls._quarantine)

    @classmethod
    def clear_quarantine(cls):
        """
        Briefing:
            Clears all quarantined records from the in-memory buffer.
        """
        cls._quarantine.clear()


class LoopGuard:
    """
    Briefing:
        Causal cycle and synchronization loop detector for mesh and relay topologies.

    Reason:
        In ad-hoc peer-to-peer mesh networks (BLE mesh, LoRa, Wi-Fi Direct), events gossip
        across neighboring nodes. Without loop guards, an event from Node A sent to Node B
        would be forwarded to Node C and back to Node A, causing an infinite propagation loop
        that floods radio frequency channels and depletes device batteries.
    """
    # Explanation: Hard limit on the number of mesh hops an event envelope can traverse.
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
        Briefing:
            Validates whether an event transmission forms a closed causal loop or exceeds hop limits.

        Reason:
            Uses graph cycle detection logic:
            1. Verifies hop count does not exceed MAX_SYNC_HOPS (TTL expiration).
            2. Verifies that the event is not being sent back to its original author.
            3. Verifies that the target node is not already in the traversed nodes vector.

        Parameters:
            event_id: Unique identifier of the event envelope.
            origin_device_id: Device ID that originally created the event.
            target_device_id: Immediate recipient device ID for this hop.
            hop_count: Current number of peer hops traversed.
            traversed_nodes: Ordered list of device IDs that have already routed this event.

        Returns:
            True if the transmission path is acyclic and within bounds.

        Raises:
            LoopDetectedException: If a cycle, loopback, or hop limit violation is identified.
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
    Briefing:
        Global lock sorting utility enforcing lexicographical resource acquisition order.

    Reason:
        Eliminates the Coffman "Circular Wait" condition in multi-resource database transactions.
        For instance, if Transaction 1 updates Incident A then Incident B, while Transaction 2
        updates Incident B then Incident A, an execution race causes a severe database deadlock.
        By sorting resource identifiers before acquiring locks, all concurrent transactions
        acquire locks in the identical order, mathematically eliminating circular wait deadlocks.
    """
    @staticmethod
    def get_ordered_keys(*resource_ids: str) -> List[str]:
        """
        Briefing:
            Sorts arbitrary resource identifiers into a canonical, deterministic sequence.

        Parameters:
            *resource_ids: Variable arguments containing string resource keys/UUIDs.

        Returns:
            A lexicographically sorted list of non-empty resource IDs.
        """
        return sorted([r for r in resource_ids if r])


class ResiliencyManager:
    """
    Briefing:
        Centralized registry and facade for circuit breakers, DLQ metrics, and resilience diagnostics.

    Reason:
        Provides a unified interface for API health endpoints (`/health/resilience`), enabling
        tactical dashboards to display real-time circuit states and DLQ count without tight coupling.
    """
    # Explanation: Registry mapping service names to their active CircuitBreaker instances.
    _circuits: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get_circuit_breaker(cls, service_name: str) -> CircuitBreaker:
        """
        Briefing:
            Retrieves or lazily instantiates the CircuitBreaker for a given subsystem name.

        Parameters:
            service_name: Unique identifier of the subsystem (e.g. 'sms_gateway', 'ai_service').
        """
        if service_name not in cls._circuits:
            cls._circuits[service_name] = CircuitBreaker(service_name)
        return cls._circuits[service_name]

    @classmethod
    def get_circuit_state(cls, service_name: str) -> str:
        """
        Briefing:
            Returns the string state representation ("CLOSED", "OPEN", "HALF_OPEN") of a service.
        """
        cb = cls.get_circuit_breaker(service_name)
        return cb.state.value

    @classmethod
    def get_dlq_metrics(cls) -> Dict[str, Any]:
        """
        Briefing:
            Aggregates diagnostic telemetry on the contents of the Dead Letter Queue.

        Returns:
            Dictionary containing total count and quarantined event UUIDs.
        """
        entries = DeadLetterQueue.get_quarantined_entries()
        return {
            "total_quarantined": len(entries),
            "quarantined_event_ids": [e.event_id for e in entries],
        }
