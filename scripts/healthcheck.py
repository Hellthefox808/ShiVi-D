#!/usr/bin/env python3
"""
ShiVi Post-Deployment Automated Health & Smoke Test Validator
Executes live HTTP diagnostic checks across all critical modules and measures response latency.
"""
import sys
import time
import urllib.request
import json

if sys.platform == "win32":
    reconfig = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfig):
        try:
            reconfig(encoding="utf-8")
        except Exception:
            pass

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

ENDPOINTS = [
    ("/health", "Core Micro-Health Probe"),
    ("/v1/dashboard/summary", "Incident Operations Center (IOC) Summary"),
    ("/v1/dashboard/geojson", "Geospatial Polygon Map Layer"),
    ("/v1/incidents", "Incident Catalog Feed"),
    ("/v1/conflicts", "Causal Conflict Engine Status"),
    ("/v1/assets", "Physical Asset Contention State"),
    ("/v1/integrations/sms/logs", "Disaster SMS & Satellite Ledger"),
    ("/v1/audit/timeline", "Cryptographic Audit Ledger Chain"),
    ("/docs", "OpenAPI Swagger Interactive Documentation"),
]

GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def check_endpoint(path: str, description: str):
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ShiVi-HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            latency_ms = (time.perf_counter() - start) * 1000.0
            status_code = response.getcode()
            return status_code, latency_ms, None
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return 0, latency_ms, str(e)


def main():
    print(f"\n{BOLD}{GREEN}{'='*80}{RESET}")
    print(f"{BOLD}{GREEN}  [*] SHIVI POST-DEPLOYMENT AUTOMATED DIAGNOSTIC VALIDATOR{RESET}")
    print(f"{BOLD}{GREEN}{'='*80}{RESET}")
    print(f"  Target Server: {CYAN}{BASE_URL}{RESET}\n")

    print(f"{BOLD}{'ENDPOINT':<32} {'STATUS':<10} {'LATENCY':<12} {'RESULT':<10} {'DESCRIPTION'}{RESET}")
    print(f"{'-'*80}")

    all_passed = True
    total_latency = 0.0

    for path, desc in ENDPOINTS:
        code, latency, err = check_endpoint(path, desc)
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
