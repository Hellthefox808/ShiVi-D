"""
ShiVi Tactical Load Balancer & High-Availability Reverse Proxy Core
==================================================================

Briefing:
    This module provides a lightweight, resilient Layer-7 load balancer and reverse proxy
    engineered specifically for disaster response command hubs and field deployable clusters.
    During natural disasters or infrastructure outages, command centers frequently operate
    multiple commodity laptops, micro-servers, or rugged edge nodes acting as ShiVi backends.

Reason:
    A single point of failure in field operations is unacceptable. If an edge server running
    a database or API node suffers a battery drain, thermal throttling, or hardware fault,
    field workers must not lose the ability to sync incident data or view tactical maps.
    The TacticalLoadBalancer provides:
    1. Automatic failover: Continuously probes `/health` across all upstream nodes.
    2. Intelligent traffic distribution: Supports Least-Connections and Round-Robin strategies.
    3. Resilient fallback: If all nodes are marked unhealthy, it attempts best-effort delivery
       rather than hard-failing incoming field telemetry.
    4. Operational transparency: Injects upstream routing headers (`x-lb-upstream-node`,
       `x-lb-proxy-time`) and serves real-time telemetry on `/lb-status`.
"""

import sys
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
import uvicorn

# Briefing: Logger dedicated to load balancer routing, health checks, and node transitions.
# Reason: Provides immediate visibility into cluster node failures, recoveries, and upstream latency.
logger = logging.getLogger("shivi.load_balancer")


@dataclass
class BackendNode:
    """
    Briefing:
        Dataclass representing a single upstream backend instance and its operational metrics.

    Reason:
        Maintains active connection counters, cumulative request volumes, latency benchmarks,
        and failure counts needed for dynamic balancing algorithms (like least-connections)
        and health monitoring state transitions.
    """
    # Explanation: Upstream URL root (e.g., "http://192.168.1.50:8000")
    url: str
    # Explanation: Traffic distribution weight (reserved for weighted load balancing)
    weight: int = 1
    # Explanation: Current health status based on background probe responses
    healthy: bool = True
    # Explanation: Concurrently active in-flight requests currently assigned to this node
    active_connections: int = 0
    # Explanation: Cumulative count of all requests successfully routed to this node
    total_requests: int = 0
    # Explanation: Consecutive failed health checks before transitioning healthy -> False
    failed_checks: int = 0
    # Explanation: Round-trip latency in milliseconds recorded during the most recent health check
    latency_ms: float = 0.0


