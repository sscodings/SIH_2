import json
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Alert, User
from app.core.security import require_user
from app.core.audit import log_audit_action
from app.worker import MONITOR_METRICS

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("")
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by status: new, ack, resolved"),
    severity: Optional[str] = Query(None, description="Filter by severity: Critical, High, Medium, Info"),
    chain: Optional[str] = None,
    address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status.lower())
    if severity:
        query = query.filter(Alert.severity == severity)
    if chain:
        query = query.filter(Alert.chain == chain)
    if address:
        query = query.filter(Alert.address == address)

    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

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
                "evidence_tx_hashes": json.loads(a.evidence_tx_hashes or "[]"),
                "dedup_key": a.dedup_key,
                "status": a.status or ("ack" if a.is_acknowledged else "new"),
                "is_acknowledged": a.is_acknowledged,
                "acknowledged_by": a.acknowledged_by,
                "resolved_by": a.resolved_by,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
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
    alert.status = "ack"
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

@router.post("/{id}/resolve")
def resolve_alert(
    id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "resolved"
    alert.resolved_by = current_user.email
    alert.resolved_at = datetime.utcnow()
    db.commit()

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="RESOLVE_ALERT",
        entity_type="ALERT",
        entity_id=str(id),
        details={"alert_title": alert.title}
    )

    return {"status": "resolved", "id": id, "resolved_by": current_user.email}

@router.get("/monitor/status")
def get_monitor_status(
    current_user: User = Depends(require_user)
):
    """Returns background watchlist and system monitoring health status."""
    return {
        "status": "healthy",
        "metrics": MONITOR_METRICS,
        "timestamp": datetime.utcnow().isoformat()
    }
