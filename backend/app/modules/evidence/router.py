import uuid
import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.evidence.models import Evidence

router = APIRouter(prefix="/evidence", tags=["Evidence & Binary Attachments"])


class EvidencePresignRequest(BaseModel):
    task_id: Optional[str] = None
    incident_id: Optional[str] = None
    file_type: str = "IMAGE"
    sha256_hash: str
    byte_size: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EvidenceResponse(BaseModel):
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
    query = select(Evidence).where(Evidence.tenant_id == current_user.tenant_id)
    if task_id:
        query = query.where(Evidence.task_id == task_id)
    result = await db.execute(query)
    return result.scalars().all()
