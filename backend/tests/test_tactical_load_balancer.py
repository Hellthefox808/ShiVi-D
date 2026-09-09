import pytest
import asyncio
from fastapi.testclient import TestClient

from app.core.load_balancer import TacticalLoadBalancer, BackendNode, create_lb_app
from app.main import app as backend_app


def test_server_timing_and_process_time_headers():
    """Verify that backend app injects X-Process-Time and Server-Timing headers."""
    client = TestClient(backend_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-process-time" in response.headers
    assert "server-timing" in response.headers
    assert "app;dur=" in response.headers["server-timing"]


@pytest.mark.asyncio
async def test_load_balancer_least_conn_strategy():
    """Verify least_conn strategy directs requests to the node with lowest active connections."""
    nodes = ["http://127.0.0.1:8001", "http://127.0.0.1:8002"]
    lb = TacticalLoadBalancer(nodes=nodes, strategy="least_conn")

    # Node 0 has 1 active connection, Node 1 has 0
    lb.nodes[0].active_connections = 1
    selected = await lb.select_node()
    assert selected.url == "http://127.0.0.1:8002"
    assert selected.active_connections == 1

    # Release node
    lb.release_node(selected)
    assert selected.active_connections == 0
    await lb.client.aclose()


@pytest.mark.asyncio
async def test_load_balancer_round_robin_strategy():
    """Verify round_robin strategy cycles evenly through healthy nodes."""
    nodes = ["http://127.0.0.1:8001", "http://127.0.0.1:8002"]
    lb = TacticalLoadBalancer(nodes=nodes, strategy="round_robin")

    first = await lb.select_node()
    second = await lb.select_node()
    third = await lb.select_node()

    assert first.url != second.url
    assert first.url == third.url
    await lb.client.aclose()


@pytest.mark.asyncio
async def test_load_balancer_automatic_failover():
    """Verify unhealthy nodes are excluded from selection."""
    nodes = ["http://127.0.0.1:8001", "http://127.0.0.1:8002"]
    lb = TacticalLoadBalancer(nodes=nodes, strategy="least_conn")

    # Mark node 0 down
    lb.nodes[0].healthy = False

    # All selections must route to node 1
    for _ in range(5):
        selected = await lb.select_node()
        assert selected.url == "http://127.0.0.1:8002"
        lb.release_node(selected)

    await lb.client.aclose()


def test_load_balancer_status_endpoint():
    """Verify /lb-status endpoint returns accurate telemetry."""
    lb_app = create_lb_app(nodes=["http://127.0.0.1:8001", "http://127.0.0.1:8002"], strategy="least_conn")
    client = TestClient(lb_app)
    response = client.get("/lb-status")
    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "least_conn"
    assert data["total_nodes"] == 2
    assert data["healthy_nodes"] == 2
    assert len(data["nodes"]) == 2