class TacticalLoadBalancer:
    """
    Briefing:
        Asynchronous Layer-7 reverse proxy and load balancing orchestrator.

    Reason:
        Distributes incoming HTTP traffic across a pool of field backend servers, actively
        monitors their responsiveness, and routes around degraded or unreachable instances.
    """
    def __init__(self, nodes: List[str], strategy: str = "least_conn"):
        """
        Briefing:
            Initializes the load balancer with a list of upstream node URLs and a routing strategy.

        Parameters:
            nodes: List of upstream base URLs (e.g., `["http://10.0.0.1:8000", "http://10.0.0.2:8000"]`).
            strategy: Routing strategy identifier; "least_conn" (default) or "round_robin".
        """
        # Explanation: Normalized list of BackendNode instances with trailing slashes stripped
        self.nodes = [BackendNode(url=u.rstrip("/")) for u in nodes]
        # Explanation: Active load balancing strategy
        self.strategy = strategy  # "least_conn" or "round_robin"
        # Explanation: Index pointer for round-robin scheduling
        self._current_index = 0
        # Explanation: Lock protecting concurrent index and connection state mutations
        self._lock = asyncio.Lock()
        # Explanation: High-performance reusable async HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
        )

    def get_healthy_nodes(self) -> List[BackendNode]:
        """
        Briefing:
            Filters the node list to return currently healthy backend servers.

        Reason:
            Implements a graceful degradation fallback: if ALL nodes are flagged as down
            (perhaps due to a transient network glitch during health check), it returns
            all nodes anyway to make a best-effort proxy attempt rather than immediately
            rejecting field personnel with 503 Service Unavailable.
        """
        healthy = [n for n in self.nodes if n.healthy]
        return healthy if healthy else self.nodes  # Fallback to all if all flagged down

    async def select_node(self) -> BackendNode:
        """
        Briefing:
            Selects an optimal upstream backend node according to the configured routing strategy.

        Reason:
            In 'least_conn' mode, chooses the node with the fewest active in-flight requests
            (and lowest total requests as a secondary tie-breaker) to prevent uneven load.
            In 'round_robin' mode, cycles predictably across all healthy nodes.
            Increments active connection and total request counters under an asyncio lock.

        Returns:
            The chosen `BackendNode`.

        Raises:
            RuntimeError: If no backend nodes are configured.
        """
        async with self._lock:
            healthy = self.get_healthy_nodes()
            if not healthy:
                raise RuntimeError("No available backend nodes configured")

            if self.strategy == "least_conn":
                # Explanation: Pick node with minimal active connections, tie-breaking by total historical requests
                node = min(healthy, key=lambda n: (n.active_connections, n.total_requests))
            else:
                # Explanation: Modular increment for predictable round-robin distribution
                self._current_index = (self._current_index + 1) % len(healthy)
                node = healthy[self._current_index]

            node.active_connections += 1
            node.total_requests += 1
            return node

    def release_node(self, node: BackendNode):
        """
        Briefing:
            Decrements the active connection counter for a node once a proxied request finishes.

        Reason:
            Maintains precise real-time concurrency metrics so that `least_conn` routing remains
            accurate under fluctuating network conditions.
        """
        if node.active_connections > 0:
            node.active_connections -= 1

    async def health_check_loop(self, interval_seconds: float = 3.0):
        """
        Briefing:
            Continuous background coroutine periodically probing upstream node health.

        Reason:
            Probes the `/health` endpoint of each node every `interval_seconds`.
            - Measures round-trip latency (`latency_ms`).
            - Automatically restores previously failed nodes upon receiving HTTP 200.
            - Marks nodes as unhealthy after 3 consecutive failed probes (timeout, 5xx, or network error),
              removing them from the active traffic pool without manual administrative intervention.

        Parameters:
            interval_seconds: Polling frequency in seconds (default 3.0s).
        """
        while True:
            for node in self.nodes:
                try:
                    start = time.perf_counter()
                    resp = await self.client.get(f"{node.url}/health", timeout=2.0)
                    elapsed = (time.perf_counter() - start) * 1000.0
                    node.latency_ms = round(elapsed, 2)

                    if resp.status_code == 200:
                        if not node.healthy:
                            logger.info(f"🟢 Node RECOVERED: {node.url} (latency: {node.latency_ms}ms)")
                        node.healthy = True
                        node.failed_checks = 0
                    else:
                        node.failed_checks += 1
                        if node.failed_checks >= 3 and node.healthy:
                            logger.warning(f"🔴 Node UNHEALTHY (status {resp.status_code}): {node.url}")
                            node.healthy = False
                except Exception as e:
                    node.failed_checks += 1
                    if node.failed_checks >= 3 and node.healthy:
                        logger.warning(f"🔴 Node UNREACHABLE ({e.__class__.__name__}): {node.url}")
                        node.healthy = False

            await asyncio.sleep(interval_seconds)

    async def proxy_request(self, request: Request) -> Response:
        """
        Briefing:
            Intercepts and proxies an incoming Starlette/FastAPI HTTP request to an upstream node.

        Reason:
            1. Intercepts `/lb-status` to serve internal cluster telemetry without forwarding upstream.
            2. Acquires an optimal backend node via `select_node()`.
            3. Reformulates HTTP headers:
               - Strips inbound `host` header to prevent DNS mismatch on upstream server.
               - Adds standard `x-forwarded-host` and `x-forwarded-for` for client IP preservation.
            4. Forwards request body stream and method unchanged.
            5. Injects diagnostic response headers:
               - `x-lb-upstream-node`: Shows which physical server handled the request.
               - `x-lb-strategy`: Current balancing algorithm.
               - `x-lb-proxy-time`: Total round-trip latency through the proxy.
            6. Strips hop-by-hop headers (`transfer-encoding`, `connection`, `content-encoding`).
            7. Decrements active connections in a `finally` block to guarantee no resource leaks.

        Parameters:
            request: The inbound Starlette HTTP `Request`.

        Returns:
            Starlette `Response` matching the upstream server's output and status.
        """
        # Explanation: Local inspection endpoint for monitoring cluster health
        if request.url.path == "/lb-status":
            return Response(
                content=self.get_status_json(),
                media_type="application/json",
            )

        try:
            node = await self.select_node()
        except Exception as e:
            return Response(
                content=f'{{"error": "No healthy upstream backend nodes: {str(e)}"}}',
                status_code=503,
                media_type="application/json",
            )

        start_time = time.perf_counter()
        target_url = f"{node.url}{request.url.path}"
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"

        # Explanation: Clean and format headers for reverse proxying
        headers = dict(request.headers)
        headers.pop("host", None)
        headers["x-forwarded-host"] = request.headers.get("host", "")
        headers["x-forwarded-for"] = request.client.host if request.client else "127.0.0.1"

        try:
            body = await request.body()
            upstream_resp = await self.client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

            proxy_time = (time.perf_counter() - start_time) * 1000.0
            resp_headers = dict(upstream_resp.headers)
            # Explanation: Attach tactical observability headers
            resp_headers["x-lb-upstream-node"] = node.url
            resp_headers["x-lb-strategy"] = self.strategy
            resp_headers["x-lb-proxy-time"] = f"{proxy_time:.2f}ms"

            # Explanation: Strip hop-by-hop headers to prevent HTTP transport protocol errors
            for h in ["content-encoding", "transfer-encoding", "connection"]:
                resp_headers.pop(h, None)

            return Response(
                content=upstream_resp.content,
                status_code=upstream_resp.status_code,
                headers=resp_headers,
                media_type=upstream_resp.headers.get("content-type"),
            )
        except Exception as e:
            logger.error(f"Error forwarding request to {node.url}: {e}")
            node.failed_checks += 1
            return Response(
                content=f'{{"error": "Upstream error on node {node.url}: {str(e)}"}}',
                status_code=502,
                media_type="application/json",
            )
        finally:
            # Explanation: Guarantee connection release even if upstream raises or client disconnects
            self.release_node(node)

    def get_status_json(self) -> str:
        """
        Briefing:
            Produces a formatted JSON string summarizing cluster topology and node metrics.

        Returns:
            JSON formatted summary containing node health, latencies, and request totals.
        """
        import json
        return json.dumps({
            "strategy": self.strategy,
            "total_nodes": len(self.nodes),
            "healthy_nodes": len([n for n in self.nodes if n.healthy]),
            "nodes": [
                {
                    "url": n.url,
                    "healthy": n.healthy,
                    "active_connections": n.active_connections,
                    "total_requests": n.total_requests,
                    "latency_ms": n.latency_ms,
                    "failed_checks": n.failed_checks,
                }
                for n in self.nodes
            ],
        }, indent=2)


def create_lb_app(nodes: List[str], strategy: str = "least_conn") -> Starlette:
    """
    Briefing:
        Factory function creating a complete Starlette ASGI load balancer application.

    Reason:
        Configures an asynchronous lifespan context manager that starts the health check
        background task on application startup and cleanly terminates tasks and HTTP client
        connections on shutdown. Mounts catch-all wildcard routes for seamless proxying.

    Parameters:
        nodes: List of upstream backend URLs.
        strategy: Balancing strategy ("least_conn" or "round_robin").

    Returns:
        Configured `Starlette` ASGI application ready to be served via uvicorn.
    """
    lb = TacticalLoadBalancer(nodes=nodes, strategy=strategy)

    @asynccontextmanager
    async def lifespan(app):
        # Explanation: Launch background health checking loop as an asynchronous task
        check_task = asyncio.create_task(lb.health_check_loop())
        yield
        # Explanation: Clean shutdown: cancel background loop and close HTTP connection pool
        check_task.cancel()
        await lb.client.aclose()

    app = Starlette(lifespan=lifespan)
    # Explanation: Catch-all route forwarding all paths and standard HTTP methods to the proxy
    app.add_route("/{path:path}", lb.proxy_request, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    return app
