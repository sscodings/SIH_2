from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Watchlist, Alert, User
from app.core.ws import ws_manager
from app.core.security import require_user
from app.core.audit import log_audit_action
from app.core.validators import validate_crypto_address

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

class WatchlistRequest(BaseModel):
    address: str
    chain: str
    label: str = ""
    reason: str = "High-risk suspect holding"
    alert_on_outflow: bool = True
    min_threshold_usd: float = 50.0
    alert_on_vasp: bool = True

@router.get("")
def list_watchlist(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    total = db.query(Watchlist).filter(Watchlist.is_active == True).count()
    items = db.query(Watchlist).filter(Watchlist.is_active == True).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": w.id,
                "address": w.address,
                "chain": w.chain,
                "label": w.label,
                "reason": w.reason,
                "alert_on_outflow": w.alert_on_outflow,
                "min_threshold_usd": w.min_threshold_usd,
                "alert_on_vasp": w.alert_on_vasp,
                "created_at": w.created_at.isoformat()
            }
            for w in items
        ]
    }

@router.post("")
def add_to_watchlist(
    payload: WatchlistRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    addr_clean = payload.address.strip()
    chain_clean = payload.chain.lower().strip()

    if not validate_crypto_address(addr_clean, chain_clean):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid address format for chain '{chain_clean}': '{addr_clean}'"
        )

    item = Watchlist(
        address=addr_clean,
        chain=chain_clean,
        label=payload.label,
        reason=payload.reason,
        alert_on_outflow=payload.alert_on_outflow,
        min_threshold_usd=payload.min_threshold_usd,
        alert_on_vasp=payload.alert_on_vasp
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="ADD_WATCHLIST",
        entity_type="WATCHLIST",
        entity_id=str(item.id),
        details={"address": item.address, "chain": item.chain}
    )

    return {"status": "added", "id": item.id}

@router.delete("/{id}")
def remove_from_watchlist(
    id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    item = db.query(Watchlist).filter(Watchlist.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    item.is_active = False
    db.commit()

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="REMOVE_WATCHLIST",
        entity_type="WATCHLIST",
        entity_id=str(id),
        details={"address": item.address}
    )

    return {"status": "removed", "id": id}
