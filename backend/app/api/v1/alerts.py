from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Alert, User
from app.core.security import require_user
from app.core.audit import log_audit_action

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("")
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    total = db.query(Alert).count()
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
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
def acknowledge_alert(
    id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_acknowledged = True
    alert.acknowledged_by = current_user.email
    db.commit()

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="ACKNOWLEDGE_ALERT",
        entity_type="ALERT",
        entity_id=str(id),
        details={"alert_title": alert.title}
    )

    return {"status": "acknowledged", "id": id, "acknowledged_by": current_user.email}
