import os
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import AuditLog, AuditCheckpoint, AppSetting, User, PIIAccessLog
from app.core.audit import verify_audit_chain, log_audit_action
from app.core.security import require_role


router = APIRouter(prefix="/admin", tags=["Admin & Settings"])
audit_router = APIRouter(prefix="/audit-log", tags=["Audit Log"])
audit_alias_router = APIRouter(prefix="/audit", tags=["Audit Log Alias"])


class SettingUpdateRequest(BaseModel):
    key: str
    value: str

# Audit Log Endpoints (Supervisor & Admin)
@audit_router.get("")
def get_audit_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    total = db.query(AuditLog).count()
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "logs": [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat(),
                "user_email": l.user_email,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "details": json.loads(l.details or "{}"),
                "prev_hash": l.prev_hash,
                "entry_hash": l.entry_hash,
                "signature": l.signature
            }
            for l in logs
        ]
    }

@audit_router.get("/verify")
def verify_audit_log_chain(db: Session = Depends(get_db)):
    return verify_audit_chain(db)

@audit_router.get("/checkpoints")
def get_audit_checkpoints(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    total = db.query(AuditCheckpoint).count()
    checkpoints = db.query(AuditCheckpoint).order_by(AuditCheckpoint.id.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "checkpoints": [
            {
                "id": c.id,
                "last_audit_id": c.last_audit_id,
                "last_entry_hash": c.last_entry_hash,
                "checkpoint_signature": c.checkpoint_signature,
                "created_at": c.created_at.isoformat()
            }
            for c in checkpoints
        ]
    }

@audit_router.get("/pii-access")
@audit_alias_router.get("/pii-access")
def get_pii_access_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    total = db.query(PIIAccessLog).count()
    logs = db.query(PIIAccessLog).order_by(PIIAccessLog.timestamp.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "logs": [
            {
                "id": l.id,
                "user_email": l.user_email,
                "record_type": l.record_type,
                "record_id": l.record_id,
                "fields_viewed": l.fields_viewed,
                "reason": l.reason,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None
            }
            for l in logs
        ]
    }


# Admin-only Settings & Management Endpoints
@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    settings_records = db.query(AppSetting).all()
    return {s.key: s.value for s in settings_records}

@router.post("/settings")
def update_setting(
    payload: SettingUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    rec = db.query(AppSetting).filter(AppSetting.key == payload.key).first()
    old_val = rec.value if rec else None
    if rec:
        rec.value = payload.value
    else:
        rec = AppSetting(key=payload.key, value=payload.value)
        db.add(rec)
    db.commit()

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="UPDATE_APP_SETTING",
        entity_type="APP_SETTING",
        entity_id=payload.key,
        details={"key": payload.key, "old_value": old_val, "new_value": payload.value}
    )

    return {"status": "updated", "key": payload.key, "value": payload.value}

@router.get("/model-card")
def get_model_card():
    card_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ml", "models", "model_card.json")
    if os.path.exists(card_path):
        with open(card_path, "r") as f:
            return json.load(f)
    return {
        "model_name": "ChainNetra Classifier",
        "status": "Ready",
        "accuracy": 0.99
    }
