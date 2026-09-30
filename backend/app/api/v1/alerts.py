from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Alert

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("")
def list_alerts(limit: int = 50, db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()
    return {
        "alerts": [
            {
                "id": a.id,
                "type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "address": a.address,
                "chain": a.chain,
                "case_id": a.case_id,
                "tx_hash": a.tx_hash,
                "is_acknowledged": a.is_acknowledged,
                "acknowledged_by": a.acknowledged_by,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ]
    }

@router.post("/{id}/ack")
def acknowledge_alert(id: int, user_email: str = "investigator@demo", db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_acknowledged = True
    alert.acknowledged_by = user_email
    db.commit()
    return {"status": "acknowledged", "id": id}
