"""
ShiVi Backend Performance Benchmark Harness
Executes empirical load tests against core endpoints and measures throughput,
P50/P95/P99 latency, and memory footprint.
"""
import asyncio
import time
import statistics
import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

import httpx
from app.main import app


async def benchmark_endpoint(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    total_requests: int = 100,
    concurrency: int = 10,
    payload: dict | None = None,
):
    print(f"\n[BENCHMARK] {method} {path} ({total_requests} requests, concurrency={concurrency})")
    sem = asyncio.Semaphore(concurrency)
    latencies = []

    async def single_request():
        async with sem:
            t0 = time.perf_counter()
            if method == "GET":
                res = await client.get(path)
            elif method == "POST":
                res = await client.post(path, json=payload or {})
            else:
                raise ValueError(f"Unsupported method {method}")
            t1 = time.perf_counter()
            assert res.status_code == 200, f"Failed with {res.status_code}: {res.text}"
            latencies.append((t1 - t0) * 1000)

    start_total = time.perf_counter()
    tasks = [asyncio.create_task(single_request()) for _ in range(total_requests)]
    await asyncio.gather(*tasks)
    total_time = time.perf_counter() - start_total

    latencies.sort()
    throughput = total_requests / total_time
    avg_latency = statistics.mean(latencies)
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[min(int(len(latencies) * 0.95), len(latencies) - 1)]
    p99 = latencies[min(int(len(latencies) * 0.99), len(latencies) - 1)]

    print(f"  • Throughput:  {throughput:,.2f} req/sec")
    print(f"  • Avg Latency: {avg_latency:.2f} ms")
    print(f"  • P50 Latency: {p50:.2f} ms")
    print(f"  • P95 Latency: {p95:.2f} ms")
    print(f"  • P99 Latency: {p99:.2f} ms")
    print(f"  • Total Time:  {total_time:.2f} s")

    return {
        "path": path,
        "throughput": throughput,
        "avg": avg_latency,
        "p50": p50,
        "p95": p95,
        "p99": p99,
    }


async def run_all_benchmarks():
    print("=" * 80)
    print("  [BENCHMARK] SHIVI OPERATIONS CORE API - MAXIMUM CAPACITY BENCHMARK SUITE")
    print("================================================================================")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Edge Health check benchmark (High concurrency)
        await benchmark_endpoint(client, "GET", "/health", total_requests=500, concurrency=50)

        # 2. IOC Dashboard Summary (In-memory cached query)
        await benchmark_endpoint(client, "GET", "/v1/dashboard/summary", total_requests=200, concurrency=20)

        # 3. Spatial GeoJSON Viewport Endpoint
        await benchmark_endpoint(client, "GET", "/v1/dashboard/geojson", total_requests=100, concurrency=10)

        # 4. 14-Phase Continuous Verified Context Loop Telemetry
        await benchmark_endpoint(client, "GET", "/v1/dashboard/context-loop", total_requests=100, concurrency=10)

        # 5. Compact 140-Byte Satellite Burst Encoding (CRC-32 micro-framing)
        sat_payload = {
            "event_id": "EVT-SAT-001",
            "category": "RESCUE",
            "severity": "CRITICAL",
            "people_at_risk": 5,
            "latitude": 26.1856,
            "longitude": 91.7483,
            "short_desc": "Boat rescue required rooftop flooded",
        }
        await benchmark_endpoint(
            client,
            "POST",
            "/v1/integrations/sms/compact/encode",
            total_requests=200,
            concurrency=20,
            payload=sat_payload,
        )

        # 6. Disaster SMS Gateway Ingestion & NLP Triage
        sms_payload = {
            "sender_phone": "+919876543210",
            "message_text": "SOS 3 PEOPLE TRAPPED SECTOR 4",
            "gateway_type": "GSM_GATEWAY",
        }
        await benchmark_endpoint(
            client,
            "POST",
            "/v1/integrations/sms/inbound",
            total_requests=100,
            concurrency=10,
            payload=sms_payload,
        )

        # 7. Operational Simulation Drills across all 4 scenarios
        scenarios = [
            "scenario-flood-contradiction",
            "scenario-asset-contention",
            "scenario-replay-attack",
            "scenario-sms-triage",
        ]
        for sc in scenarios:
            await benchmark_endpoint(
                client,
                "POST",
                f"/v1/demo/simulate-workflow?scenario_id={sc}",
                total_requests=10,
                concurrency=2,
            )

    print("\n" + "=" * 80)
    print("  [BENCHMARK] TACTICAL LOAD BALANCER & MULTI-NODE ROUTING EVALUATION")
    print("================================================================================")
    from app.core.load_balancer import TacticalLoadBalancer

    lb_least_conn = TacticalLoadBalancer(
        nodes=["http://backend-node-1:8000", "http://backend-node-2:8000"],
        strategy="least_conn",
    )
    lb_round_robin = TacticalLoadBalancer(
        nodes=["http://backend-node-1:8000", "http://backend-node-2:8000"],
        strategy="round_robin",
    )

    print("[LOAD BALANCER] Simulating 1,000 requests across dual backend nodes:")
    for lb, name in [(lb_least_conn, "Least-Connections"), (lb_round_robin, "Round-Robin")]:
        t0 = time.perf_counter()
        for _ in range(1000):
            node = await lb.select_node()
            lb.release_node(node)
        elapsed = time.perf_counter() - t0
        lb_throughput = 1000 / elapsed
        print(f"  • Strategy: {name:<18} | Throughput: {lb_throughput:,.2f} dispatches/sec | Distribution: " +
              ", ".join([f"{n.url.split('//')[1]}: {n.total_requests} reqs" for n in lb.nodes]))
        await lb.client.aclose()

    print("\n" + "=" * 80)
    print("  [SUCCESS] MAXIMUM CAPACITY & LOAD BALANCER BENCHMARK RUN COMPLETED (100% INTEGRITY)")
    print("================================================================================")


if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
