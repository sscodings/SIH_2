import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import Label
from app.labels.base import LabelRecord
from app.core.addresses import normalize

logger = logging.getLogger("chainnetra.labels.service")

RELIABILITY_TIERS = {
    "verified_authority": 1.0,
    "analyst_approved": 0.95,
    "exchange_self_disclosure": 0.90,
    "unverified_official": 0.85,
    "community": 0.70,
    "manual": 0.80
}

class LabelService:
    @staticmethod
    def get_tier_weight(tier: str) -> float:
        return RELIABILITY_TIERS.get((tier or "").lower(), 0.80)

    @staticmethod
    def save_records(db: Session, records: List[LabelRecord]) -> Dict[str, int]:
        """
        Saves incoming LabelRecords non-destructively:
        - Never overwrites silently; inserts new records or updates status
        - If existing record has same chain & address, stores both to preserve history
        """
        added = 0
        updated = 0

        for r in records:
            norm_addr = normalize(r.chain, r.address)

            # Check if identical record already exists
            existing = db.query(Label).filter(
                Label.chain == r.chain.lower(),
                Label.address == norm_addr,
                Label.entity == r.entity,
                Label.source == r.source
            ).first()

            if existing:
                # Update status/validity if changed
                if existing.record_status != r.record_status or existing.valid_to != r.valid_to:
                    existing.record_status = r.record_status
                    existing.valid_to = r.valid_to
                    existing.superseded_by = r.superseded_by
                    existing.wallet_type = r.wallet_type
                    updated += 1
            else:
                lbl = Label(
                    chain=r.chain.lower(),
                    address=norm_addr,
                    entity=r.entity,
                    category=r.category,
                    source=r.source,
                    source_url=r.source_url,
                    license=r.license,
                    weight_tier=r.weight_tier,
                    wallet_type=r.wallet_type,
                    raw_wallet_type=r.raw_wallet_type,
                    valid_from=r.valid_from,
                    valid_to=r.valid_to,
                    superseded_by=r.superseded_by,
                    record_status=r.record_status,
                    snapshot_date=r.snapshot_date,
                    confidence=LabelService.get_tier_weight(r.weight_tier),
                    verified_at=r.verified_at,
                    fetched_at=r.fetched_at or datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db.add(lbl)
                added += 1

        db.commit()
        return {"added": added, "updated": updated}

    @staticmethod
    def lookup_attribute(
        db: Session,
        chain: str,
        address: str,
        transfer_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Looks up labels for an address on a chain:
        - Only active records can attribute
        - Respects valid_from and valid_to window
        - Conflicts: selects higher-reliability label, lists conflicting labels in evidence
        """
        c = (chain or "").lower().strip()
        norm_addr = normalize(c, address)

        # Query all matching labels
        labels: List[Label] = db.query(Label).filter(
            Label.chain == c,
            Label.address == norm_addr
        ).all()

        if not labels:
            return None

        # Filter out inactive, revoked, or pending labels
        active_candidates = []
        conflicts = []

        for lbl in labels:
            status = (lbl.record_status or "active").lower()
            if status != "active":
                continue

            # Check time validity window
            if transfer_time is not None:
                t_utc = transfer_time.replace(tzinfo=timezone.utc) if transfer_time.tzinfo is None else transfer_time
                if lbl.valid_from is not None:
                    vf_utc = lbl.valid_from.replace(tzinfo=timezone.utc) if lbl.valid_from.tzinfo is None else lbl.valid_from
                    if t_utc < vf_utc:
                        continue
                if lbl.valid_to is not None:
                    vt_utc = lbl.valid_to.replace(tzinfo=timezone.utc) if lbl.valid_to.tzinfo is None else lbl.valid_to
                    if t_utc > vt_utc:
                        continue

            active_candidates.append(lbl)

        if not active_candidates:
            return None

        # Sort candidates by reliability weight tier
        active_candidates.sort(
            key=lambda x: LabelService.get_tier_weight(x.weight_tier),
            reverse=True
        )

        chosen = active_candidates[0]
        if len(active_candidates) > 1:
            for other in active_candidates[1:]:
                conflicts.append({
                    "entity": other.entity,
                    "category": other.category,
                    "source": other.source,
                    "weight_tier": other.weight_tier,
                    "wallet_type": other.wallet_type
                })

        return {
            "entity": chosen.entity,
            "category": chosen.category,
            "source": chosen.source,
            "source_url": chosen.source_url,
            "weight_tier": chosen.weight_tier,
            "wallet_type": chosen.wallet_type,
            "confidence": LabelService.get_tier_weight(chosen.weight_tier),
            "record_status": chosen.record_status,
            "conflicts": conflicts,
            "superseded_by": chosen.superseded_by
        }
