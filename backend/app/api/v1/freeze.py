from typing import Optional, List, Any
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import FreezeRequest, User
from app.services.freeze import FreezeService, FreezeTransitionError, get_legal_basis_advisory
from app.core.security import require_user
from app.legal.provisions import get_citation

router = APIRouter(prefix="/freeze-requests", tags=["Freeze Requests"])

class CreateFreezeRequest(BaseModel):
    case_id: int
    vasp_id: int
    deposit_address: str
    suspect_wallet: str
    legal_order_ref: Optional[str] = None
    notes: Optional[str] = ""
    victim_loss_inr: Optional[float] = None
    victim_loss_usd: Optional[float] = None
    fir_number: Optional[str] = None
    fir_date: Optional[str] = None
    police_station: Optional[str] = None
    district_state: Optional[str] = None
    offence_sections: Optional[List[str]] = None
    io_name: Optional[str] = None
    io_designation: Optional[str] = None
    io_contact: Optional[str] = None
    legal_basis: Optional[str] = None
    court_order_ref: Optional[str] = None
    court_order_date: Optional[str] = None
    freeze_amount: Optional[float] = None
    traced_tainted_amount: Optional[float] = None
    supporting_tx_hashes: Optional[List[str]] = None
    over_limit_justification: Optional[str] = None
    data_origin: Optional[str] = "LIVE"

class UpdateStatusRequest(BaseModel):
    status: str
    frozen_amount_usd: Optional[float] = None
    notes: Optional[str] = None

@router.get("/advisory")
def get_freeze_legal_advisory():
    """Returns statutory advisory for legal basis selection."""
    c_106 = get_citation("seizure_of_property")
    c_107 = get_citation("attachment_proceeds_of_crime")
    return {
        "legal_basis_advisory": get_legal_basis_advisory(),
        "options": [
            {"key": "bnss_106_seizure", "label": f"{c_106['citation']} ({c_106['label']})"},
            {"key": "bnss_107_attachment", "label": f"{c_107['citation']} ({c_107['label']})"},
            {"key": "court_order", "label": "Other Competent Court Order"}
        ]
    }

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
        "legal_basis_advisory": get_legal_basis_advisory(),

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
                "freeze_amount": r.freeze_amount,
                "traced_tainted_amount": r.traced_tainted_amount,
                "status": r.status,
                "watermark": r.watermark,
                "legal_basis": r.legal_basis,
                "legal_order_ref": r.legal_order_ref,
                "fir_number": r.fir_number,
                "police_station": r.police_station,
                "district_state": r.district_state,
                "created_by": r.created_by,
                "approved_by": r.approved_by,
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "acknowledged_at": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
                "frozen_amount_usd": r.frozen_amount_usd,
                "created_at": r.created_at.isoformat() if r.created_at else None
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
    fir_d = None
    if payload.fir_date:
        try:
            fir_d = date.fromisoformat(payload.fir_date)
        except ValueError:
            pass

    co_d = None
    if payload.court_order_date:
        try:
            co_d = date.fromisoformat(payload.court_order_date)
        except ValueError:
            pass

    fr = FreezeService.create_freeze_request(
        db=db,
        case_id=payload.case_id,
        vasp_id=payload.vasp_id,
        deposit_address=payload.deposit_address,
        suspect_wallet=payload.suspect_wallet,
        legal_order_ref=payload.legal_order_ref,
        notes=payload.notes or "",
        created_by=current_user.email,
        victim_loss_inr=payload.victim_loss_inr,
        victim_loss_usd=payload.victim_loss_usd,
        fir_number=payload.fir_number,
        fir_date=fir_d,
        police_station=payload.police_station,
        district_state=payload.district_state,
        offence_sections=payload.offence_sections,
        io_name=payload.io_name,
        io_designation=payload.io_designation,
        io_contact=payload.io_contact,
        legal_basis=payload.legal_basis,
        court_order_ref=payload.court_order_ref,
        court_order_date=co_d,
        freeze_amount=payload.freeze_amount,
        traced_tainted_amount=payload.traced_tainted_amount,
        supporting_tx_hashes=payload.supporting_tx_hashes,
        over_limit_justification=payload.over_limit_justification,
        data_origin=payload.data_origin or "LIVE"
    )
    return {
        "status": "created",
        "freeze_request_id": fr.id,
        "request_number": fr.request_number,
        "watermark": fr.watermark,
        "legal_basis_advisory": get_legal_basis_advisory()
    }

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
            "frozen_amount_usd": updated.frozen_amount_usd,
            "watermark": updated.watermark
        }
    except FreezeTransitionError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
