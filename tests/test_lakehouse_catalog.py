"""
Tests for Federated Lakehouse Catalog Integration
"""
import pytest
from app.modules.integrations.lakehouse import LakehouseFederationService


def test_list_registered_catalogs():
    catalogs = LakehouseFederationService.get_registered_catalogs()
    assert len(catalogs) == 2
    providers = [c.provider for c in catalogs]
    assert "unity" in providers
    assert "glue" in providers
    assert catalogs[0].refresh_interval_seconds == 300


def test_inspect_sample_iceberg_tables():
    glue_tables = LakehouseFederationService.inspect_sample_tables("glue_telemetry_lakehouse")
    assert len(glue_tables) == 1
    assert glue_tables[0].format == "APACHE_ICEBERG"
    assert glue_tables[0].namespace == "historical_gis"
    assert "inundation_depth_meters" in glue_tables[0].schema_fields

    unity_tables = LakehouseFederationService.inspect_sample_tables("unity_disaster_lakehouse")
    assert len(unity_tables) == 1
    assert unity_tables[0].namespace == "relief_supplies"
