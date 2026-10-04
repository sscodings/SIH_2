import json
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

from app.db.database import get_db
from app.db.models import Webhook, WebhookDelivery, User
from app.services.webhooks import WebhookService, validate_webhook_url, SSRFValidationError
from app.core.security import require_role
from app.core.audit import log_audit_action

router = APIRouter(prefix="/webhooks", tags=["Webhooks & Integrations"])

class WebhookCreate(BaseModel):
    name: str
    target_url: str
    events: List[str] = ["trace_complete", "vasp_found", "freeze_alert"]

@router.get("")
def list_webhooks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    total = db.query(Webhook).count()
    hooks = db.query(Webhook).offset(skip).limit(limit).all()
    results = []
    for h in hooks:
        recent_deliv = db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == h.id
        ).order_by(WebhookDelivery.id.desc()).limit(5).all()
        results.append({
            "id": h.id,
            "name": h.name,
            "target_url": h.target_url,
            "events": json.loads(h.events or "[]"),
            "is_active": h.is_active,
            "created_at": h.created_at.isoformat() if h.created_at else None,
            "deliveries": [
                {
                    "event": d.event_type,
                    "status_code": d.status_code,
                    "latency_ms": d.latency_ms,
                    "success": d.success,
                    "attempt_count": d.attempt_count,
                    "response_body": d.response_body,
                    "timestamp": d.created_at.isoformat()
                }
                for d in recent_deliv
            ]
        })
    return {"total": total, "webhooks": results}

@router.post("")
def create_webhook(
    payload: WebhookCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    # Validate target URL against SSRF and private networks
    try:
        clean_url, hostname = validate_webhook_url(payload.target_url, db=db)
    except SSRFValidationError as e:
        raise HTTPException(status_code=400, detail=f"SSRF validation failed: {str(e)}")

    # Generate a cryptographically strong unique webhook signing secret
    generated_secret = secrets.token_hex(24)

    hook = Webhook(
        name=payload.name,
        target_url=clean_url,
        events=json.dumps(payload.events),
        secret=generated_secret,
        is_active=True
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="CREATE_WEBHOOK",
        entity_type="WEBHOOK",
        entity_id=str(hook.id),
        details={"name": hook.name, "target_url": clean_url}
    )

    # Return secret ONCE upon creation
    return {
        "status": "created",
        "id": hook.id,
        "name": hook.name,
        "target_url": hook.target_url,
        "signing_secret": generated_secret,
        "notice": "Store this signing_secret securely. It will not be shown again."
    }

@router.post("/{id}/test")
async def test_webhook(
    id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    hook = db.query(Webhook).filter(Webhook.id == id).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    test_payload = {
        "event": "test_ping",
        "case_id": 1,
        "message": "Test transmission from ChainNetra Forensic Dispatcher",
        "triggered_by": current_user.email
    }
    await WebhookService.dispatch_event(db, "test_ping", test_payload)

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="TEST_WEBHOOK",
        entity_type="WEBHOOK",
        entity_id=str(hook.id),
        details={"name": hook.name}
    )

    return {"status": "dispatched", "webhook_id": id}
