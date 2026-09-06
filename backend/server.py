"""
ShiVi Operations Core API - Standalone Server Runner
Provides standalone execution of the FastAPI backend with health reporting and uvicorn lifecycle.
"""
import os
import sys
import uvicorn

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "false").lower() in ("true", "1", "yes")

    print("=" * 80)
    print("  [*] SHIVI OPERATIONS CORE API - LOCAL-FIRST DISASTER COORDINATION")
    print("=" * 80)
    print(f"  - Host:         http://{host}:{port}")
    print(f"  - Swagger Docs: http://localhost:{port}/docs")
    print(f"  - ReDoc:        http://localhost:{port}/redoc")
    print(f"  - Health Check: http://localhost:{port}/health")
    print(f"  - IOC Summary:  http://localhost:{port}/v1/dashboard/summary")
    print(f"  - P0 Simulator: http://localhost:{port}/v1/demo/simulate-workflow")
    print("=" * 80)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
