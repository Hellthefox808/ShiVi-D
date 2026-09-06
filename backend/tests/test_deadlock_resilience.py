"""
Tests for Deadlock Retry, Circuit Breaker, DLQ & Loop Guard
"""
import pytest
import asyncio
from app.core.resilience import (
    DeadlockRetryPolicy,
    CircuitBreaker,
    CircuitBreakerOpenException,
    DeadLetterQueue,
    LoopGuard,
    LoopDetectedException,
    DeterministicLockOrdering,
)
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_deadlock_retry_success_after_transient_failures():
    attempts = 0

    async def flaky_db_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("OperationalError: database is locked (Code 40P01)")
        return "SUCCESS_COMMITTED"

    result = await DeadlockRetryPolicy.execute_with_retry(
        flaky_db_operation,
        max_retries=5,
        base_delay_ms=10,
    )
    assert result == "SUCCESS_COMMITTED"
    assert attempts == 3


@pytest.mark.asyncio
async def test_deadlock_retry_exceeds_max_attempts():
    async def permanently_deadlocked_operation():
        raise RuntimeError("OperationalError: 40P01: deadlock detected")

    with pytest.raises(RuntimeError) as exc_info:
        await DeadlockRetryPolicy.execute_with_retry(
            permanently_deadlocked_operation,
            max_retries=3,
            base_delay_ms=5,
        )
    assert "deadlock" in str(exc_info.value).lower()


def test_deterministic_lock_ordering():
    # Order arbitrary resource IDs lexicographically
    res_a = "task-uuid-zzz"
    res_b = "task-uuid-aaa"
    res_c = "task-uuid-mmm"

    ordered = DeterministicLockOrdering.get_ordered_keys(res_a, res_b, res_c)
    assert ordered == ["task-uuid-aaa", "task-uuid-mmm", "task-uuid-zzz"]


@pytest.mark.asyncio
async def test_circuit_breaker_transitions():
    cb = CircuitBreaker("weather_api", failure_threshold=2, recovery_timeout_seconds=0.1)

    async def failing_call():
        raise ConnectionResetError("Remote server down")

    async def healthy_call():
        return {"temp": 28.5}

    # 1. First failure
    with pytest.raises(ConnectionResetError):
        await cb.call(failing_call)
    assert cb.can_execute() is True

    # 2. Second failure triggers OPEN state
    with pytest.raises(ConnectionResetError):
        await cb.call(failing_call)

    # 3. Third call fast-fails with CircuitBreakerOpenException without invoking func
    with pytest.raises(CircuitBreakerOpenException):
        await cb.call(failing_call)

    # 4. Wait for cooldown
    await asyncio.sleep(0.15)
    assert cb.can_execute() is True

    # 5. Success resets state to CLOSED
    res = await cb.call(healthy_call)
    assert res["temp"] == 28.5
    assert cb.state.value == "CLOSED"


def test_dead_letter_queue_quarantine():
    DeadLetterQueue.clear_quarantine()

    entry = DeadLetterQueue.isolate_poison_pill(
        tenant_id="00000000-0000-0000-0000-000000000001",
        event_id="EVT-POISON-001",
        payload={"corrupted": True, "syntax_error": "unmatched quote"},
        error="JSONDecodeError: Unterminated string",
    )

    assert entry.event_id == "EVT-POISON-001"
    entries = DeadLetterQueue.get_quarantined_entries()
    assert len(entries) == 1
    assert entries[0].event_id == "EVT-POISON-001"


def test_loop_guard_detects_cycles_and_max_hops():
    # 1. Normal single hop propagation -> Safe
    assert LoopGuard.check_event_loop(
        event_id="EVT-01",
        origin_device_id="DEV-A",
        target_device_id="SERVER",
        hop_count=1,
    ) is True

    # 2. Cycle back to origin node -> LoopDetectedException
    with pytest.raises(LoopDetectedException) as exc1:
        LoopGuard.check_event_loop(
            event_id="EVT-01",
            origin_device_id="DEV-A",
            target_device_id="DEV-A",
            hop_count=2,
        )
    assert "Causal cycle detected" in str(exc1.value)

    # 3. Max hops exceeded -> LoopDetectedException
    with pytest.raises(LoopDetectedException) as exc2:
        LoopGuard.check_event_loop(
            event_id="EVT-01",
            origin_device_id="DEV-A",
            target_device_id="DEV-F",
            hop_count=6,
        )
    assert "exceeded maximum allowed" in str(exc2.value)


@pytest.mark.asyncio
async def test_health_liveness_and_readiness_probes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Liveness
        res_live = await client.get("/v1/resilience/health/liveness")
        assert res_live.status_code == 200
        assert res_live.json()["status"] == "ALIVE"

        # Readiness
        res_ready = await client.get("/v1/resilience/health/readiness")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "READY"
        assert res_ready.json()["database"] == "CONNECTED"
