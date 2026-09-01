from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables for local/testing execution
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach routers
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
app.include_router(resilience_router)  # Includes /v1/resilience/health/liveness, /v1/resilience/health/readiness


@app.get("/health", tags=["Health & Diagnostics"])
async def health_check():
    return {
        "status": "healthy",
        "service": "ShiVi Operations Core API",
        "version": settings.VERSION,
    }
