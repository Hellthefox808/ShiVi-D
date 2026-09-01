"""
Assets & Physical Leases API Router
Provides endpoints for asset listing, physical possession checkouts, NFC lease transfer, and contention resolution.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.assets.models import PhysicalAsset, AssetAllocationClaim
from app.modules.assets.allocation_engine import DistributedAssetAllocationEngine
from app.modules.audit.models import AuditEntry

router = APIRouter(prefix="/assets", tags=["Physical Assets & Custody Leases"])


class AssetCreateRequest(BaseModel):
    asset_code: str
    name: str
    category: str  # GENERATOR, PUMP, VEHICLE, BOAT, DRONE, MEDICAL
    current_location_name: Optional[str] = "Main Staging Depot"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AssetClaimRequest(BaseModel):
    incident_id: str
    task_id: str
    claim_type: str = "VIRTUAL_RESERVATION"  # VIRTUAL_RESERVATION or PHYSICAL_POSSESSION
    proof_data: Dict[str, Any] = {}
    priority_score: float = 50.0


class AssetResponse(BaseModel):
    id: str
    asset_code: str
    name: str
    category: str
    status: str
    current_location_name: Optional[str]
    current_holder_id: Optional[str]
    has_physical_proof: bool

    class Config:
        from_attributes = True


@router.post("", response_model=AssetResponse)
async def create_asset(
    req: AssetCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    asset = PhysicalAsset(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        asset_code=req.asset_code,
        name=req.name,
        category=req.category,
        current_location_name=req.current_location_name,
        latitude=req.latitude,
        longitude=req.longitude,
        status="AVAILABLE",
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("", response_model=List[AssetResponse])
async def list_assets(
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    query = select(PhysicalAsset).where(PhysicalAsset.tenant_id == current_user.tenant_id)
    if category:
        query = query.where(PhysicalAsset.category == category)
    if status_filter:
        query = query.where(PhysicalAsset.status == status_filter)
    res = await db.execute(query)
    return res.scalars().all()


@router.post("/{asset_code}/claim")
async def claim_asset_custody(
    asset_code: str,
    req: AssetClaimRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    res = await db.execute(
        select(PhysicalAsset).where(
            PhysicalAsset.asset_code == asset_code,
            PhysicalAsset.tenant_id == current_user.tenant_id,
        )
    )
    asset = res.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_code} not found")

    # Check if asset is already claimed
    if asset.status == "IN_USE" and asset.current_holder_id and asset.current_holder_id != current_user.sub:
        # Contention detected!
        # Query available substitutes in same category
        sub_res = await db.execute(
            select(PhysicalAsset).where(
                PhysicalAsset.tenant_id == current_user.tenant_id,
                PhysicalAsset.category == asset.category,
                PhysicalAsset.status == "AVAILABLE",
                PhysicalAsset.id != asset.id,
            )
        )
        available_subs = [
            {"id": a.id, "asset_code": a.asset_code, "current_location_name": a.current_location_name}
            for a in sub_res.scalars().all()
        ]

        # Existing holder claim
        claim_existing = {
            "asset_id": asset.id,
            "claimant_id": asset.current_holder_id,
            "incident_id": asset.current_incident_id or "prior-incident",
            "task_id": asset.current_task_id or "prior-task",
            "claim_type": "PHYSICAL_POSSESSION" if asset.has_physical_proof else "VIRTUAL_RESERVATION",
            "proof_data": {"proof_type": asset.physical_proof_type},
            "priority_score": 60.0,
            "claimed_at": asset.updated_at,
        }

        # Incoming claim
        claim_incoming = {
            "asset_id": asset.id,
            "claimant_id": current_user.sub,
            "incident_id": req.incident_id,
            "task_id": req.task_id,
            "claim_type": req.claim_type,
            "proof_data": req.proof_data,
            "priority_score": req.priority_score,
            "claimed_at": datetime.now(timezone.utc),
        }

        resolution = DistributedAssetAllocationEngine.resolve_contention(
            asset_code=asset_code,
            claim_a=claim_existing,
            claim_b=claim_incoming,
            available_substitutes=available_subs,
        )

        # Update substitute asset if assigned
        if resolution.substitute_provided and resolution.substitute_asset_id:
            sub_asset_res = await db.execute(select(PhysicalAsset).where(PhysicalAsset.id == resolution.substitute_asset_id))
            sub_asset = sub_asset_res.scalars().first()
            if sub_asset:
                sub_asset.status = "IN_USE"
                sub_asset.current_holder_id = resolution.loser_claimant_id
                sub_asset.current_incident_id = resolution.loser_incident_id
                sub_asset.current_task_id = resolution.loser_task_id

        # Record Audit Entry
        audit = AuditEntry(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            action="ASSET_CONTENTION_RESOLVED",
            actor_id=current_user.sub,
            actor_role=current_user.role,
            target_entity_type="physical_asset",
            target_entity_id=asset.id,
            previous_state={"holder": asset.current_holder_id, "status": asset.status},
            new_state={
                "winner": resolution.winner_claimant_id,
                "substitute": resolution.substitute_asset_code,
            },
            reason=resolution.winner_reason,
        )
        db.add(audit)
        await db.commit()

        return {
            "status": "contention_resolved",
            "resolution": resolution.__dict__,
        }

    # Normal Uncontended Claim
    asset.status = "IN_USE"
    asset.current_holder_id = current_user.sub
    asset.current_incident_id = req.incident_id
    asset.current_task_id = req.task_id
    asset.has_physical_proof = (req.claim_type == "PHYSICAL_POSSESSION")
    asset.physical_proof_type = req.proof_data.get("proof_type") if req.claim_type == "PHYSICAL_POSSESSION" else None
    asset.physical_proof_timestamp = datetime.now(timezone.utc) if req.claim_type == "PHYSICAL_POSSESSION" else None

    claim = AssetAllocationClaim(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        asset_id=asset.id,
        claimant_id=current_user.sub,
        incident_id=req.incident_id,
        task_id=req.task_id,
        claim_type=req.claim_type,
        proof_data=req.proof_data,
        priority_score=req.priority_score,
        claim_status="ACTIVE",
    )
    db.add(claim)
    await db.commit()

    return {
        "status": "allocated",
        "asset_code": asset.asset_code,
        "holder_id": current_user.sub,
        "has_physical_proof": asset.has_physical_proof,
    }
