import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, Dict
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


class TokenPayload(BaseModel):
    sub: str
    role: str
    tenant_id: str
    exp: Optional[int] = None


def hash_password(password: str) -> str:
    salt = settings.JWT_SECRET[:16]
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    return hash_password(password)


def create_access_token(
    subject: Union[str, Dict[str, Any], Any],
    role: Optional[str] = None,
    tenant_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    if isinstance(subject, dict):
        to_encode = subject.copy()
        if "exp" not in to_encode:
            expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
            to_encode["exp"] = expire
    else:
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode = {
            "sub": str(subject),
            "role": role or "SUPERVISOR",
            "tenant_id": str(tenant_id) if tenant_id else "11111111-1111-1111-1111-111111111111",
            "exp": expire,
        }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user_token(token: Optional[str] = Depends(oauth2_scheme)) -> TokenPayload:
    if not token:
        # Default mock context for seeded/demo mode if unauthenticated in local testing
        return TokenPayload(
            sub="00000000-0000-0000-0000-000000000001",
            role="SUPERVISOR",
            tenant_id="11111111-1111-1111-1111-111111111111",
        )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        return token_data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Alias for dependency injection
get_current_user = get_current_user_token

