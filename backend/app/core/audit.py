import hmac
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.models import AuditLog, AuditCheckpoint
from app.core.config import settings
from app.core.time import utcnow, ensure_utc

logger = logging.getLogger("chainnetra.audit")

GENESIS_HASH = "GENESIS_HASH_000000000000000000000000000000000000000000000000000000000000"

def get_audit_hmac_key() -> str:
    return settings.AUDIT_HMAC_KEY or "chainnetra_audit_fallback_key_2026"

def format_audit_timestamp(ts: Any) -> str:
    """Formats timestamp into ISO string with UTC timezone offset (+00:00)."""
    if isinstance(ts, datetime):
        dt = ensure_utc(ts)
        return dt.isoformat()
    if isinstance(ts, str):
        return ts
    return str(ts)

def compute_entry_hash(
    prev_hash: str,
    timestamp_str: str,
    user_email: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details_json: str
) -> str:
    raw = f"{prev_hash}|{timestamp_str}|{user_email}|{action}|{entity_type}|{entity_id}|{details_json}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def compute_hmac_signature(entry_hash: str, key: str) -> str:
    return hmac.new(key.encode('utf-8'), entry_hash.encode('utf-8'), hashlib.sha256).hexdigest()

def ensure_sqlite_immutability_triggers(db: Session):
    try:
        bind = db.get_bind()
        if "sqlite" in bind.dialect.name:
            db.execute(text("""
                CREATE TRIGGER IF NOT EXISTS prevent_audit_log_update 
                BEFORE UPDATE ON audit_logs 
                BEGIN 
                    SELECT RAISE(ABORT, 'Audit log entries are immutable and cannot be updated'); 
                END;
            """))
            db.execute(text("""
                CREATE TRIGGER IF NOT EXISTS prevent_audit_log_delete 
                BEFORE DELETE ON audit_logs 
                BEGIN 
                    SELECT RAISE(ABORT, 'Audit log entries cannot be deleted'); 
                END;
            """))
            db.commit()
    except Exception as e:
        logger.debug(f"Triggers already set or unsupported: {e}")

def create_audit_checkpoint(db: Session, last_audit_id: int, last_entry_hash: str):
    key = get_audit_hmac_key()
    checkpoint_payload = f"CHECKPOINT:{last_audit_id}:{last_entry_hash}"
    checkpoint_sig = hmac.new(key.encode('utf-8'), checkpoint_payload.encode('utf-8'), hashlib.sha256).hexdigest()

    cp = AuditCheckpoint(
        last_audit_id=last_audit_id,
        last_entry_hash=last_entry_hash,
        checkpoint_signature=checkpoint_sig,
        created_at=utcnow()
    )
    db.add(cp)
    db.commit()

def log_audit_action(
    db: Session,
    user_email: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: Optional[dict] = None
) -> AuditLog:
    # Ensure immutability triggers on DB
    ensure_sqlite_immutability_triggers(db)

    # Lock & serialize write transaction
    bind = db.get_bind()
    if "sqlite" in bind.dialect.name:
        try:
            db.execute(text("BEGIN IMMEDIATE"))
        except Exception:
            pass

    # Query last audit entry to establish linear chain
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_log.entry_hash if last_log and last_log.entry_hash else GENESIS_HASH

    now_utc = utcnow()
    ts_str = format_audit_timestamp(now_utc)
    details_str = json.dumps(details or {}, sort_keys=True)

    entry_hash = compute_entry_hash(
        prev_hash=prev_hash,
        timestamp_str=ts_str,
        user_email=user_email,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id or ""),
        details_json=details_str
    )

    hmac_key = get_audit_hmac_key()
    signature = compute_hmac_signature(entry_hash, hmac_key)

    audit_entry = AuditLog(
        timestamp=now_utc,
        user_email=user_email,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id or ""),
        details=details_str,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        signature=signature
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)

    # Checkpoint generation check
    checkpoint_interval = getattr(settings, "AUDIT_CHECKPOINT_INTERVAL", 50)
    if audit_entry.id % checkpoint_interval == 0:
        create_audit_checkpoint(db, audit_entry.id, entry_hash)

    return audit_entry

def verify_audit_chain(db: Session) -> dict:
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    if not logs:
        return {"valid": True, "count": 0, "message": "Audit chain empty, valid."}

    hmac_key = get_audit_hmac_key()
    expected_prev = GENESIS_HASH

    for idx, entry in enumerate(logs):
        # 1. Verify Prev Hash Chain Link
        if entry.prev_hash != expected_prev:
            return {
                "valid": False,
                "broken_at_id": entry.id,
                "broken_at_index": idx,
                "reason": f"Mismatched prev_hash at entry {entry.id}. Expected: {expected_prev}, Got: {entry.prev_hash}"
            }

        # 2. Recompute Entry SHA-256 Hash
        ts_str = format_audit_timestamp(entry.timestamp)
        recomputed_hash = compute_entry_hash(
            prev_hash=entry.prev_hash,
            timestamp_str=ts_str,
            user_email=entry.user_email,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id or "",
            details_json=entry.details or "{}"
        )

        if recomputed_hash != entry.entry_hash:
            # Backward-compatibility fallback for pre-F5 chains
            if isinstance(entry.timestamp, datetime):
                legacy_candidates = [
                    entry.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                    ensure_utc(entry.timestamp).replace(microsecond=0).isoformat(),
                ]
            else:
                legacy_candidates = [str(entry.timestamp)[:19].replace(" ", "T")]

            matched = False
            for cand in legacy_candidates:
                alt_hash = compute_entry_hash(
                    prev_hash=entry.prev_hash,
                    timestamp_str=cand,
                    user_email=entry.user_email,
                    action=entry.action,
                    entity_type=entry.entity_type,
                    entity_id=entry.entity_id or "",
                    details_json=entry.details or "{}"
                )
                if alt_hash == entry.entry_hash:
                    recomputed_hash = alt_hash
                    matched = True
                    break

            if not matched:
                return {
                    "valid": False,
                    "broken_at_id": entry.id,
                    "broken_at_index": idx,
                    "reason": f"Tampered entry hash at entry {entry.id}. Recomputed {recomputed_hash} != Recorded {entry.entry_hash}"
                }

        # 3. Verify HMAC Signature
        if entry.signature:
            recomputed_sig = compute_hmac_signature(entry.entry_hash, hmac_key)
            if not hmac.compare_digest(recomputed_sig, entry.signature):
                return {
                    "valid": False,
                    "broken_at_id": entry.id,
                    "broken_at_index": idx,
                    "reason": f"Cryptographic HMAC signature mismatch at entry {entry.id}. Unauthorized off-chain rewrite detected."
                }

        expected_prev = entry.entry_hash

    # 4. Verify Checkpoints
    checkpoints = db.query(AuditCheckpoint).order_by(AuditCheckpoint.id.asc()).all()
    for cp in checkpoints:
        expected_cp_payload = f"CHECKPOINT:{cp.last_audit_id}:{cp.last_entry_hash}"
        expected_cp_sig = hmac.new(hmac_key.encode('utf-8'), expected_cp_payload.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_cp_sig, cp.checkpoint_signature):
            return {
                "valid": False,
                "broken_at_checkpoint_id": cp.id,
                "reason": f"Audit checkpoint #{cp.id} has invalid HMAC signature."
            }

    return {
        "valid": True,
        "count": len(logs),
        "checkpoints_count": len(checkpoints),
        "message": f"All {len(logs)} audit entries verified intact with valid SHA-256 chain of custody and HMAC-SHA256 signatures."
    }
