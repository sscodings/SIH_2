from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.db.database import get_db
from backend.app.db.models import FreezeRequest, Entity
from backend.app.services.freeze import FreezeService

router = APIRouter(prefix="/freeze-requests", tags=["Freeze Requests"])

class CreateFreezeRequest(BaseModel):
    case_id: int
    vasp_id: int
    deposit_address: str
    suspect_wallet: str
    legal_order_ref: Optional[str] = "Cr.No 402/2026 U/S 66D IT Act & 420 IPC"
    notes: Optional[str] = ""

class UpdateStatusRequest(BaseModel):
    status: str
    user_email: str = "supervisor@demo"
    frozen_amount_usd: Optional[float] = 0.0

@router.get("")
def list_freeze_requests(db: Session = Depends(get_db)):
    requests = db.query(FreezeRequest).order_by(FreezeRequest.created_at.desc()).all()
    return {
        "freeze_requests": [
            {
                "id": r.id,
                "request_number": r.request_number,
                "case_id": r.case_id,
                "vasp_id": r.vasp_id,
                "vasp_name": r.vasp_name,
                "deposit_address": r.deposit_address,
                "suspect_wallet": r.suspect_wallet,
                "victim_loss_inr": r.victim_loss_inr,
                "victim_loss_usd": r.victim_loss_usd,
                "status": r.status,
                "legal_order_ref": r.legal_order_ref,
                "created_by": r.created_by,
                "approved_by": r.approved_by,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "acknowledged_at": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
                "frozen_amount_usd": r.frozen_amount_usd,
                "created_at": r.created_at.isoformat()
            }
            for r in requests
        ]
    }

@router.post("")
def create_freeze(payload: CreateFreezeRequest, db: Session = Depends(get_db)):
    fr = FreezeService.create_freeze_request(
        db=db,
        case_id=payload.case_id,
        vasp_id=payload.vasp_id,
        deposit_address=payload.deposit_address,
        suspect_wallet=payload.suspect_wallet,
        legal_order_ref=payload.legal_order_ref or "",
        notes=payload.notes or "",
        created_by="investigator@demo"
    )
    return {"status": "created", "freeze_request_id": fr.id, "request_number": fr.request_number}

@router.patch("/{id}/status")
def update_status(id: int, payload: UpdateStatusRequest, db: Session = Depends(get_db)):
    try:
        updated = FreezeService.update_freeze_status(
            db=db,
            request_id=id,
            new_status=payload.status,
            user_email=payload.user_email,
            frozen_amount_usd=payload.frozen_amount_usd or 0.0
        )
        return {"status": "updated", "new_status": updated.status, "id": updated.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
