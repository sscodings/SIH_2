import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import User, UserRefreshToken
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    hash_refresh_token, decode_token, revoke_token, get_current_user,
    require_user, login_rate_limiter
)
from app.core.audit import log_audit_action
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user: dict

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None

@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_key = f"{client_ip}:login"
    if login_rate_limiter.is_rate_limited(rate_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts from this IP. Please try again in 1 minute."
        )

    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check account lockout
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    if user and user.locked_until and user.locked_until > now_utc:
        log_audit_action(
            db=db,
            user_email=form_data.username,
            action="LOGIN_BLOCKED_LOCKED_ACCOUNT",
            entity_type="USER",
            entity_id=str(user.id),
            details={"ip": client_ip, "locked_until": user.locked_until.isoformat()}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is temporarily locked due to excessive failed attempts. Try again later."
        )

    if not user or not verify_password(form_data.password, user.hashed_password):
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                # Lockout for 15 minutes
                user.locked_until = now_utc + timedelta(minutes=15)
            db.commit()

        log_audit_action(
            db=db,
            user_email=form_data.username,
            action="LOGIN_FAILED",
            entity_type="USER",
            entity_id=str(user.id) if user else "UNKNOWN",
            details={"ip": client_ip, "attempts": user.failed_login_attempts if user else 1}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled. Contact system administrator."
        )

    # Successful login: reset failed counters
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    # Create Access & Refresh Tokens
    access_token, jti, expire = create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.full_name}
    )
    refresh_token = create_refresh_token(user_id=user.id, db=db)

    # Set HttpOnly Refresh Cookie
    response.set_cookie(
        key="chainnetra_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False if settings.CHAINNETRA_MODE == "DEMO" else True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )

    log_audit_action(
        db=db,
        user_email=user.email,
        action="USER_LOGIN",
        entity_type="USER",
        entity_id=str(user.id),
        details={"role": user.role, "ip": client_ip}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role
        }
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: Request,
    response: Response,
    payload: Optional[RefreshRequest] = None,
    db: Session = Depends(get_db)
):
    # Extract token from payload body first if explicitly passed, then cookie
    token_str = None
    if payload and payload.refresh_token:
        token_str = payload.refresh_token
    elif request.cookies.get("chainnetra_refresh_token"):
        token_str = request.cookies.get("chainnetra_refresh_token")

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    token_hash = hash_refresh_token(token_str)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    token_rec = db.query(UserRefreshToken).filter(
        UserRefreshToken.token_hash == token_hash,
        UserRefreshToken.is_revoked == False
    ).first()

    if not token_rec or token_rec.expires_at < now_utc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user = db.query(User).filter(User.id == token_rec.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found"
        )

    # Rotate refresh token (revoke previous, issue new)
    token_rec.is_revoked = True
    new_refresh_token = create_refresh_token(user_id=user.id, db=db)

    # Generate new access token
    new_access_token, jti, expire = create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.full_name}
    )

    response.set_cookie(
        key="chainnetra_refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False if settings.CHAINNETRA_MODE == "DEMO" else True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role
        }
    }

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    # Revoke current access token jti
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw_token = auth_header.split(" ", 1)[1]
        decoded = decode_token(raw_token)
        if decoded and "jti" in decoded:
            exp_ts = decoded.get("exp")
            exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else datetime.now(timezone.utc) + timedelta(minutes=30)
            revoke_token(db, decoded["jti"], exp_dt)

    # Invalidate all refresh tokens for this user
    db.query(UserRefreshToken).filter(
        UserRefreshToken.user_id == current_user.id
    ).update({"is_revoked": True})
    db.commit()

    # Clear cookie
    response.delete_cookie(key="chainnetra_refresh_token")

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="USER_LOGOUT",
        entity_type="USER",
        entity_id=str(current_user.id),
        details={"email": current_user.email}
    )

    return {"status": "logged_out", "message": "Tokens revoked and session terminated successfully"}

@router.get("/me")
def get_me(current_user: User = Depends(require_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.full_name,
        "role": current_user.role
    }
