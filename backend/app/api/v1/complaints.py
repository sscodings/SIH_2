import json
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Complaint, User
from app.services.ingest import IngestionService, IngestionValidationError
from app.core.ws import ws_manager
from app.core.security import require_user
from app.core.audit import log_audit_action

router = APIRouter(prefix="", tags=["Complaints"])

class IngestRequest(BaseModel):
    victim_name: str
    victim_state: str = "Maharashtra"
    fraud_type: str = "Investment Scam"
    reported_wallets: List[str]
    amount_lost_inr: float
    complaint_number: Optional[str] = None

@router.get("/complaints")
def list_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    chain: Optional[str] = None,
    fraud_type: Optional[str] = None,
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

    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "complaint_number": c.complaint_number,
                "source": c.source,
                "victim_name": c.victim_name,
                "victim_state": c.victim_state,
                "fraud_type": c.fraud_type,
                "reported_wallets": json.loads(c.reported_wallets or "[]"),
                "chain": c.chain,
                "amount_lost_inr": c.amount_lost_inr,
                "amount_lost_usd": c.amount_lost_usd,
                "reported_at": c.reported_at.isoformat(),
                "status": c.status,
                "priority": c.priority
            }
            for c in items
        ]
    }

@router.get("/complaints/{id}")
def get_complaint(id: int, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {
        "id": c.id,
        "complaint_number": c.complaint_number,
        "source": c.source,
        "victim_name": c.victim_name,
        "victim_state": c.victim_state,
        "fraud_type": c.fraud_type,
        "reported_wallets": json.loads(c.reported_wallets or "[]"),
        "chain": c.chain,
        "amount_lost_inr": c.amount_lost_inr,
        "amount_lost_usd": c.amount_lost_usd,
        "reported_at": c.reported_at.isoformat(),
        "status": c.status,
        "priority": c.priority
    }

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
    except IngestionValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Broadcast to WebSocket
    await ws_manager.broadcast_event(
        topic="inbox",
        event_type="new_complaint",
        data={
            "id": complaint.id,
            "complaint_number": complaint.complaint_number,
            "victim_name": complaint.victim_name,
            "amount_inr": complaint.amount_lost_inr,
            "chain": complaint.chain,
            "priority": complaint.priority
        }
    )

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="INGEST_NCRP_COMPLAINT",
        entity_type="COMPLAINT",
        entity_id=str(complaint.id),
        details={"complaint_number": complaint.complaint_number, "wallets": payload.reported_wallets}
    )

    return {"status": "ingested", "complaint_id": complaint.id, "complaint_number": complaint.complaint_number}

@router.post("/ingest/csv")
async def ingest_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv") and file.content_type not in ("text/csv", "application/vnd.ms-excel", "text/plain", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .csv files are supported.")

    content_bytes = await file.read()
    if len(content_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 5MB")

    try:
        content_str = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            content_str = content_bytes.decode("latin1")
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode CSV text")

    try:
        result = IngestionService.process_csv_upload(db, content_str)
    except IngestionValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="INGEST_CSV_BULK",
        entity_type="COMPLAINT",
        entity_id="BULK",
        details={"valid_rows": result.get("valid_rows"), "total_rows": result.get("total_rows")}
    )

    return result
