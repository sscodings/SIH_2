import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from app.core.time import utcnow
import httpx
from sqlalchemy.orm import Session

from app.db.models import OutboxMessage, Complaint

logger = logging.getLogger("chainnetra.services.outbox")

def enqueue_outbox(
    db: Session,
    event_type: str,
    destination_url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> OutboxMessage:
    """Enqueues an outgoing notification or webhook to the outbox queue."""
    msg = OutboxMessage(
        event_type=event_type,
        destination_url=destination_url,
        payload=json.dumps(payload),
        headers=json.dumps(headers or {}),
        status="pending",
        retry_count=0,
        max_retries=3,
        next_retry_at=utcnow()
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

async def process_outbox_batch(db: Session, max_items: int = 20) -> List[Dict[str, Any]]:
    """Processes pending or retry-ready outbox messages."""
    now = utcnow()
    messages = db.query(OutboxMessage).filter(
        OutboxMessage.status.in_(["pending", "retry"]),
        OutboxMessage.next_retry_at <= now
    ).order_by(OutboxMessage.created_at.asc()).limit(max_items).all()

    results = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for msg in messages:
            try:
                headers = json.loads(msg.headers or "{}")
                payload = json.loads(msg.payload or "{}")
                headers.setdefault("Content-Type", "application/json")
                
                resp = await client.post(msg.destination_url, json=payload, headers=headers)
                if 200 <= resp.status_code < 300:
                    msg.status = "sent"
                    msg.sent_at = utcnow()
                    results.append({"id": msg.id, "status": "sent", "code": resp.status_code})
                else:
                    msg.retry_count += 1
                    msg.error_message = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    if msg.retry_count >= msg.max_retries:
                        msg.status = "failed"
                    else:
                        msg.status = "retry"
                        delay_seconds = (2 ** msg.retry_count) * 5
                        msg.next_retry_at = utcnow() + timedelta(seconds=delay_seconds)
                    results.append({"id": msg.id, "status": msg.status, "code": resp.status_code})
            except Exception as exc:
                msg.retry_count += 1
                msg.error_message = str(exc)[:500]
                if msg.retry_count >= msg.max_retries:
                    msg.status = "failed"
                else:
                    msg.status = "retry"
                    delay_seconds = (2 ** msg.retry_count) * 5
                    msg.next_retry_at = utcnow() + timedelta(seconds=delay_seconds)
                results.append({"id": msg.id, "status": msg.status, "error": str(exc)})
    
    db.commit()
    return results

def generate_sahyog_notice(complaint: Complaint, reason: str = "Takedown notice under IT Act s.79(3)(b)") -> Dict[str, Any]:
    """
    Generates an outbound SAHYOG notice format for intermediary coordination.
    Note: SAHYOG is strictly an outbound notice export format, NOT an inbound complaint feed.
    """
    try:
        wallets = json.loads(complaint.reported_wallets or "[]")
    except Exception:
        wallets = []

    return {
        "notice_type": "IT_ACT_S79_3_B",
        "legal_basis": "Information Technology Act, 2000 Section 79(3)(b)",
        "disclaimer": "DISCLAIMER: UNVERIFIED PROTOTYPE EXPORT - GENERATED FOR INTERMEDIARY COORDINATION UNDER IT ACT S.79(3)(b)",
        "complaint_number": complaint.complaint_number,
        "source_system": complaint.source_system or "NCRP",
        "suspect_wallets": wallets,
        "chain": complaint.chain,
        "claimed_vasp": complaint.claimed_vasp_hint,
        "amount_lost_inr": complaint.amount_lost_inr,
        "incident_at": complaint.incident_at.isoformat() if complaint.incident_at else None,
        "reason": reason,
        "exported_at": utcnow().isoformat()
    }
