"""
Resilience & Health Probes Router - Multi-Replica Load Balancer Readiness & DLQ Management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.resilience import DeadLetterQueue, DeadLetterQueueEntry

router = APIRouter(prefix="/v1/resilience", tags=["Resilience & Load Balancing"])


@router.get("/health/liveness")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes / Azure Container Apps Liveness Probe.
    Returns 200 OK immediately if the process is running and event loop is alive.
    """
    return {"status": "ALIVE", "tier": "CORE_API_V1"}


@router.get("/health/readiness")
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Load Balancer Readiness Probe.
    Verifies database connectivity and query execution before routing traffic to this replica.
    """
    try:
        # Execute fast non-blocking heartbeat query
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
    Lists all quarantined poison pill payloads isolated from retry loops.
    """
    return DeadLetterQueue.get_quarantined_entries()


@router.delete("/dlq")
async def clear_dead_letter_queue(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Clears quarantined DLQ entries after operator resolution.
    """
    DeadLetterQueue.clear_quarantine()
    return {"status": "CLEARED"}
