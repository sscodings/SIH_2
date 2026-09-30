import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.db.models import AuditLog

def compute_entry_hash(prev_hash: str, timestamp_str: str, user_email: str, action: str, entity_type: str, entity_id: str, details_json: str) -> str:
    raw = f"{prev_hash}|{timestamp_str}|{user_email}|{action}|{entity_type}|{entity_id}|{details_json}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def log_audit_action(db: Session, user_email: str, action: str, entity_type: str, entity_id: str, details: dict = None) -> AuditLog:
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_log.entry_hash if last_log and last_log.entry_hash else "GENESIS_HASH_000000000000000000000000000000000000000000000000000000000000"
    
    timestamp = datetime.now(timezone.utc)
    # Store and compute with standardized string format
    ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    details_str = json.dumps(details or {}, sort_keys=True)
    entry_hash = compute_entry_hash(prev_hash, ts_str, user_email, action, entity_type, entity_id, details_str)
    
    audit_entry = AuditLog(
        timestamp=timestamp,
        user_email=user_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details_str,
        prev_hash=prev_hash,
        entry_hash=entry_hash
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

def verify_audit_chain(db: Session) -> dict:
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    if not logs:
        return {"valid": True, "count": 0, "message": "Audit chain empty, valid."}
    
    expected_prev = "GENESIS_HASH_000000000000000000000000000000000000000000000000000000000000"
    for idx, entry in enumerate(logs):
        if entry.prev_hash != expected_prev:
            return {
                "valid": False,
                "broken_at_id": entry.id,
                "broken_at_index": idx,
                "reason": f"Mismatched prev_hash at entry {entry.id}. Expected: {expected_prev}, Got: {entry.prev_hash}"
            }
        # Format entry.timestamp with identical %Y-%m-%d %H:%M:%S
        ts_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if isinstance(entry.timestamp, datetime) else str(entry.timestamp)[:19]
        recomputed = compute_entry_hash(
            entry.prev_hash,
            ts_str,
            entry.user_email,
            entry.action,
            entry.entity_type,
            entry.entity_id or "",
            entry.details or "{}"
        )
        if recomputed != entry.entry_hash:
            return {
                "valid": False,
                "broken_at_id": entry.id,
                "broken_at_index": idx,
                "reason": f"Tampered entry hash at entry {entry.id}. Recomputed {recomputed} != Recorded {entry.entry_hash}"
            }
        expected_prev = entry.entry_hash
        
    return {"valid": True, "count": len(logs), "message": f"All {len(logs)} audit entries verified intact with valid SHA-256 chain of custody."}
