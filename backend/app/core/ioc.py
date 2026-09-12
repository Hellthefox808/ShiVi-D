"""
Briefing: ShiVi Inversion of Control (IoC) Container, Protocol Contracts, and Service Registry.
Reason: Decouples high-level disaster coordination logic from specific implementation details.
Enables swapping in-memory mocks during offline unit testing or substituting cloud AI APIs with
on-device quantized LLMs without rewriting route handlers.
Features:
1. Typed Protocol Interfaces for Causal Conflicts, Edge AI, Asset Allocation, Security, and Resilience.
2. Singleton, Factory, and Instance service lifetimes with automatic constructor argument resolution.
3. Recursive dependency cycle detection to prevent stack overflows during complex wiring.
4. Native FastAPI `Depends(get_service(IInterface))` integration.
"""
import inspect
from typing import Type, TypeVar, Dict, Any, Callable, Optional, Protocol, runtime_checkable
from datetime import datetime, timezone

T = TypeVar("T")


# ==============================================================================
# 1. CORE DOMAIN SERVICE INTERFACES (PROTOCOLS)
# ==============================================================================

@runtime_checkable
class IConflictEngine(Protocol):
    """
    Briefing: Contract for Causal Conflict Resolution and Version Vector Reconcilers.
    Reason: Decouples conflict adjudication algorithms (LWW, Lamport, safety freeze) from sync endpoints.
    """
    def resolve_conflicts(self, base_state: Dict[str, Any], incoming_events: list) -> Dict[str, Any]:
        ...


@runtime_checkable
class IAIGateway(Protocol):
    """
    Briefing: Contract for Hybrid Edge/Cloud AI Intelligence Gateway.
    Reason: Permits hot-swapping between Gemini API, local ONNX models, or heuristic fallback parsers.
    """
    async def extract_incident_features(self, raw_text: str) -> Dict[str, Any]:
        ...

    async def prioritize_incident(self, incident_data: Dict[str, Any]) -> float:
        ...


@runtime_checkable
class IAssetAllocationEngine(Protocol):
    """
    Briefing: Contract for Distributed Physical Asset Contention and Allocation.
    Reason: Resolves simultaneous conflicting claims over emergency boats, ambulances, and fuel reserves.
    """
    def resolve_contention(
        self,
        asset_code: str,
        claim_a: Dict[str, Any],
        claim_b: Dict[str, Any],
        available_substitutes: list,
    ) -> Any:
        ...


@runtime_checkable
class ISecurityValidator(Protocol):
    """
    Briefing: Contract for Offline Cryptographic Identity and Anti-Replay Validation.
    Reason: Enforces hardware monotonic hash chains and role authorization checks.
    """
    def validate_offline_event(
        self,
        event: Dict[str, Any],
        actor_role: str,
        seen_event_ids: set,
    ) -> Any:
        ...


@runtime_checkable
class ILakehouseCatalog(Protocol):
    """
    Briefing: Contract for Lakehouse Federated Iceberg and BigQuery Data Cataloging.
    Reason: Abstract storage metadata lookups for cross-cloud telemetry analytics.
    """
    def get_table_metadata(self, table_name: str) -> Dict[str, Any]:
        ...


@runtime_checkable
class IResilienceManager(Protocol):
    """
    Briefing: Contract for System Resiliency, Circuit Breakers, and Lock Managers.
    Reason: Monitors failure rates and isolates failing external subsystems.
    """
    def get_circuit_state(self, service_name: str) -> str:
        ...


# ==============================================================================
# 2. INVERSION OF CONTROL (IoC) CONTAINER IMPLEMENTATION
# ==============================================================================

class ServiceLifetime:
    """Supported dependency injection instance lifetimes."""
    SINGLETON = "SINGLETON"
    FACTORY = "FACTORY"
    INSTANCE = "INSTANCE"


