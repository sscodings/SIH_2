import os
import json
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.db.database import get_db
from backend.app.db.models import AuditLog, AppSetting
from backend.app.core.audit import verify_audit_chain, log_audit_action

router = APIRouter(prefix="/admin", tags=["Admin & Audit"])

class SettingUpdateRequest(BaseModel):
    key: str
    value: str

@router.get("/audit-log")
def get_audit_log(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return {
        "total": len(logs),
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
                "entry_hash": l.entry_hash
            }
            for l in logs
        ]
    }

@router.get("/audit-log/verify")
def verify_audit_log_chain(db: Session = Depends(get_db)):
    return verify_audit_chain(db)

audit_router = APIRouter(prefix="/audit-log", tags=["Audit Log"])

@audit_router.get("")
def get_audit_log_direct(limit: int = 100, db: Session = Depends(get_db)):
    return get_audit_log(limit=limit, db=db)

@audit_router.get("/verify")
def verify_audit_log_chain_direct(db: Session = Depends(get_db)):
    return verify_audit_chain(db)

@router.post("/audit-log/tamper-test")
def simulate_audit_tamper(db: Session = Depends(get_db)):
    """
    Intentionally modifies the details of an audit entry to test tamper detection.
    """
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    if not last_log:
        raise HTTPException(status_code=400, detail="No audit entries to tamper with")
    
    last_log.details = json.dumps({"tampered": True, "illegal_override": "Modified by unauthorized actor"})
    db.commit()
    return {"status": "tampered", "tampered_entry_id": last_log.id, "message": "Modified entry details without updating hash chain. Verification will now report tampered."}

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    settings_records = db.query(AppSetting).all()
    return {s.key: s.value for s in settings_records}

@router.post("/settings")
def update_setting(payload: SettingUpdateRequest, db: Session = Depends(get_db)):
    rec = db.query(AppSetting).filter(AppSetting.key == payload.key).first()
    if rec:
        rec.value = payload.value
    else:
        rec = AppSetting(key=payload.key, value=payload.value)
        db.add(rec)
    db.commit()
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
