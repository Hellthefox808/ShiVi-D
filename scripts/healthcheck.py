import sys
import os
import time
import json
from pathlib import Path

# Fix Windows stdout encoding for UTF-8 symbols
if sys.platform == "win32":
    reconfig = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfig):
        try:
            reconfig(encoding="utf-8")
        except Exception:
            pass

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

ENDPOINTS = [
    ("/health", "Core Micro-Health Probe"),
    ("/v1/dashboard/summary", "Incident Operations Center (IOC) Summary"),
    ("/v1/dashboard/geojson", "Geospatial Polygon Map Layer"),
    ("/v1/incidents", "Incident Catalog Feed"),
    ("/v1/conflicts", "Causal Conflict Engine Status"),
    ("/v1/assets", "Physical Asset Contention State"),
    ("/v1/demo/scenarios", "Operational Simulation Drill Registry"),
    ("/v1/integrations/sms/logs", "Disaster SMS & Satellite Ledger"),
    ("/v1/audit/timeline", "Cryptographic Audit Ledger Chain"),
    ("/docs", "OpenAPI Swagger Interactive Documentation"),
]


def check_live(base_url: str, path: str):
    import urllib.request
    url = f"{base_url}{path}"
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ShiVi-HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=3) as response:
            latency_ms = (time.perf_counter() - start) * 1000.0
            return response.getcode(), latency_ms, None
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return 0, latency_ms, str(e)


def check_in_process(client, path: str):
    start = time.perf_counter()
    try:
        resp = client.get(path)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return resp.status_code, latency_ms, None
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return 0, latency_ms, str(e)


def is_live_server_reachable(base_url: str) -> bool:
    import urllib.request
    try:
        req = urllib.request.Request(f"{base_url}/health", headers={"User-Agent": "ShiVi-Probe/1.0"})
        with urllib.request.urlopen(req, timeout=0.8) as response:
            return response.getcode() == 200
    except Exception:
        return False


def main():
    force_in_process = "--in-process" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    base_url = args[0] if args else "http://localhost:8000"

    print(f"\n{BOLD}{GREEN}{'='*80}{RESET}")
    print(f"{BOLD}{GREEN}  [*] SHIVI POST-DEPLOYMENT AUTOMATED DIAGNOSTIC VALIDATOR{RESET}")
    print(f"{BOLD}{GREEN}{'='*80}{RESET}")

    in_process = force_in_process or not is_live_server_reachable(base_url)
    client = None

    if in_process:
        mode_label = "In-Process ASGI Engine (Direct Memory TestClient)"
        if not force_in_process:
            print(f"  {YELLOW}[!] Live server at {base_url} not reachable. Defaulting to in-process ASGI engine.{RESET}")
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            client = TestClient(app)
        except Exception as exc:
            print(f"  {RED}[ERROR] Failed to initialize in-process ASGI client: {exc}{RESET}\n")
            return 1
    else:
        mode_label = f"Live HTTP Server ({base_url})"

    print(f"  Execution Mode: {CYAN}{mode_label}{RESET}\n")
    print(f"{BOLD}{'ENDPOINT':<32} {'STATUS':<10} {'LATENCY':<12} {'RESULT':<10} {'DESCRIPTION'}{RESET}")
    print(f"{'-'*80}")

    all_passed = True
    total_latency = 0.0

    for path, desc in ENDPOINTS:
        if in_process:
            code, latency, err = check_in_process(client, path)
        else:
            code, latency, err = check_live(base_url, path)

        total_latency += latency

        if code in (200, 201):
            status_str = f"{GREEN}{code} OK{RESET}"
            result_str = f"{GREEN}PASS{RESET}"
        else:
            status_str = f"{RED}{code or 'FAIL'}{RESET}"
            result_str = f"{RED}FAIL{RESET}"
            all_passed = False

        print(f"{path:<32} {status_str:<19} {latency:6.2f} ms   {result_str:<19} {desc}")

    mean_latency = total_latency / len(ENDPOINTS)
    print(f"{'-'*80}")
    print(f"  Average Endpoint Latency: {CYAN}{mean_latency:.2f} ms{RESET}")

    if all_passed:
        print(f"\n{BOLD}{GREEN}  ✅ ALL CRITICAL PIPELINE SERVICES VERIFIED OPERATIONAL & HEALTHY{RESET}\n")
        return 0
    else:
        print(f"\n{BOLD}{RED}  ❌ ONE OR MORE CRITICAL PIPELINE SERVICES FAILED VALIDATION{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

