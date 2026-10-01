import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Complaint
from app.core.audit import log_audit_action
from app.core.time import utcnow

logger = logging.getLogger("chainnetra.retention")

# Read retention policy from decisions.md. If absent, default to None ("no automatic purge").
RETENTION_DAYS_CONFIG: Optional[int] = None

def check_retention_startup():
    if RETENTION_DAYS_CONFIG is None:
        logger.warning(
            "DPDP Retention Notice: No retention numbers defined in decisions.md. "
            "Defaulting to 'no automatic purge'. Legal review required."
        )

def purge_expired_records(
    db: Session,
    retention_days: Optional[int] = None,
    actor_email: str = "system@chainnetra"
) -> Dict[str, Any]:
    """
    Purges/anonymizes records older than retention window unless legal_hold=True.
    Actions are immutably audit-logged.
    """
    days = retention_days if retention_days is not None else RETENTION_DAYS_CONFIG
    if days is None or days <= 0:
        return {
            "purged_count": 0,
            "skipped_legal_hold": 0,
            "status": "NO_AUTOMATIC_PURGE_CONFIGURED"
        }

    cutoff = utcnow() - timedelta(days=days)
    
    # Query candidate complaints older than cutoff
    candidates = db.query(Complaint).filter(Complaint.reported_at < cutoff).all()
    
    purged_count = 0
    skipped_legal_hold = 0

    for c in candidates:
        if c.legal_hold:
            skipped_legal_hold += 1
            continue

        # Anonymize personal data
        c.victim_ref = None
        c.victim_name = "ANONYMIZED_PURGED"
        c.claimed_vasp_hint = None
        purged_count += 1

    db.commit()

    if purged_count > 0:
        log_audit_action(
            db=db,
            user_email=actor_email,
            action="DPDP_RETENTION_PURGE",
            entity_type="COMPLAINTS",
            entity_id="BULK",
            details={
                "purged_count": purged_count,
                "skipped_legal_hold": skipped_legal_hold,
                "retention_days": days,
                "cutoff": cutoff.isoformat()
            }
        )

    return {
        "purged_count": purged_count,
        "skipped_legal_hold": skipped_legal_hold,
        "retention_days": days,
        "cutoff": cutoff.isoformat(),
        "status": "PURGE_COMPLETED"
    }
