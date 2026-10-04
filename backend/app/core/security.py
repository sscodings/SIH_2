import time
import secrets
import bcrypt
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, List, Dict, Callable, Tuple
from collections import defaultdict
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.db.models import User, RevokedToken, UserRefreshToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

ALGORITHM = "HS256"

# Role hierarchy: admin > supervisor > investigator
ROLE_HIERARCHY: Dict[str, List[str]] = {
    "admin": ["admin", "supervisor", "investigator"],
    "supervisor": ["supervisor", "investigator"],
    "investigator": ["investigator"]
}

# Role Matrix documentation and capabilities
ROLE_MATRIX: Dict[str, List[str]] = {
    "investigator": [
        "cases:read", "cases:write",
        "traces:run", "traces:cancel",
        "notes:write",
        "freeze:draft",
        "reports:generate", "reports:read",
        "complaints:read", "complaints:write",
        "wallets:read",
        "watchlist:read", "watchlist:write",
        "alerts:read", "alerts:ack",
        "entities:read"
    ],
    "supervisor": [
        "All investigator capabilities",
        "freeze:approve", "freeze:send", "freeze:reject", "freeze:freeze",
        "analytics:read",
        "audit:read"
    ],
    "admin": [
        "All supervisor capabilities",
        "labels:write", "labels:delete",
        "settings:read", "settings:write",
        "webhooks:read", "webhooks:write", "webhooks:test",
        "users:read", "users:write",
        "api_keys:manage"
    ]
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, str, datetime]:
    to_encode = data.copy()
    jti = secrets.token_hex(16)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "jti": jti})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire

def create_refresh_token(user_id: int, db: Session) -> str:
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Invalidate existing active refresh tokens for user (rotation)
    db.query(UserRefreshToken).filter(
        UserRefreshToken.user_id == user_id,
        UserRefreshToken.is_revoked == False
    ).update({"is_revoked": True})

    db.add(UserRefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        is_revoked=False,
        expires_at=expires_at
    ))
    db.commit()
    return raw_token

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def is_token_revoked(db: Session, jti: str) -> bool:
    if not jti:
        return False
    revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
    return revoked is not None

def revoke_token(db: Session, jti: str, expires_at: datetime):
    if jti:
        db.add(RevokedToken(jti=jti, expires_at=expires_at))
        db.commit()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    unauthorized_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload:
        raise unauthorized_exc

    email: Optional[str] = payload.get("sub")
    role: Optional[str] = payload.get("role")
    jti: Optional[str] = payload.get("jti")

    if not email or not role:
        raise unauthorized_exc

    if is_token_revoked(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.locked_until and user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account temporarily locked due to excessive failed attempts",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def require_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

def require_role(*allowed_roles: str) -> Callable:
    allowed_roles_clean = [r.lower() for r in allowed_roles]

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = (current_user.role or "investigator").lower()
        permitted = ROLE_HIERARCHY.get(user_role, [user_role])
        if not any(req in permitted for req in allowed_roles_clean):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient permissions for role '{current_user.role}'. Required one of: {list(allowed_roles)}"
            )
        return current_user

    return role_checker

# In-Memory Rate Limiter for public endpoints
class InMemoryRateLimiter:
    def __init__(self, requests_limit: int = 30, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history = defaultdict(list)

    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        # Clean expired
        self.history[key] = [t for t in self.history[key] if t > window_start]
        if len(self.history[key]) >= self.requests_limit:
            return True
        self.history[key].append(now)
        return False

public_rate_limiter = InMemoryRateLimiter(requests_limit=60, window_seconds=60)
login_rate_limiter = InMemoryRateLimiter(requests_limit=10, window_seconds=60)

def rate_limit_public(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{client_ip}:{request.url.path}"
    if public_rate_limiter.is_rate_limited(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down."
        )

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' ws: wss: http: https:;"
        )
        return response
