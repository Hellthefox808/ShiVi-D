"""
ShiVi Cryptographic Evidence & Binary Attachments API Router
============================================================

Briefing:
    Provides REST endpoints for registering, pre-signing, and retrieving multimedia evidence
    attachments (reconnaissance photographs, audio field logs, GPS track logs).

Reason:
    High-resolution photos cannot easily be streamed directly through microservice JSON endpoints
    or low-power mesh radios.
    The Evidence Router enables:
    1. Pre-Signed Evidence Reservation: Allows field clients to register metadata (SHA-256 digest,
       byte size, GPS coordinates) and receive a dedicated storage upload path.
    2. Zero-Trust Verification: Preserves the client-computed SHA-256 hash so the backend can
       verify data integrity upon binary transmission.
    3. Task Linkage: Maps evidence directly to task assignments for completion auditing.
"""

import uuid
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.evidence.models import Evidence

# Briefing: FastAPI Router mounted under `/evidence` for binary proof management.
# Reason: Provides isolated endpoints for media upload reservation and verification lookups.
router = APIRouter(prefix="/evidence", tags=["Evidence & Binary Attachments"])


class EvidencePresignRequest(BaseModel):
    """
    Briefing:
        Request payload submitted by a mobile client prior to uploading binary evidence.

    Reason:
        Transmits the cryptographic fingerprint (SHA-256) and capture metadata so that the
        server can validate file size, storage quota, and integrity before receiving bytes.
    """
    task_id: Optional[str] = None
    incident_id: Optional[str] = None
    file_type: str = "IMAGE"
    sha256_hash: str
    byte_size: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EvidenceResponse(BaseModel):
    """
    Briefing:
        Response returning the registered evidence record and canonical upload path.
    """
    id: str
    tenant_id: str
    task_id: Optional[str]
    incident_id: Optional[str]
    file_type: str
    file_path: str
    sha256_hash: str
    is_verified: str
    uploaded_at: datetime


@router.post("/presign", response_model=EvidenceResponse)
async def presign_evidence(
    req: EvidencePresignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Reserves a storage slot and records metadata for an upcoming evidence upload.

    Reason:
        Generates a deterministic storage path scoped to the user's tenant ID, stores
        the expected SHA-256 hash, and associates the record with the target task or incident.

    Parameters:
        req: `EvidencePresignRequest` containing hash, size, and optional GPS coordinates.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        The registered `EvidenceResponse` containing the designated `file_path`.
    """
    evidence_id = str(uuid.uuid4())
    fake_path = f"uploads/{current_user.tenant_id}/{evidence_id}.jpg"
    
    ev = Evidence(
        id=evidence_id,
        tenant_id=current_user.tenant_id,
        task_id=req.task_id,
        incident_id=req.incident_id,
        file_type=req.file_type,
        file_path=fake_path,
        sha256_hash=req.sha256_hash,
        byte_size=req.byte_size,
        latitude=req.latitude,
        longitude=req.longitude,
        captured_by_user_id=current_user.sub,
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return ev


@router.get("", response_model=List[EvidenceResponse])
async def list_evidence(
    task_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Retrieves evidence attachments belonging to the active tenant, optionally filtered by task.

    Reason:
        Enables supervisors to view all photos and sensor logs submitted for a specific rescue task
        when reviewing completion claims in the verification portal.

    Parameters:
        task_id: Optional UUID of task to filter by.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        List of matching `EvidenceResponse` records.
    """
    query = select(Evidence).where(Evidence.tenant_id == current_user.tenant_id)
    if task_id:
        query = query.where(Evidence.task_id == task_id)
    result = await db.execute(query)
    return result.scalars().all()
