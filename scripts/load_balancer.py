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
    args = parser.parse_args()

    logger.info(f"Starting ShiVi Tactical Load Balancer on port {args.port}")
    logger.info(f"Upstream Nodes ({args.strategy}): {args.nodes}")
    app = create_lb_app(nodes=args.nodes, strategy=args.strategy)
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
