import os
import csv
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from app.db.models import Entity

logger = logging.getLogger("chainnetra.labels.fiu")

SNAPSHOT_DATE_STR = "2024-12-02"
SNAPSHOT_DATE = datetime(2024, 12, 2, tzinfo=timezone.utc)
STALENESS_THRESHOLD_DAYS = 180

class FiuVaspService:
    @staticmethod
    def is_snapshot_stale() -> bool:
        now = datetime.now(timezone.utc)
        return (now - SNAPSHOT_DATE).days > STALENESS_THRESHOLD_DAYS

    @staticmethod
    def get_staleness_warning() -> Optional[str]:
        if FiuVaspService.is_snapshot_stale():
            now = datetime.now(timezone.utc)
            days = (now - SNAPSHOT_DATE).days
            return f"FIU-IND VASP snapshot is {days} days old (as of {SNAPSHOT_DATE_STR}, > 180 days). Registry data may be out of date."
        return None

    @staticmethod
    def load_fiu_vasp_list(db: Session, csv_path: Optional[str] = None) -> int:
        if not csv_path:
            csv_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "tests", "fixtures", "fiu_vasp_list.csv"
            )
            if not os.path.exists(csv_path):
                csv_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "docs", "research", "fiu_vasp_list.csv"
                )

        if not os.path.exists(csv_path):
            logger.error(f"FIU VASP CSV not found at {csv_path}")
            return 0

        loaded_count = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                legal_name = row.get("name", "").strip()
                if not legal_name:
                    continue

                trade_name = row.get("trade_name", "").strip()
                source = row.get("source", "").strip()

                # Keep nullable fields strictly None when empty
                entity_type = row.get("entity_type", "").strip() or None
                registration_date = row.get("registration_date", "").strip() or None
                nodal_email = row.get("nodal_officer_email", "").strip() or None
                nodal_phone = row.get("nodal_officer_phone", "").strip() or None

                existing = db.query(Entity).filter(Entity.name == legal_name).first()
                trade_names_list = [trade_name] if trade_name else []

                if existing:
                    existing.registered_in_india = True
                    existing.as_of = SNAPSHOT_DATE_STR
                    existing.source = source
                    existing.entity_type = entity_type
                    existing.registration_date = registration_date
                    existing.nodal_officer_email = nodal_email
                    existing.nodal_officer_phone = nodal_phone
                    
                    # Merge trade names if not present
                    try:
                        curr_aliases = json.loads(existing.trade_names or "[]")
                    except Exception:
                        curr_aliases = []
                    for t in trade_names_list:
                        if t and t not in curr_aliases:
                            curr_aliases.append(t)
                    existing.trade_names = json.dumps(curr_aliases)
                else:
                    entity = Entity(
                        name=legal_name,
                        category="VASP",
                        jurisdiction="India",
                        description=f"FIU-IND Registered VASP (as of {SNAPSHOT_DATE_STR})",
                        registered_in_india=True,
                        as_of=SNAPSHOT_DATE_STR,
                        trade_names=json.dumps(trade_names_list),
                        entity_type=entity_type,
                        registration_date=registration_date,
                        nodal_officer_email=nodal_email,
                        nodal_officer_phone=nodal_phone,
                        source=source
                    )
                    db.add(entity)
                    loaded_count += 1

        db.commit()
        logger.info(f"Loaded/Updated {loaded_count} FIU-IND VASP entities")
        return loaded_count

    @staticmethod
    def match_vasp(db: Session, query_name: str) -> Dict[str, Any]:
        """
        Cross-checks an entity query name against the FIU snapshot:
        - Matches legal name or trade name aliases
        - Returns entity details, registration status, and nodal contact readiness
        - If missing from snapshot, returns status 'not in FIU snapshot' (NEVER 'unregistered')
        """
        if not query_name or not query_name.strip():
            return {
                "matched": False,
                "status": "not in FIU snapshot",
                "registered_in_india": False,
                "entity": None,
                "notice_routing": "contact not on file - analyst must add",
                "auto_dispatch_allowed": False
            }

        q = query_name.strip().lower()

        # 1. Direct legal name match (case-insensitive)
        entities = db.query(Entity).all()
        for e in entities:
            if e.name.lower() == q:
                return FiuVaspService._build_match_result(e)

        # 2. Trade name / alias match
        for e in entities:
            try:
                aliases = json.loads(e.trade_names or "[]")
            except Exception:
                aliases = []
            for alias in aliases:
                if alias.lower() == q:
                    return FiuVaspService._build_match_result(e)

        # 3. Known aliases fallback (Binance -> Binance International Limited, Unocoin -> Unocoin Technologies Pvt Ltd, WazirX -> Zanmai Labs Pvt Ltd)
        KNOWN_ALIASES = {
            "binance": "Binance International Limited",
            "unocoin": "Unocoin Technologies Pvt Ltd",
            "wazirx": "Zanmai Labs Pvt Ltd",
            "coinswitch": "Bitcipher Labs LLP",
            "mudrex": "RPFAS Technologies Pvt Ltd",
            "zebpay": "Awlencan Innovations India Limited",
            "coindcx": "Neblio Technologies Private Limited"
        }
        if q in KNOWN_ALIASES:
            target_legal = KNOWN_ALIASES[q]
            matched_ent = db.query(Entity).filter(Entity.name.ilike(target_legal)).first()
            if matched_ent:
                return FiuVaspService._build_match_result(matched_ent)

        # Not in FIU snapshot
        return {
            "matched": False,
            "status": "not in FIU snapshot",
            "registered_in_india": False,
            "entity": None,
            "notice_routing": "contact not on file - analyst must add",
            "auto_dispatch_allowed": False,
            "staleness_warning": FiuVaspService.get_staleness_warning()
        }

    @staticmethod
    def _build_match_result(entity: Entity) -> Dict[str, Any]:
        has_nodal = bool(entity.nodal_officer_email or entity.nodal_officer_phone)
        return {
            "matched": True,
            "status": "registered" if entity.registered_in_india else "not in FIU snapshot",
            "registered_in_india": bool(entity.registered_in_india),
            "entity": {
                "id": entity.id,
                "name": entity.name,
                "trade_names": json.loads(entity.trade_names or "[]"),
                "as_of": entity.as_of,
                "nodal_officer_email": entity.nodal_officer_email,
                "nodal_officer_phone": entity.nodal_officer_phone,
            },
            "notice_routing": "ready" if has_nodal else "contact not on file - analyst must add",
            "auto_dispatch_allowed": has_nodal,
            "staleness_warning": FiuVaspService.get_staleness_warning()
        }
