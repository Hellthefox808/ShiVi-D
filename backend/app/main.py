"""
Briefing: ShiVi Disaster Response Central Coordination FastAPI Service Entrypoint.
Reason: Operates as the central command authority and synchronization hub for all field nodes,
web dashboards, and tactical assets. Provides REST endpoints across the full 8-phase disaster
lifecycle (Capture, Persist, Sync, Reconcile, Safety, Decide, Verify, Audit).
"""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.database import engine, Base
from app.modules.identity.router import router as identity_router
from app.modules.incidents.router import router as incidents_router
from app.modules.tasks.router import router as tasks_router
from app.modules.sync.router import router as sync_router
from app.modules.conflicts.router import router as conflicts_router
from app.modules.evidence.router import router as evidence_router
from app.modules.verifications.router import router as verifications_router
from app.modules.audit.router import router as audit_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.integrations.router import router as integrations_router
from app.modules.intelligence.router import router as intelligence_router
from app.modules.resilience.router import router as resilience_router
from app.modules.assets.router import router as assets_router
from app.modules.demo.router import router as demo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Briefing: Application lifecycle manager managing startup and shutdown routines.
    Reason: Automatically initializes SQLite/PostgreSQL database schemas during local development
    or container startup before accepting incoming HTTP sync traffic.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_server_timing_and_process_time(request: Request, call_next):
    """
    Briefing: HTTP middleware recording sub-millisecond execution duration for every request.
    Reason: In emergency operations, latency anomalies can degrade real-time dispatching.
    Adds `X-Process-Time` and `Server-Timing` headers for telemetry and audit profiling.
    """
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    response.headers["Server-Timing"] = f"app;dur={process_time:.2f}"
    return response


# Briefing: HTTP response GZip compression.
# Reason: Reduces raw payload size by 60-80% for payloads > 1KB. Crucial for field responders
# transmitting over satellite bursts or congested 2G/3G disaster backhauls.
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Briefing: Cross-Origin Resource Sharing (CORS) security configuration.
# Reason: Permits the React web dashboard (running on port 3000/3001) and mobile test devices
# to communicate securely with the API without browser origin blocking.
cors_origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:8000,*",
)
cors_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
if "*" in cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Briefing: Register modular domain routers representing each phase of disaster operations.
app.include_router(identity_router, prefix=settings.API_V1_STR)
app.include_router(incidents_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
app.include_router(sync_router, prefix=settings.API_V1_STR)
app.include_router(conflicts_router, prefix=settings.API_V1_STR)
app.include_router(evidence_router, prefix=settings.API_V1_STR)
app.include_router(verifications_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(integrations_router, prefix=settings.API_V1_STR)
app.include_router(intelligence_router, prefix=settings.API_V1_STR)
app.include_router(assets_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)
app.include_router(resilience_router)  # Includes /v1/resilience/health/liveness, /v1/resilience/health/readiness


@app.get("/health", tags=["Health & Diagnostics"])
async def health_check():
    """
    Briefing: Lightweight liveness probe endpoint.
    Reason: Polled by load balancers, orchestrators, and mobile field clients to confirm service availability.
    """
    return {
        "status": "healthy",
        "service": "ShiVi Operations Core API",
        "version": settings.VERSION,
    }

