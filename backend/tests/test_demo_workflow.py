"""
Test ShiVi P0 Demo Simulation Endpoints
Validates full 9-step verified context loop via REST API.
"""
import pytest
import httpx
from app.main import app


@pytest.mark.asyncio
async def test_demo_status_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/v1/demo/status")
        assert res.status_code == 200
        data = res.json()
        assert data["simulation_ready"] is True
        assert "total_incidents" in data
        assert "total_conflicts" in data


@pytest.mark.asyncio
async def test_demo_simulation_workflow():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/v1/demo/simulate-workflow")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert len(data["steps"]) == 9
        assert data["incident"]["status"] == "RESOLVED"
        assert data["conflict"]["status"] == "RESOLVED"
        assert data["conflict"]["resolved_value"] == "BLOCKED"
        assert data["task"]["status"] == "VERIFIED"
        assert len(data["evidence"]["sha256_hash"]) == 64


@pytest.mark.asyncio
async def test_demo_reset_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/v1/demo/reset")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
