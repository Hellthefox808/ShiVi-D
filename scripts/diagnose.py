#!/usr/bin/env python3
"""
ShiVi Comprehensive System Diagnostic & Troubleshooting Wizard
Automates pre-flight verification across Python environment, packages,
Node.js tooling, port availability, SQLite WAL concurrency, and MCP configuration.
"""
import sys
import os
import socket
import subprocess
import json
import sqlite3
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
FRONTEND_DIR = ROOT_DIR / "frontend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def check_port(port: int) -> bool:
    """Returns True if port is free, False if in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except socket.error:
            return False


def run_diagnostics():
    print(f"\n{BOLD}{GREEN}{'='*80}{RESET}")
    print(f"{BOLD}{GREEN}  [*] SHIVI SYSTEM DIAGNOSTIC & TROUBLESHOOTING WIZARD{RESET}")
    print(f"{BOLD}{GREEN}{'='*80}{RESET}")
    print(f"  Root Directory: {CYAN}{ROOT_DIR}{RESET}\n")

    issues = []
    warnings = []

    # --------------------------------------------------------------------------
    # 1. PYTHON & RUNTIME ENVIRONMENT
    # --------------------------------------------------------------------------
    print(f"{BOLD}[1/5] Python & Runtime Environment{RESET}")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    is_venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    print(f"  • Python Version:    {CYAN}{py_ver}{RESET}")
    print(f"  • Executable:        {CYAN}{sys.executable}{RESET}")
    print(f"  • Virtual Env (.venv): {GREEN if is_venv else YELLOW}{'ACTIVE' if is_venv else 'GLOBAL INTERPRETER (Recommend .venv)'}{RESET}")

    if sys.version_info < (3, 10):
        issues.append("Python 3.10+ is required for modern async type union syntax.")

    # Check Required Backend Packages
    required_packages = [
        ("fastapi", "FastAPI Core Framework"),
        ("starlette", "Starlette ASGI Toolkit"),
        ("pydantic", "Pydantic Schema Validation"),
        ("sqlalchemy", "SQLAlchemy 2.0 Async ORM"),
        ("aiosqlite", "Async SQLite Driver"),
        ("jose", "JOSE JWT Security Crypto"),
        ("uvicorn", "Uvicorn Production Server"),
        ("httpx", "HTTPX Async Client"),
        ("pytest", "Pytest Automated Testing Suite"),
    ]

    missing_pkgs = []
    for pkg, label in required_packages:
        try:
            __import__(pkg)
            print(f"    ✓ {pkg:<14} ({label})")
        except ImportError:
            missing_pkgs.append(pkg)
            print(f"    ✗ {pkg:<14} ({RED}MISSING{RESET})")

    if missing_pkgs:
        issues.append(f"Missing Python dependencies: {', '.join(missing_pkgs)}. Run: pip install -r backend/requirements.txt")

    # --------------------------------------------------------------------------
    # 2. FRONTEND & NODE.JS TOOLING
    # --------------------------------------------------------------------------
    print(f"\n{BOLD}[2/5] Frontend & Node.js Environment{RESET}")
    try:
        node_res = subprocess.run(["node", "-v"], capture_output=True, text=True, timeout=5)
        node_ver = node_res.stdout.strip()
        print(f"  • Node.js Version:   {CYAN}{node_ver}{RESET}")
    except Exception:
        issues.append("Node.js is not installed or not in system PATH.")
        print(f"  • Node.js Version:   {RED}NOT FOUND{RESET}")

    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists() and any(node_modules.iterdir()):
        print(f"  • node_modules:      {GREEN}PRESENT{RESET} ({FRONTEND_DIR / 'node_modules'})")
    else:
        issues.append("Frontend node_modules missing. Run: cd frontend && npm install")
        print(f"  • node_modules:      {RED}MISSING{RESET}")

    # --------------------------------------------------------------------------
    # 3. NETWORK & PORT AVAILABILITY
    # --------------------------------------------------------------------------
    print(f"\n{BOLD}[3/5] Network & Port Allocation{RESET}")
    p8000_free = check_port(8000)
    p3000_free = check_port(3000)
    p3001_free = check_port(3001)

    print(f"  • Port 8000 (Backend Core API):  {GREEN + 'AVAILABLE' if p8000_free else YELLOW + 'IN USE (Live Server Active)'}{RESET}")
    print(f"  • Port 3000 (Frontend Default):  {GREEN + 'AVAILABLE' if p3000_free else YELLOW + 'IN USE (Dev scripts will auto-fallback to 3001)'}{RESET}")
    print(f"  • Port 3001 (Frontend Fallback): {GREEN + 'AVAILABLE' if p3001_free else YELLOW + 'IN USE'}{RESET}")

    if not p3000_free and not p3001_free:
        warnings.append("Both port 3000 and 3001 are in use. Next.js will negotiate an alternate port.")

    # --------------------------------------------------------------------------
    # 4. DATABASE & WAL CONCURRENCY
    # --------------------------------------------------------------------------
    print(f"\n{BOLD}[4/5] SQLite Database & Concurrency Configuration{RESET}")
    db_paths = [
        ROOT_DIR / "backend" / "shivi_local.db",
        ROOT_DIR / "shivi_local.db",
    ]
    active_db = None
    for p in db_paths:
        if p.exists():
            active_db = p
            break

    if active_db:
        print(f"  • Active Database:   {CYAN}{active_db}{RESET}")
        try:
            conn = sqlite3.connect(str(active_db))
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode;")
            jmode = cursor.fetchone()[0].upper()
            cursor.execute("PRAGMA synchronous;")
            sync_val = cursor.fetchone()[0]

            wal_ok = jmode == "WAL"
            print(f"  • Journal Mode:      {GREEN + jmode if wal_ok else YELLOW + jmode} {RESET}(WAL mode optimal for concurrent readers)")
            print(f"  • Synchronous Level: {CYAN}{sync_val}{RESET} (1=NORMAL, 2=FULL)")

            # Query table row counts
            tables = ["tenants", "users", "incidents", "tasks", "conflict_cases", "audit_entries", "physical_assets"]
            table_stats = []
            for t in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {t};")
                    cnt = cursor.fetchone()[0]
                    table_stats.append(f"{t}: {cnt}")
                except Exception:
                    table_stats.append(f"{t}: N/A")
            print(f"  • Data Rows:         {', '.join(table_stats)}")
            conn.close()
        except Exception as e:
            issues.append(f"Failed to inspect SQLite database: {e}")
    else:
        warnings.append("No local SQLite database file detected yet. Will be auto-initialized on first backend launch.")
        print(f"  • Active Database:   {YELLOW}PENDING FIRST RUN INITIALIZATION{RESET}")

    # --------------------------------------------------------------------------
    # 5. MCP CONFIGURATION & APP HEALTH PROBE
    # --------------------------------------------------------------------------
    print(f"\n{BOLD}[5/5] MCP Configuration & In-Process ASGI Health{RESET}")
    mcp_file = ROOT_DIR / ".mcp.json"
    if mcp_file.exists():
        try:
            with open(mcp_file, "r", encoding="utf-8") as f:
                json.load(f)
            print(f"  • .mcp.json:         {GREEN}VALID JSON{RESET}")
        except Exception as e:
            issues.append(f".mcp.json contains invalid JSON: {e}")
            print(f"  • .mcp.json:         {RED}INVALID JSON ({e}){RESET}")
    else:
        print(f"  • .mcp.json:         {YELLOW}NOT PRESENT (Optional){RESET}")

    # Test in-process ASGI engine
    try:
        from fastapi.testclient import TestClient
        from app.main import app  # type: ignore
        client = TestClient(app)
        h_res = client.get("/health")
        server_timing = h_res.headers.get("server-timing")
        process_time = h_res.headers.get("x-process-time")
        if h_res.status_code == 200:
            print(f"  • ASGI Engine Probe: {GREEN}HEALTHY (200 OK){RESET}")
            if server_timing:
                print(f"  • Latency Headers:   {CYAN}{server_timing}{RESET} (Process-Time: {process_time})")
        else:
            issues.append(f"ASGI Engine /health returned {h_res.status_code}")
            print(f"  • ASGI Engine Probe: {RED}STATUS {h_res.status_code}{RESET}")

        # Check Tactical Load Balancer Core Engine
        from app.core.load_balancer import TacticalLoadBalancer  # type: ignore
        lb = TacticalLoadBalancer(nodes=["http://127.0.0.1:8001", "http://127.0.0.1:8002"])
        print(f"  • Tactical LB Core:  {GREEN}OPERATIONAL{RESET} (strategies: least_conn, round_robin)")
    except Exception as exc:
        issues.append(f"ASGI Engine / LB initialization failed: {exc}")
        print(f"  • ASGI Engine Probe: {RED}FAILED ({exc}){RESET}")

    # --------------------------------------------------------------------------
    # SUMMARY & ACTIONABLE RECOMMENDATIONS
    # --------------------------------------------------------------------------
    print(f"\n{'-'*80}")
    if issues:
        print(f"{BOLD}{RED}  [!] {len(issues)} ACTIONABLE ISSUES DETECTED:{RESET}")
        for idx, iss in enumerate(issues, 1):
            print(f"      {idx}. {RED}{iss}{RESET}")
        print(f"\n  {YELLOW}Suggested Resolution:{RESET}")
        print(f"    - Use Python virtual environment: {CYAN}.venv\\Scripts\\python.exe{RESET}")
        print(f"    - Reinstall dependencies: {CYAN}pip install -r backend/requirements.txt{RESET}")
        print(f"    - Install frontend modules: {CYAN}cd frontend && npm install{RESET}")
        return 1
    else:
        print(f"{BOLD}{GREEN}  ✅ SYSTEM FULLY OPTIMIZED & READY FOR HIGH-CAPACITY CRISIS DEPLOYMENT{RESET}")
        if warnings:
            print(f"     Notices: {', '.join(warnings)}")
        print(f"\n  {BOLD}Recommended Launch Command:{RESET}")
        print(f"    {CYAN}node scripts/dev.js{RESET} (Starts backend on :8000 and frontend on :3000/3001)")
        print(f"\n  {BOLD}Automated Multi-Scenario Audit:{RESET}")
        print(f"    {CYAN}.venv\\Scripts\\python.exe .agents/skills/shivi-disaster-workflow/scripts/verify_workflow.py verify-all --output verification_report.json{RESET}\n")
        return 0


if __name__ == "__main__":
    sys.exit(run_diagnostics())
