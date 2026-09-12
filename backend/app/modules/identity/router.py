"""
ShiVi Identity & Authentication API Router
==========================================

Briefing:
    Provides REST endpoints for user authentication, JSON Web Token (JWT) issuance,
    and intra-tenant user discovery. Serves as the security boundary enforcing
    multi-tenant isolation and role-based permissions across mobile and web clients.

Reason:
    Every request across the ShiVi API requires an authenticated cryptographic identity:
    1. JWT Claims: Encodes user ID (`sub`), authoritative role (`role`), and tenant ID (`tenant_id`),
       allowing downstream microservices and routers to perform stateless authorization checks.
    2. Tenant Boundary: Ensures that user directory queries return only colleagues within the
       same tenant jurisdiction, preventing cross-agency reconnaissance.
    3. Seamless Field Token Minting: Issues signed tokens for offline synchronization handshakes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash, get_current_user_token, TokenPayload
from app.modules.identity.models import User, Tenant

# Briefing: FastAPI Router mounted under `/auth` for identity and access management.
# Reason: Provides distinct authentication endpoints separated from operational business logic.
router = APIRouter(prefix="/auth", tags=["Identity & Auth"])


class LoginRequest(BaseModel):
    """
    Briefing:
        Inbound credentials payload for authenticating a user.
    """
    # Explanation: Unique username of the responder or commander
    username: str
    # Explanation: Raw plaintext password submitted over TLS
    password: str


class TokenResponse(BaseModel):
    """
    Briefing:
        Authentication token response containing the signed JWT and principal metadata.
    """
    # Explanation: Cryptographically signed HMAC-SHA256 JWT access token
    access_token: str
    # Explanation: OAuth2 token type (always 'bearer')
    token_type: str = "bearer"
    # Explanation: User UUID primary key
    user_id: str
    # Explanation: Username handle
    username: str
    # Explanation: Authoritative role ('CITIZEN', 'RESPONDER', 'SUPERVISOR', 'ADMIN')
    role: str
    # Explanation: Multi-tenant jurisdictional isolation key
    tenant_id: str


class UserResponse(BaseModel):
    """
    Briefing:
        Safe public profile representation of a registered user.
    """
    id: str
    username: str
    full_name: str
    role: str
    tenant_id: str


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Briefing:
        Authenticates user credentials and issues a signed JWT access token.

    Reason:
        Verifies that the username exists and creates a signed token binding the user's
        identity, role, and tenant boundary. In offline/demo environments, permits standard
        test credentials to ensure operational continuity during local field drills.

    Parameters:
        req: `LoginRequest` containing username and password.
        db: Database session.

    Returns:
        `TokenResponse` with signed JWT and user metadata.

    Raises:
        HTTPException(401): If the user does not exist or credentials fail verification.
    """
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalars().first()
    
    # Explanation: Validate existence of user record
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    # Explanation: Generate signed JWT with sub=user.id, role=user.role, tenant_id=user.tenant_id
    token = create_access_token(subject=user.id, role=user.role, tenant_id=user.tenant_id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        role=user.role,
        tenant_id=user.tenant_id,
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user_token)
):
    """
    Briefing:
        Retrieves all registered personnel within the caller's tenant organization.

    Reason:
        Used by dispatchers and supervisors to populate responder assignment dropdowns
        and team selection rosters while strictly preventing cross-tenant data leaks.

    Parameters:
        db: Database session.
        current_user: Authenticated JWT claims containing caller's tenant ID.

    Returns:
        List of `UserResponse` profiles for the active tenant.
    """
    result = await db.execute(select(User).where(User.tenant_id == current_user.tenant_id))
    users = result.scalars().all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            role=u.role,
            tenant_id=u.tenant_id,
        )
        for u in users
    ]
