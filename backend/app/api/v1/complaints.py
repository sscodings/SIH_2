import json
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Complaint, User, PIIAccessLog
from app.services.ingest import IngestionService, IngestionValidationError
from app.core.ws import ws_manager
from app.core.security import require_user
from app.core.audit import log_audit_action
from app.core.time import utcnow

router = APIRouter(prefix="", tags=["Complaints"])

class IngestRequest(BaseModel):
    victim_name: str
    victim_state: str = "Maharashtra"
    fraud_type: str = "Investment Scam"
    reported_wallets: List[str]
    amount_lost_inr: float
    complaint_number: Optional[str] = None

def _format_complaint_dict(
    c: Complaint,
    current_user: User,
    unmask: bool = False,
    reason: Optional[str] = None,
    db: Optional[Session] = None
) -> dict:
    # Default is always masked (E4)
    victim_name = "Victim (Masked)"
    victim_ref = "REDACTED"

    if unmask:
        if current_user.role not in ("supervisor", "admin"):
            raise HTTPException(
                status_code=403,
                detail="Unmasking personal data is restricted to Supervisor and Admin roles only."
            )
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=422,
                detail="Mandatory reason text required to view unmasked personal data."
            )

        victim_name = c.victim_name
        victim_ref = c.victim_ref  # Automatically decrypted by EncryptedString decorator

        # Log unmasked access to pii_access_log
        if db is not None:
            access_log = PIIAccessLog(
                user_email=current_user.email,
                record_type="COMPLAINT",
                record_id=str(c.id),
                fields_viewed="victim_name, victim_ref",
                reason=reason.strip(),
                timestamp=utcnow()
            )
            db.add(access_log)
            db.commit()

    return {
        "id": c.id,
        "complaint_number": c.complaint_number,
        "source": c.source,
        "source_system": c.source_system,
        "data_origin": c.data_origin,
        "victim_name": victim_name,
        "victim_ref": victim_ref,
        "victim_state": c.victim_state,
        "fraud_type": c.fraud_type,
        "reported_wallets": json.loads(c.reported_wallets or "[]"),
        "chain": c.chain,
        "amount_lost_inr": c.amount_lost_inr,
        "amount_lost_usd": c.amount_lost_usd,
        "amount_unknown": c.amount_unknown,
        "legal_hold": c.legal_hold,
        "incident_at": c.incident_at.isoformat() if c.incident_at else None,
        "reported_at": c.reported_at.isoformat() if c.reported_at else None,
        "txn_hash": c.txn_hash,
        "claimed_vasp_hint": c.claimed_vasp_hint,
        "linked_complaint_ids": json.loads(c.linked_complaint_ids or "[]"),
        "vasp_flag": c.vasp_flag,
        "status": c.status,
        "priority": c.priority
    }

@router.get("/complaints")
def list_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    chain: Optional[str] = None,
    fraud_type: Optional[str] = None,
    unmask: bool = Query(False, description="Request unmasked personal data (Supervisor/Admin only)"),
    reason: Optional[str] = Query(None, description="Mandatory reason for unmasking personal data"),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == status)
    if chain:
        query = query.filter(Complaint.chain == chain)
    if fraud_type:
        query = query.filter(Complaint.fraud_type == fraud_type)

    total = query.count()
    items = query.order_by(Complaint.reported_at.desc()).offset(skip).limit(limit).all()

    formatted_items = []
    for c in items:
        formatted = _format_complaint_dict(c, current_user, unmask=unmask, reason=reason, db=db)
        formatted_items.append(formatted)

    return {
        "total": total,
        "items": formatted_items
    }

@router.get("/complaints/{id}")
def get_complaint(
    id: int,
    unmask: bool = Query(False, description="Request unmasked personal data (Supervisor/Admin only)"),
    reason: Optional[str] = Query(None, description="Mandatory reason for unmasking personal data"),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return _format_complaint_dict(c, current_user, unmask=unmask, reason=reason, db=db)

@router.post("/ingest/ncrp")
async def ingest_ncrp(
    payload: IngestRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    try:
        complaint = IngestionService.ingest_single_complaint(
            db=db,
            victim_name=payload.victim_name,
            victim_state=payload.victim_state,
            fraud_type=payload.fraud_type,
            reported_wallets=payload.reported_wallets,
            amount_lost_inr=payload.amount_lost_inr,
            source="NCRP",
            complaint_number=payload.complaint_number
        )
        await ws_manager.broadcast_event(
            topic="complaints:new",
            event_type="complaint_ingested",
            data={
                "complaint_number": complaint.complaint_number,
                "amount_lost_inr": complaint.amount_lost_inr,
                "priority": complaint.priority,
                "chain": complaint.chain
            }
        )
        return {
            "status": "ingested",
            "complaint_number": complaint.complaint_number,
            "id": complaint.id,
            "complaint_id": complaint.id
        }
    except IngestionValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
