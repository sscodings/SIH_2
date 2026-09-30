from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import FreezeRequest, User
from app.services.freeze import FreezeService, FreezeTransitionError
from app.core.security import require_user

router = APIRouter(prefix="/freeze-requests", tags=["Freeze Requests"])

class CreateFreezeRequest(BaseModel):
    case_id: int
    vasp_id: int
    deposit_address: str
    suspect_wallet: str
    legal_order_ref: Optional[str] = "Cr.No 402/2026 U/S 66D IT Act & 420 IPC"
    notes: Optional[str] = ""
    victim_loss_inr: Optional[float] = None
    victim_loss_usd: Optional[float] = None

class UpdateStatusRequest(BaseModel):
    status: str
    frozen_amount_usd: Optional[float] = None
    notes: Optional[str] = None

@router.get("")
def list_freeze_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    total = db.query(FreezeRequest).count()
    requests = db.query(FreezeRequest).order_by(FreezeRequest.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
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
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "acknowledged_at": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
                "frozen_amount_usd": r.frozen_amount_usd,
                "created_at": r.created_at.isoformat()
            }
            for r in requests
        ]
    }

@router.post("")
def create_freeze(
    payload: CreateFreezeRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    fr = FreezeService.create_freeze_request(
        db=db,
        case_id=payload.case_id,
        vasp_id=payload.vasp_id,
        deposit_address=payload.deposit_address,
        suspect_wallet=payload.suspect_wallet,
        legal_order_ref=payload.legal_order_ref or "",
        notes=payload.notes or "",
        created_by=current_user.email,
        victim_loss_inr=payload.victim_loss_inr,
        victim_loss_usd=payload.victim_loss_usd
    )
    return {"status": "created", "freeze_request_id": fr.id, "request_number": fr.request_number}

@router.patch("/{id}/status")
def update_status(
    id: int,
    payload: UpdateStatusRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    try:
        updated = FreezeService.update_freeze_status(
            db=db,
            request_id=id,
            new_status=payload.status,
            actor_email=current_user.email,
            actor_role=current_user.role,
            frozen_amount_usd=payload.frozen_amount_usd
        )
        return {
            "status": "updated",
            "new_status": updated.status,
            "id": updated.id,
            "approved_by": updated.approved_by,
            "frozen_amount_usd": updated.frozen_amount_usd
        }
    except FreezeTransitionError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