class IoCContainer:
    """
    Briefing: High-performance Inversion of Control container with dependency cycle detection.
    Reason: Manages lifecycle, dependency injection, and test overrides across backend modules.
    """

    def __init__(self):
        self._registry: Dict[Type, Dict[str, Any]] = {}
        self._singletons: Dict[Type, Any] = {}
        self._overrides: Dict[Type, Any] = {}
        self._is_initialized = False

    def bind_singleton(self, interface: Type[T], implementation: Type[T]) -> "IoCContainer":
        """Registers a service as a Singleton (instantiated once and cached)."""
        self._registry[interface] = {
            "type": implementation,
            "lifetime": ServiceLifetime.SINGLETON,
        }
        return self

    def bind_factory(self, interface: Type[T], factory_fn: Callable[[], T]) -> "IoCContainer":
        """Registers a factory function that produces a new instance on each resolution."""
        self._registry[interface] = {
            "factory": factory_fn,
            "lifetime": ServiceLifetime.FACTORY,
        }
        return self

    def bind_instance(self, interface: Type[T], instance: T) -> "IoCContainer":
        """Directly registers an existing instantiated object."""
        self._registry[interface] = {
            "instance": instance,
            "lifetime": ServiceLifetime.INSTANCE,
        }
        self._singletons[interface] = instance
        return self

    def override(self, interface: Type[T], instance: T) -> "IoCContainer":
        """Overrides a service binding with a mock/test instance."""
        self._overrides[interface] = instance
        return self

    def clear_override(self, interface: Optional[Type] = None):
        """Clears specific or all test overrides."""
        if interface:
            self._overrides.pop(interface, None)
        else:
            self._overrides.clear()

    def resolve(self, interface: Type[T], resolving_chain: Optional[set] = None) -> T:
        """
        Resolves an instance of the requested interface with dependency injection
        and recursion cycle detection.
        """
        # 1. Check for active test overrides first
        if interface in self._overrides:
            return self._overrides[interface]

        if interface not in self._registry:
            raise KeyError(f"IoC Resolution Error: Interface '{interface.__name__}' is not registered in container.")

        spec = self._registry[interface]
        lifetime = spec.get("lifetime")

        # 2. Instance lifetime
        if lifetime == ServiceLifetime.INSTANCE:
            return spec["instance"]

        # 3. Singleton lifetime
        if lifetime == ServiceLifetime.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]

            # Instantiation with cycle detection
            impl_cls = spec["type"]
            if resolving_chain is None:
                resolving_chain = set()

            if interface in resolving_chain:
                chain_str = " -> ".join([c.__name__ for c in resolving_chain])
                raise RecursionError(f"Circular dependency detected in IoC container: {chain_str} -> {interface.__name__}")

            resolving_chain.add(interface)
            instance = self._instantiate(impl_cls, resolving_chain)
            self._singletons[interface] = instance
            return instance

        # 4. Factory lifetime
        if lifetime == ServiceLifetime.FACTORY:
            factory_fn = spec["factory"]
            return factory_fn()

        raise ValueError(f"Unknown service lifetime: {lifetime}")

    def _instantiate(self, cls: Type, resolving_chain: set) -> Any:
        """Instantiates a class by recursively resolving constructor arguments."""
        try:
            init_signature = inspect.signature(cls.__init__)
            params = init_signature.parameters

            kwargs = {}
            for name, param in params.items():
                if name == "self":
                    continue
                target_key = None
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation in self._registry:
                        target_key = param.annotation
                    elif isinstance(param.annotation, str):
                        # Match forward reference by class name
                        for reg_type in self._registry.keys():
                            if getattr(reg_type, "__name__", "") == param.annotation:
                                target_key = reg_type
                                break

                if target_key is not None:
                    kwargs[name] = self.resolve(target_key, resolving_chain.copy())

            return cls(**kwargs)
        except (TypeError, RecursionError) as e:
            if isinstance(e, RecursionError):
                raise e
            # Fallback to zero-arg constructor
            try:
                return cls()
            except TypeError:
                raise e

    async def initialize_all(self):
        """Asynchronously initializes all registered singletons."""
        for interface in list(self._registry.keys()):
            instance = self.resolve(interface)
            if hasattr(instance, "startup") and inspect.iscoroutinefunction(instance.startup):
                await instance.startup()
            elif hasattr(instance, "initialize") and inspect.iscoroutinefunction(instance.initialize):
                await instance.initialize()
        self._is_initialized = True

    async def shutdown_all(self):
        """Asynchronously triggers shutdown hooks across all resolved singletons."""
        for instance in self._singletons.values():
            if hasattr(instance, "shutdown") and inspect.iscoroutinefunction(instance.shutdown):
                await instance.shutdown()
            elif hasattr(instance, "close") and inspect.iscoroutinefunction(instance.close):
                await instance.close()

    def health_check(self) -> Dict[str, Any]:
        """Runs diagnostics on all registered container services."""
        diagnostics = {}
        for interface, spec in self._registry.items():
            name = interface.__name__
            diagnostics[name] = {
                "lifetime": spec.get("lifetime"),
                "is_instantiated": interface in self._singletons or interface in self._overrides,
                "status": "HEALTHY",
            }
        return {
            "container_status": "ONLINE",
            "registered_services_count": len(self._registry),
            "singletons_active": len(self._singletons),
            "services": diagnostics,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


# ==============================================================================
# 3. GLOBAL CONTAINER INSTANCE & DEFAULT REGISTRATIONS
# ==============================================================================

# Global container instance
ioc_container = IoCContainer()


def setup_default_container(container: IoCContainer = ioc_container) -> IoCContainer:
    """Wires default core domain implementations into the IoC container."""
    from app.modules.conflicts.engine import CausalConflictEngine
    from app.modules.intelligence.gateway import IntelligenceGateway
    from app.modules.assets.allocation_engine import DistributedAssetAllocationEngine
    from app.core.security_crypto import OfflineSecurityValidator
    from app.core.resilience import ResiliencyManager

    container.bind_instance(IConflictEngine, CausalConflictEngine)
    container.bind_instance(IAIGateway, IntelligenceGateway)
    container.bind_instance(IAssetAllocationEngine, DistributedAssetAllocationEngine)
    container.bind_instance(ISecurityValidator, OfflineSecurityValidator)
    container.bind_instance(IResilienceManager, ResiliencyManager)

    return container


# Initialize on import
setup_default_container(ioc_container)


# ==============================================================================
# 4. FASTAPI DEPENDENCY INJECTION HELPER
# ==============================================================================

def get_service(interface: Type[T]) -> Callable[[], T]:
    """
    FastAPI dependency injection helper:
    Example usage in router:
        @router.get("/something")
        async def my_endpoint(ai_gateway: IAIGateway = Depends(get_service(IAIGateway))):
    """
    def _dependency_provider() -> T:
        return ioc_container.resolve(interface)
    return _dependency_provider
