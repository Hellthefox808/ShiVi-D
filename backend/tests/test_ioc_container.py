"""
Tests for Inversion of Control (IoC) Container & Service Registry
Verifies singleton, factory, cycle detection, overrides, and Protocol resolution.
"""
import pytest
from typing import Protocol
from app.core.ioc import (
    IoCContainer,
    ServiceLifetime,
    IConflictEngine,
    IAIGateway,
    IAssetAllocationEngine,
    ISecurityValidator,
    IResilienceManager,
    setup_default_container,
)


class IDummyService(Protocol):
    def ping(self) -> str:
        ...


class DummyServiceImpl:
    def ping(self) -> str:
        return "pong"


class CircularServiceA:
    def __init__(self, service_b: "CircularServiceB"):
        self.service_b = service_b


class CircularServiceB:
    def __init__(self, service_a: CircularServiceA):
        self.service_a = service_a


def test_ioc_singleton_resolution():
    container = IoCContainer()
    container.bind_singleton(IDummyService, DummyServiceImpl)

    inst1 = container.resolve(IDummyService)
    inst2 = container.resolve(IDummyService)

    assert inst1 is inst2
    assert inst1.ping() == "pong"


def test_ioc_factory_resolution():
    container = IoCContainer()
    counter = 0

    def make_dummy():
        nonlocal counter
        counter += 1
        return DummyServiceImpl()

    container.bind_factory(IDummyService, make_dummy)

    inst1 = container.resolve(IDummyService)
    inst2 = container.resolve(IDummyService)

    assert inst1 is not inst2
    assert counter == 2


def test_ioc_test_override_and_clear():
    container = IoCContainer()
    container.bind_singleton(IDummyService, DummyServiceImpl)

    class MockDummy:
        def ping(self) -> str:
            return "mock_pong"

    # Set override
    container.override(IDummyService, MockDummy())
    assert container.resolve(IDummyService).ping() == "mock_pong"

    # Clear override
    container.clear_override(IDummyService)
    assert container.resolve(IDummyService).ping() == "pong"


def test_ioc_circular_dependency_detection():
    container = IoCContainer()
    container.bind_singleton(CircularServiceA, CircularServiceA)
    container.bind_singleton(CircularServiceB, CircularServiceB)

    with pytest.raises(RecursionError) as exc_info:
        container.resolve(CircularServiceA)

    assert "Circular dependency detected" in str(exc_info.value)


def test_ioc_unregistered_interface_raises():
    container = IoCContainer()
    with pytest.raises(KeyError) as exc_info:
        container.resolve(IDummyService)

    assert "is not registered in container" in str(exc_info.value)


def test_default_ioc_container_wiring():
    container = setup_default_container(IoCContainer())
    diag = container.health_check()

    assert diag["container_status"] == "ONLINE"
    assert diag["registered_services_count"] >= 5

    conflict_engine = container.resolve(IConflictEngine)
    assert conflict_engine is not None

    security_validator = container.resolve(ISecurityValidator)
    assert security_validator is not None

    resilience_mgr = container.resolve(IResilienceManager)
    assert resilience_mgr is not None
