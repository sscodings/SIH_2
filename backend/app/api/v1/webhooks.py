import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from backend.app.db.database import get_db
from backend.app.db.models import Webhook, WebhookDelivery
from backend.app.services.webhooks import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Integrations"])

class WebhookCreate(BaseModel):
    name: str
    target_url: str
    events: List[str] = ["trace_complete", "vasp_found", "freeze_alert"]
    secret: Optional[str] = "netra_wh_secret_xyz"

@router.get("")
def list_webhooks(db: Session = Depends(get_db)):
    hooks = db.query(Webhook).all()
    results = []
    for h in hooks:
        recent_deliv = db.query(WebhookDelivery).filter(WebhookDelivery.webhook_id == h.id).order_by(WebhookDelivery.id.desc()).limit(5).all()
        results.append({
            "id": h.id,
            "name": h.name,
            "target_url": h.target_url,
            "events": json.loads(h.events or "[]"),
            "is_active": h.is_active,
            "deliveries": [
                {
                    "event": d.event_type,
                    "status_code": d.status_code,
                    "latency_ms": d.latency_ms,
                    "success": d.success,
                    "timestamp": d.created_at.isoformat()
                }
                for d in recent_deliv
            ]
        })
    return {"webhooks": results}

@router.post("")
def create_webhook(payload: WebhookCreate, db: Session = Depends(get_db)):
    hook = Webhook(
        name=payload.name,
        target_url=payload.target_url,
        events=json.dumps(payload.events),
        secret=payload.secret or "netra_secret"
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)
    return {"status": "created", "id": hook.id}

@router.post("/{id}/test")
async def test_webhook(id: int, db: Session = Depends(get_db)):
    hook = db.query(Webhook).filter(Webhook.id == id).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    test_payload = {
        "event": "test_ping",
        "case_id": 1,
        "message": "Test transmission from ChainNetra Forensic Dispatcher"
    }
    await WebhookService.dispatch_event(db, "test_ping", test_payload)
    return {"status": "dispatched", "webhook_id": id}
