"""
ShiVi Resilience & Health Probes API Router
===========================================

Briefing:
    Provides REST endpoints for container health probes (Kubernetes, Docker, Azure Container Apps),
    load balancer traffic readiness gates, and administrative Dead Letter Queue (DLQ) quarantine inspection.

Reason:
    High availability and operational resilience require distinct health dimensions:
    1. Liveness Probe (`/health/liveness`): Confirms that the FastAPI process is running and the
       asyncio event loop is active. Container orchestrators restart pods if this fails.
    2. Readiness Probe (`/health/readiness`): Executes a fast non-blocking heartbeat (`SELECT 1`)
       against the active database. Tactical load balancers withhold ingress traffic from this
       replica until database connectivity is verified.
    3. DLQ Inspection & Purge (`/dlq`): Enables systems engineers and commanders to inspect
       quarantined poison-pill event payloads and purge them once root-cause analysis is complete.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.resilience import DeadLetterQueue, DeadLetterQueueEntry

# Briefing: FastAPI Router mounted under `/v1/resilience` for infrastructure health checks.
# Reason: Provides isolated, low-overhead endpoints for container probes and fault-tolerance diagnostics.
router = APIRouter(prefix="/v1/resilience", tags=["Resilience & Load Balancing"])


@router.get("/health/liveness")
async def liveness_probe() -> Dict[str, str]:
    """
    Briefing:
        Liveness probe for process supervision and container orchestrators.

    Reason:
        Returns HTTP 200 immediately if the server process is responsive. Used by Docker,
        Kubernetes, or systemd to detect thread deadlocks or hung processes requiring a restart.

    Returns:
        Dictionary indicating status 'ALIVE' and core tier identifier.
    """
    return {"status": "ALIVE", "tier": "CORE_API_V1"}


@router.get("/health/readiness")
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Briefing:
        Readiness probe for upstream tactical load balancers.

    Reason:
        Verifies active database connectivity and query execution by executing `SELECT 1`.
        Prevents load balancers from routing traffic to initializing or partitioned replicas
        that cannot currently persist disaster records.

    Parameters:
        db: Asynchronous database session.

    Returns:
        Dictionary indicating status 'READY' and database 'CONNECTED'.

    Raises:
        HTTPException(503): If the database is locked, unreachable, or throwing errors.
    """
    try:
        # Explanation: Fast non-blocking heartbeat query
        await db.execute(text("SELECT 1"))
        return {
            "status": "READY",
            "database": "CONNECTED",
            "load_balancer_traffic": "ALLOWED",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database readiness check failed: {str(e)}",
        )


@router.get("/dlq", response_model=List[DeadLetterQueueEntry])
async def list_dead_letter_queue(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Retrieves all quarantined poison-pill payloads from the Dead Letter Queue.

    Reason:
        Allows system administrators to inspect payloads that failed processing repeatedly,
        review error messages, and examine corrupted message contents without crashing pipelines.

    Parameters:
        current_user: Authenticated administrator or supervisor.

    Returns:
        List of `DeadLetterQueueEntry` models currently in quarantine.
    """
    return DeadLetterQueue.get_quarantined_entries()


@router.delete("/dlq")
async def clear_dead_letter_queue(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Briefing:
        Purges all quarantined records from the in-memory Dead Letter Queue.

    Reason:
        Allows operators to reset the quarantine buffer once offending issues have been resolved.

    Parameters:
        current_user: Authenticated administrator or supervisor.

    Returns:
        Dictionary indicating status 'CLEARED'.
    """
    DeadLetterQueue.clear_quarantine()
    return {"status": "CLEARED"}
