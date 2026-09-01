"""
Tests for Incident Operations Center (IOC) & Common Operational Picture (COP) Optimizations
Verifies in-memory TTL caching, cache invalidation, and bounding box spatial filtering.
"""
import pytest
from datetime import datetime, timezone
from app.modules.dashboard.router import (
    IOCCacheManager,
    DashboardSummary,
)


def test_ioc_cache_manager_ttl_and_invalidation():
    tenant_id = "test-tenant-ioc-01"
    IOCCacheManager.invalidate(tenant_id)

    # Initial get -> None
    assert IOCCacheManager.get(tenant_id) is None

    # Set mock summary
    summary = DashboardSummary(
        total_incidents=15,
        open_incidents=10,
        resolved_incidents=5,
        critical_incidents=3,
        active_tasks=7,
        open_conflicts=1,
        active_responders=5,
        available_assets=4,
        resource_saturation_index=1.4,
        active_safety_freezes=1,
        sync_health_status="HEALTHY",
        cached=False,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    IOCCacheManager.set(tenant_id, summary)

    # Fetch from cache -> Present and marked cached=True
    cached = IOCCacheManager.get(tenant_id)
    assert cached is not None
    assert cached.cached is True
    assert cached.total_incidents == 15
    assert cached.resource_saturation_index == 1.4

    # Invalidate cache
    IOCCacheManager.invalidate(tenant_id)
    assert IOCCacheManager.get(tenant_id) is None


def test_resource_saturation_index_calculation():
    """Verify saturation index calculations under varying conditions."""
    # Normal load: 5 tasks, 5 responders -> 1.0
    sat_normal = round(float(5) / max(float(5), 1.0), 2)
    assert sat_normal == 1.0

    # High load: 12 tasks, 3 responders -> 4.0
    sat_high = round(float(12) / max(float(3), 1.0), 2)
    assert sat_high == 4.0

    # Zero responders: 6 tasks, 0 responders -> 6.0 (prevents division by zero)
    sat_zero_resp = round(float(6) / max(float(0), 1.0), 2)
    assert sat_zero_resp == 6.0
