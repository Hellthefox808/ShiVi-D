from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash, get_current_user_token, TokenPayload
from app.modules.identity.models import User, Tenant

router = APIRouter(prefix="/auth", tags=["Identity & Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str
    tenant_id: str


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    tenant_id: str


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalars().first()
    
    # In mock demo mode, allow default passwords if not verified
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
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
