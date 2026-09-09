"""
ShiVi Tactical Load Balancer & High-Availability Reverse Proxy Core
Coordinates multi-node local and field disaster deployment clusters.

Features:
  - Round-Robin & Least-Connections load balancing strategies.
  - Active background health probing with automatic node failover & recovery.
  - Transparent HTTP proxying with upstream latency and server identification headers.
  - Real-time connection tracking and metrics reporting.
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

logger = logging.getLogger("shivi.load_balancer")


@dataclass
class BackendNode:
    url: str
    weight: int = 1
    healthy: bool = True
    active_connections: int = 0
    total_requests: int = 0
    failed_checks: int = 0
    latency_ms: float = 0.0


class TacticalLoadBalancer:
    def __init__(self, nodes: List[str], strategy: str = "least_conn"):
        self.nodes = [BackendNode(url=u.rstrip("/")) for u in nodes]
        self.strategy = strategy  # "least_conn" or "round_robin"
        self._current_index = 0
        self._lock = asyncio.Lock()
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=100, max_connections=200),
        )

    def get_healthy_nodes(self) -> List[BackendNode]:
        healthy = [n for n in self.nodes if n.healthy]
        return healthy if healthy else self.nodes  # Fallback to all if all flagged down

    async def select_node(self) -> BackendNode:
        async with self._lock:
            healthy = self.get_healthy_nodes()
            if not healthy:
                raise RuntimeError("No available backend nodes configured")

            if self.strategy == "least_conn":
                node = min(healthy, key=lambda n: (n.active_connections, n.total_requests))
            else:
                self._current_index = (self._current_index + 1) % len(healthy)
                node = healthy[self._current_index]

            node.active_connections += 1
            node.total_requests += 1
            return node

    def release_node(self, node: BackendNode):
        if node.active_connections > 0:
            node.active_connections -= 1

    async def health_check_loop(self, interval_seconds: float = 3.0):
        """Continuous background health checking of all upstream nodes."""
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
        """Proxies an incoming request to the selected backend node."""
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
            resp_headers["x-lb-upstream-node"] = node.url
            resp_headers["x-lb-strategy"] = self.strategy
            resp_headers["x-lb-proxy-time"] = f"{proxy_time:.2f}ms"

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
            self.release_node(node)

    def get_status_json(self) -> str:
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
    lb = TacticalLoadBalancer(nodes=nodes, strategy=strategy)

    @asynccontextmanager
    async def lifespan(app):
        check_task = asyncio.create_task(lb.health_check_loop())
        yield
        check_task.cancel()
        await lb.client.aclose()

    app = Starlette(lifespan=lifespan)
    app.add_route("/{path:path}", lb.proxy_request, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    return app
