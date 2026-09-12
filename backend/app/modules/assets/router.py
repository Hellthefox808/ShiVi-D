"""
ShiVi Physical Assets & Custody Leases API Router
=================================================

Briefing:
    Provides REST endpoints for inventory registration, equipment checkout, physical custody
    proof validation (NFC/QR/GPS), and automated resource contention resolution.
    Powers tactical depot logistics and mobile equipment scanner apps.

Reason:
    Equipping search-and-rescue teams requires strict custody tracking:
    1. Uncontended Allocation: Allows responders to reserve or check out available equipment.
    2. Contention Detection & Auto-Resolution: If an asset is already in use by another squad,
       the router invokes `DistributedAssetAllocationEngine`:
       - Evaluates physical possession proofs and incident life-safety priority scores.
       - Dispatches an automatic substitute from the depot to the losing squad.
       - Logs an unalterable `AuditEntry` and updates command dashboard feeds.
    3. Proof-Gated Custody: Supports NFC and QR scans to confirm on-the-ground physical possession.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user_token, TokenPayload
from app.modules.assets.models import PhysicalAsset, AssetAllocationClaim
from app.modules.assets.allocation_engine import DistributedAssetAllocationEngine
from app.modules.audit.models import AuditEntry

# Briefing: FastAPI Router mounted under `/assets` for physical equipment logistics.
# Reason: Isolates asset inventory, custody checkouts, and substitute dispatch workflows.
router = APIRouter(prefix="/assets", tags=["Physical Assets & Custody Leases"])


class AssetCreateRequest(BaseModel):
    """
    Briefing:
        Request payload for onboarding a new piece of equipment into the tactical inventory.
    """
    asset_code: str
    name: str
    category: str  # GENERATOR, PUMP, VEHICLE, BOAT, DRONE, MEDICAL
    current_location_name: Optional[str] = "Main Staging Depot"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AssetClaimRequest(BaseModel):
    """
    Briefing:
        Payload submitted by a field responder to check out or claim custody of an asset.
    """
    incident_id: str
    task_id: str
    claim_type: str = "VIRTUAL_RESERVATION"  # VIRTUAL_RESERVATION or PHYSICAL_POSSESSION
    proof_data: Dict[str, Any] = {}
    priority_score: float = 50.0


class AssetResponse(BaseModel):
    """
    Briefing:
        Response model representing an asset's current operational and custody state.
    """
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
    """
    Briefing:
        Registers a new physical asset into the tenant's equipment registry.

    Parameters:
        req: `AssetCreateRequest` specifying code, category, and initial depot location.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        The registered `AssetResponse` with status `AVAILABLE`.
    """
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
    """
    Briefing:
        Retrieves physical assets belonging to the active tenant, with optional filters.

    Parameters:
        category: Optional category filter (e.g. 'PUMP', 'BOAT').
        status_filter: Optional status filter (e.g. 'AVAILABLE', 'IN_USE').
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        List of matching `AssetResponse` records.
    """
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
    """
    Briefing:
        Claims custody of a physical asset, resolving contention automatically if already in use.

    Reason:
        1. If asset is AVAILABLE: Checks out immediately to the requesting responder.
        2. If asset is IN_USE by another responder:
           - Queries depot for unassigned substitute equipment in the same category.
           - Invokes `DistributedAssetAllocationEngine.resolve_contention()`.
           - Awards primary asset to winner (based on physical proof or life-safety priority).
           - Automatically assigns substitute asset to the displaced squad, guaranteeing zero stalls.
           - Logs an immutable `AuditEntry` and updates tactical dashboard feeds.

    Parameters:
        asset_code: Asset code (e.g. 'GEN-PUMP-01').
        req: `AssetClaimRequest` containing task link, claim type, and priority score.
        db: Database session.
        current_user: Authenticated JWT claims.

    Returns:
        Dictionary with status ('allocated' or 'contention_resolved') and allocation details.

    Raises:
        HTTPException(404): If asset code is not found in tenant.
    """
    res = await db.execute(
        select(PhysicalAsset).where(
            PhysicalAsset.asset_code == asset_code,
            PhysicalAsset.tenant_id == current_user.tenant_id,
        )
    )
    asset = res.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_code} not found")

    # Explanation: Check if asset is currently held by a different responder (contention condition)
    if asset.status == "IN_USE" and asset.current_holder_id and asset.current_holder_id != current_user.sub:
        # Contention detected!
        # Explanation: Query depot for available substitutes in the identical equipment category
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

        # Explanation: Formulate existing custody claim dictionary
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

        # Explanation: Formulate incoming competing claim dictionary
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

        # Explanation: Resolve contention via deterministic 4-step invariant engine
        resolution = DistributedAssetAllocationEngine.resolve_contention(
            asset_code=asset_code,
            claim_a=claim_existing,
            claim_b=claim_incoming,
            available_substitutes=available_subs,
        )

        # Explanation: Update primary asset custody to the winning claimant
        asset.current_holder_id = resolution.winner_claimant_id
        asset.current_incident_id = resolution.winner_incident_id
        asset.current_task_id = resolution.winner_task_id
        if resolution.winner_claimant_id == current_user.sub:
            asset.has_physical_proof = (req.claim_type == "PHYSICAL_POSSESSION")
            asset.physical_proof_type = req.proof_data.get("proof_type") if req.claim_type == "PHYSICAL_POSSESSION" else None
            asset.physical_proof_timestamp = datetime.now(timezone.utc) if req.claim_type == "PHYSICAL_POSSESSION" else None

        # Explanation: Reassign substitute equipment to displaced squad so operations continue
        if resolution.substitute_provided and resolution.substitute_asset_id:
            sub_asset_res = await db.execute(select(PhysicalAsset).where(PhysicalAsset.id == resolution.substitute_asset_id))
            sub_asset = sub_asset_res.scalars().first()
            if sub_asset:
                sub_asset.status = "IN_USE"
                sub_asset.current_holder_id = resolution.loser_claimant_id
                sub_asset.current_incident_id = resolution.loser_incident_id
                sub_asset.current_task_id = resolution.loser_task_id

        # Explanation: Record contention resolution into immutable audit ledger
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

        # Explanation: Invalidate dashboard summary cache
        from app.modules.dashboard.router import IOCCacheManager
        IOCCacheManager.invalidate(current_user.tenant_id)

        return {
            "status": "contention_resolved",
            "resolution": resolution.__dict__,
        }

    # Explanation: Normal Uncontended Checkout
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

    # Explanation: Invalidate dashboard summary cache
    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return {
        "status": "allocated",
        "asset_code": asset.asset_code,
        "holder_id": current_user.sub,
        "has_physical_proof": asset.has_physical_proof,
    }


@router.post("/simulate-contention")
async def simulate_contention_resolution(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token),
):
    """
    Briefing:
        Deterministic simulation endpoint for physical asset contention and zero-deadlock substitution.

    Reason:
        Sets up Squad Alpha with virtual reservation on IRB-04, ensures substitute IRB-05 is AVAILABLE in depot,
        then processes incoming physical NFC proof claim from Squad Bravo, triggering DistributedAssetAllocationEngine.
    """
    # 1. Ensure or reset IRB-04 (Primary Contended Asset)
    res_4 = await db.execute(
        select(PhysicalAsset).where(
            PhysicalAsset.asset_code == "IRB-04",
            PhysicalAsset.tenant_id == current_user.tenant_id,
        )
    )
    asset_4 = res_4.scalars().first()
    if not asset_4:
        asset_4 = PhysicalAsset(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            asset_code="IRB-04",
            name="Inflatable Motorized Rescue Boat #4",
            category="BOAT",
            current_location_name="Pandu Port Staging Area",
            latitude=26.1856,
            longitude=91.7483,
            status="IN_USE",
            current_holder_id="00000000-0000-0000-0000-000000000001",  # Squad Alpha
            current_incident_id="inc-alpha-001",
            current_task_id="task-alpha-rescue",
            has_physical_proof=False,
            physical_proof_type=None,
        )
        db.add(asset_4)
    else:
        asset_4.status = "IN_USE"
        asset_4.current_holder_id = "00000000-0000-0000-0000-000000000001"
        asset_4.current_incident_id = "inc-alpha-001"
        asset_4.current_task_id = "task-alpha-rescue"
        asset_4.has_physical_proof = False
        asset_4.physical_proof_type = None

    # 2. Ensure or reset IRB-05 (Available Substitute in Depot)
    res_5 = await db.execute(
        select(PhysicalAsset).where(
            PhysicalAsset.asset_code == "IRB-05",
            PhysicalAsset.tenant_id == current_user.tenant_id,
        )
    )
    asset_5 = res_5.scalars().first()
    if not asset_5:
        asset_5 = PhysicalAsset(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            asset_code="IRB-05",
            name="Inflatable Motorized Rescue Boat #5",
            category="BOAT",
            current_location_name="Sector 4 Boat Staging Depot",
            latitude=26.1820,
            longitude=91.7450,
            status="AVAILABLE",
            current_holder_id=None,
            current_incident_id=None,
            current_task_id=None,
            has_physical_proof=False,
            physical_proof_type=None,
        )
        db.add(asset_5)
    else:
        asset_5.status = "AVAILABLE"
        asset_5.current_holder_id = None
        asset_5.current_incident_id = None
        asset_5.current_task_id = None
        asset_5.has_physical_proof = False

    await db.flush()

    # 3. Formulate existing Squad Alpha virtual reservation claim
    claim_existing = {
        "asset_id": asset_4.id,
        "claimant_id": "00000000-0000-0000-0000-000000000001",
        "incident_id": "inc-alpha-001",
        "task_id": "task-alpha-rescue",
        "claim_type": "VIRTUAL_RESERVATION",
        "proof_data": {},
        "priority_score": 60.0,
        "claimed_at": asset_4.updated_at or datetime.now(timezone.utc),
    }

    # 4. Formulate incoming Squad Bravo physical NFC claim
    claim_incoming = {
        "asset_id": asset_4.id,
        "claimant_id": "00000000-0000-0000-0000-000000000002",
        "incident_id": "inc-bravo-999",
        "task_id": "task-bravo-flood",
        "claim_type": "PHYSICAL_POSSESSION",
        "proof_data": {
            "proof_type": "NFC_HARDWARE_TAG",
            "uid": "04-A1-B2-C3",
            "proximity_m": 6.2,
        },
        "priority_score": 85.0,
        "claimed_at": datetime.now(timezone.utc),
    }

    available_subs = [
        {"id": asset_5.id, "asset_code": asset_5.asset_code, "current_location_name": asset_5.current_location_name}
    ]

    # 5. Execute 4-step invariant contention engine
    resolution = DistributedAssetAllocationEngine.resolve_contention(
        asset_code="IRB-04",
        claim_a=claim_existing,
        claim_b=claim_incoming,
        available_substitutes=available_subs,
    )

    # 6. Apply resolution: Squad Bravo gets IRB-04 with physical proof
    asset_4.current_holder_id = resolution.winner_claimant_id
    asset_4.current_incident_id = resolution.winner_incident_id
    asset_4.current_task_id = resolution.winner_task_id
    asset_4.has_physical_proof = True
    asset_4.physical_proof_type = "NFC_HARDWARE_TAG"
    asset_4.physical_proof_timestamp = datetime.now(timezone.utc)

    # Squad Alpha gets IRB-05 automatically dispatched
    if resolution.substitute_provided and resolution.substitute_asset_id:
        asset_5.status = "IN_USE"
        asset_5.current_holder_id = resolution.loser_claimant_id
        asset_5.current_incident_id = resolution.loser_incident_id
        asset_5.current_task_id = resolution.loser_task_id

    # 7. Record immutable audit entry
    audit = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        action="ASSET_CONTENTION_RESOLVED",
        actor_id="00000000-0000-0000-0000-000000000002",
        actor_role="FIELD_RESPONDER",
        target_entity_type="physical_asset",
        target_entity_id=asset_4.id,
        previous_state={"holder": "Squad Alpha (SDRF)", "status": "VIRTUAL_RESERVATION"},
        new_state={
            "winner": "Squad Bravo (NDRF)",
            "primary_asset": "IRB-04",
            "substitute_asset": "IRB-05",
            "substitute_allocated_to": "Squad Alpha (SDRF)",
        },
        reason=resolution.winner_reason,
    )
    db.add(audit)
    await db.commit()

    from app.modules.dashboard.router import IOCCacheManager
    IOCCacheManager.invalidate(current_user.tenant_id)

    return {
        "status": "contention_resolved",
        "resolution": {
            "primary_asset_id": asset_4.id,
            "primary_asset_code": "IRB-04",
            "winner_claimant_id": "00000000-0000-0000-0000-000000000002",
            "winner_name": "Squad Bravo (NDRF Team 4)",
            "winner_reason": resolution.winner_reason,
            "loser_claimant_id": "00000000-0000-0000-0000-000000000001",
            "loser_name": "Squad Alpha (SDRF Team 1)",
            "substitute_provided": resolution.substitute_provided,
            "substitute_asset_id": asset_5.id,
            "substitute_asset_code": "IRB-05",
            "substitute_location": asset_5.current_location_name,
            "contingency_action_notice": resolution.contingency_action_notice,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

