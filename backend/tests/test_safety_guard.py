"""
Tests for ShiVi Accidental Data Loss Prevention (ADLP) Safety Guard
"""
import pytest
import os
from app.core.safety import ADLPSafetyGuard, ProductionDataLossError


def test_production_database_detection():
    prod_urls = [
        "postgresql+asyncpg://admin:secret@shivi-prod.postgres.database.azure.com:5432/shivi",
        "postgresql+asyncpg://admin:secret@production-db.azure.com:5432/shivi",
        "postgresql+asyncpg://admin:secret@shivi.rds.amazonaws.com:5432/shivi",
    ]
    for url in prod_urls:
        assert ADLPSafetyGuard.is_production_database(url) is True


def test_local_sqlite_is_not_production():
    assert ADLPSafetyGuard.is_production_database("sqlite+aiosqlite:///./shivi_local.db") is False
    assert ADLPSafetyGuard.is_production_database("postgresql+asyncpg://localhost:5432/shivi_dev") is False


def test_destructive_operation_blocked_on_prod():
    prod_url = "postgresql+asyncpg://admin:secret@shivi-prod.postgres.database.azure.com:5432/shivi"
    with pytest.raises(ProductionDataLossError) as exc_info:
        ADLPSafetyGuard.verify_safe_for_destructive_operation("DROP_DATABASE", prod_url)
    assert "CRITICAL SAFETY BLOCK" in str(exc_info.value)


def test_destructive_operation_requires_allow_reset_flag():
    local_url = "sqlite+aiosqlite:///./shivi_test.db"
    # Ensure env var is not set
    if "ALLOW_DATA_RESET" in os.environ:
        del os.environ["ALLOW_DATA_RESET"]

    with pytest.raises(ProductionDataLossError) as exc_info:
        ADLPSafetyGuard.verify_safe_for_destructive_operation("TRUNCATE_TABLES", local_url)
    assert "ALLOW_DATA_RESET=1" in str(exc_info.value)


def test_destructive_operation_allowed_when_explicitly_flagged():
    local_url = "sqlite+aiosqlite:///./shivi_test.db"
    os.environ["ALLOW_DATA_RESET"] = "1"
    try:
        # Should not raise
        ADLPSafetyGuard.verify_safe_for_destructive_operation("TRUNCATE_TABLES", local_url)
    finally:
        del os.environ["ALLOW_DATA_RESET"]


def test_soft_delete_audit_tombstone():
    audit_record = ADLPSafetyGuard.audit_soft_delete(
        entity_name="incident",
        entity_id="inc-99",
        actor_id="user-01",
        reason="Duplicate entry merged into inc-01",
    )
    assert audit_record["action"] == "INCIDENT_SOFT_DELETED"
    assert audit_record["is_recoverable"] is True
    assert "deleted_at" in audit_record
