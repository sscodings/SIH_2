import random
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.db.database import get_db
from backend.app.db.models import Watchlist, Alert
from backend.app.core.ws import ws_manager
from backend.app.services.webhooks import WebhookService

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
def list_watchlist(db: Session = Depends(get_db)):
    items = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    return {
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
def add_to_watchlist(payload: WatchlistRequest, db: Session = Depends(get_db)):
    item = Watchlist(
        address=payload.address.strip(),
        chain=payload.chain.lower(),
        label=payload.label,
        reason=payload.reason,
        alert_on_outflow=payload.alert_on_outflow,
        min_threshold_usd=payload.min_threshold_usd,
        alert_on_vasp=payload.alert_on_vasp
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"status": "added", "id": item.id}

@router.delete("/{id}")
def remove_from_watchlist(id: int, db: Session = Depends(get_db)):
    item = db.query(Watchlist).filter(Watchlist.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    item.is_active = False
    db.commit()
    return {"status": "removed", "id": id}

@router.post("/simulate-movement")
async def simulate_movement(db: Session = Depends(get_db)):
    """
    Simulates a sudden outbound transfer from a monitored suspect wallet.
    Fires real-time WebSocket alert, toast event, and dispatches webhook.
    """
    items = db.query(Watchlist).filter(Watchlist.is_active == True).all()
    target_addr = items[0].address if items else "TDormantFreezeCandidate40000USD00"
    target_chain = items[0].chain if items else "tron"

    moved_amount = random.randint(5000, 25000)
    tx_hash = f"sim_alert_tx_{random.randint(100000,999999)}"

    # Create alert record
    alert = Alert(
        alert_type="FUNDS_MOVED",
        severity="Critical",
        title=f"ALERT: Monitored Wallet Moved ${moved_amount:,.2f} USDT",
        message=f"Monitored address {target_addr[:10]}... initiated an outbound transfer of ${moved_amount:,.2f} USD. Destination under automated first-pass attribution.",
        address=target_addr,
        chain=target_chain,
        tx_hash=tx_hash,
        is_acknowledged=False
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    alert_data = {
        "id": alert.id,
        "type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "message": alert.message,
        "address": target_addr,
        "chain": target_chain,
        "amount_usd": moved_amount,
        "tx_hash": tx_hash,
        "timestamp": alert.created_at.isoformat()
    }

    # Broadcast on WebSocket
    await ws_manager.broadcast_event("alerts", "new_alert", alert_data)

    # Dispatch to Webhook
    await WebhookService.dispatch_event(db, "freeze_alert", alert_data)

    return {"status": "movement_simulated", "alert": alert_data}
