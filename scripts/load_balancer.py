#!/usr/bin/env python3
"""
ShiVi Tactical Load Balancer CLI
Runs the Tactical Load Balancer from the command line.
"""

import sys
import os
import argparse
import logging
import uvicorn

# Ensure backend root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, BASE_DIR)

try:
    from app.core.load_balancer import create_lb_app, logger  # type: ignore
except ImportError:
    from backend.app.core.load_balancer import create_lb_app, logger  # type: ignore

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ShiVi Tactical Load Balancer")
    parser.add_argument("--port", type=int, default=8000, help="Listen port (default: 8000)")
    parser.add_argument("--nodes", nargs="+", default=["http://127.0.0.1:8001", "http://127.0.0.1:8002"], help="Upstream backend node URLs")
    parser.add_argument("--strategy", choices=["least_conn", "round_robin"], default="least_conn", help="Balancing algorithm")
    parser.add_argument("--benchmark", action="store_true", help="Run in-memory dispatch performance benchmark")
    parser.add_argument("--requests", type=int, default=50000, help="Number of benchmark iterations (default: 50000)")
    args = parser.parse_args()

    if args.benchmark:
        import asyncio
        import time
        try:
            from app.core.load_balancer import TacticalLoadBalancer  # type: ignore
        except ImportError:
            from backend.app.core.load_balancer import TacticalLoadBalancer  # type: ignore

        async def run_benchmark():
            lb = TacticalLoadBalancer(nodes=args.nodes, strategy=args.strategy)
            count = args.requests
            print(f"[*] Benchmarking ShiVi Tactical Load Balancer ({args.strategy}) with {count:,} cycles...")
            t0 = time.perf_counter()
            for _ in range(count):
                node = await lb.select_node()
                lb.release_node(node)
            dur = time.perf_counter() - t0
            rps = count / dur if dur > 0 else 0
            avg_us = (dur / count) * 1_000_000
            print(f"  [OK] Processed {count:,} dispatches in {dur:.4f}s")
            print(f"  [OK] Dispatch Throughput: {rps:,.0f} dispatches/sec")
            print(f"  [OK] Mean Dispatch Latency: {avg_us:.3f} us ({avg_us/1000:.4f} ms)")
            await lb.client.aclose()

        asyncio.run(run_benchmark())
        sys.exit(0)

    logger.info(f"Starting ShiVi Tactical Load Balancer on port {args.port}")
    logger.info(f"Upstream Nodes ({args.strategy}): {args.nodes}")
    app = create_lb_app(nodes=args.nodes, strategy=args.strategy)
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")

