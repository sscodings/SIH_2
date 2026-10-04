import hmac
import time
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import ApiKey, Complaint
from app.services.complaint_source import ComplaintIngestionPipeline
from app.services.outbox import generate_sahyog_notice, enqueue_outbox
from app.core.audit import log_audit_action

router = APIRouter(prefix="/ingest", tags=["Ingest"])

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()

def authenticate_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> ApiKey:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )
    
    key_hash = hash_api_key(x_api_key)
    prefix = x_api_key[:16]

    # Find active key by hash or prefix match
    api_key = db.query(ApiKey).filter(
        ApiKey.is_active == True,
        (ApiKey.hashed_key == key_hash) | (ApiKey.key_prefix == prefix)
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )

    # Check scopes
    scopes = [s.strip() for s in (api_key.scopes or "ingest:write").split(",")]
    if "ingest:write" not in scopes and api_key.role not in ("admin", "supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key lacks 'ingest:write' scope"
        )

    return api_key

def verify_hmac_and_timestamp(
    request: Request,
    api_key: ApiKey,
    raw_body: bytes,
    x_signature: Optional[str] = Header(None, alias="X-Signature-SHA256"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp")
):
    # 1. Timestamp validation (max 300s clock skew)
    if not x_timestamp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Timestamp header"
        )

    try:
        # Support either UNIX float/int or ISO string
        if x_timestamp.isdigit() or "." in x_timestamp:
            ts_float = float(x_timestamp)
        else:
            ts_dt = datetime.fromisoformat(x_timestamp.replace("Z", "+00:00"))
            ts_float = ts_dt.timestamp()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Timestamp header format"
        )

    now = time.time()
    if abs(now - ts_float) > 300:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Timestamp skew exceeds 300 seconds limit (diff: {abs(now - ts_float):.1f}s)"
        )

    # 2. HMAC signature verification (if secret configured)
    if api_key.secret:
        if not x_signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Signature-SHA256 header"
            )
        
        # Expected signature: HMAC-SHA256(secret, timestamp + "." + body)
        msg = f"{x_timestamp}.{raw_body.decode('utf-8', errors='replace')}".encode("utf-8")
        expected_sig = hmac.new(api_key.secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(expected_sig, x_signature.strip()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid HMAC signature"
            )

@router.post("/complaints")
async def ingest_rest_complaints(
    request: Request,
    api_key: ApiKey = Depends(authenticate_api_key),
    x_signature: Optional[str] = Header(None, alias="X-Signature-SHA256"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    db: Session = Depends(get_db)
):
    raw_body = await request.body()
    verify_hmac_and_timestamp(request, api_key, raw_body, x_signature, x_timestamp)

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON body")

    records: List[Dict[str, Any]] = []
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        if "complaints" in payload and isinstance(payload["complaints"], list):
            records = payload["complaints"]
        else:
            records = [payload]

    results = []
    for rec in records:
        res = ComplaintIngestionPipeline.process_record(
            db=db,
            row=rec,
            source_system=rec.get("source_system") or "REST_INGEST",
            key_id=str(api_key.id)
        )
        results.append(res)

    # Per-key audit log
    log_audit_action(
        db=db,
        user_email=f"api_key:{api_key.name}",
        action="INGEST_REST_COMPLAINT",
        entity_type="COMPLAINT",
        entity_id=str(api_key.id),
        details={"count": len(results), "summary": [r.get("status") for r in results]}
    )

    return {
        "status": "success",
        "processed": len(results),
        "results": results
    }

class SahyogNoticeRequest(BaseModel):
    complaint_number: str
    reason: Optional[str] = "Takedown notice under IT Act s.79(3)(b)"
    target_url: Optional[str] = None

@router.post("/sahyog/export")
def export_sahyog_notice(
    req: SahyogNoticeRequest,
    api_key: ApiKey = Depends(authenticate_api_key),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.complaint_number == req.complaint_number).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    notice = generate_sahyog_notice(complaint, reason=req.reason or "Takedown notice under IT Act s.79(3)(b)")
    
    outbox_msg_id = None
    if req.target_url:
        outbox_msg = enqueue_outbox(
            db=db,
            event_type="sahyog_notice",
            destination_url=req.target_url,
            payload=notice
        )
        outbox_msg_id = outbox_msg.id

    return {
        "status": "generated",
        "notice": notice,
        "outbox_message_id": outbox_msg_id
    }
