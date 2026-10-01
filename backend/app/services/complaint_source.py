import os
import csv
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.db.models import Complaint, ComplaintWallet, Case, CaseComplaint, Label, Alert
from app.core.config import settings
from app.core.addresses import validate_address, validate_tx_hash, normalize
from app.labels.fiu import FiuVaspService

logger = logging.getLogger("chainnetra.services.complaint_source")

class ComplaintSource(ABC):
    @abstractmethod
    def fetch_complaints(self) -> List[Dict[str, Any]]:
        pass

class MockNcrpSource(ComplaintSource):
    def __init__(self, fixture_path: Optional[str] = None):
        self.fixture_path = fixture_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "tests", "fixtures", "sample_complaint.csv"
        )

    def fetch_complaints(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.fixture_path):
            return []
        records = []
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records

class ComplaintIngestionPipeline:
    @staticmethod
    def parse_incident_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str or not date_str.strip():
            return None
        s = date_str.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None

    @staticmethod
    def process_record(
        db: Session,
        row: Dict[str, Any],
        source_system: str = "NCRP",
        key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Normalize headers (handle standard & legacy headers)
        complaint_num = (row.get("complaint_id") or row.get("complaint_number") or "").strip()
        if not complaint_num:
            return {"status": "rejected", "error": "Missing complaint_id / complaint_number"}

        # Idempotency check: unique (source_system, complaint_number)
        existing = db.query(Complaint).filter(
            Complaint.source_system == source_system,
            Complaint.complaint_number == complaint_num
        ).first()

        if existing:
            return {
                "status": "duplicate",
                "complaint_id": existing.id,
                "complaint_number": existing.complaint_number,
                "message": f"Duplicate complaint {complaint_num} for source {source_system}"
            }

        data_origin = (row.get("data_origin") or "REAL").strip().upper()
        victim_state = (row.get("state") or row.get("victim_state") or "Maharashtra").strip()
        fraud_type = (row.get("category") or row.get("fraud_type") or "Cyber Fraud").strip()
        
        # Raw wallet and chain hint
        raw_wallet = (row.get("suspect_wallet_address") or row.get("wallet") or row.get("address") or "").strip()
        chain_hint = (row.get("chain") or "").strip().lower()

        # 2. Checksum validation & Format vs Hint enforcement
        addr_val = validate_address(raw_wallet, chain_hint=chain_hint)
        if not addr_val["valid"]:
            return {
                "status": "rejected",
                "complaint_number": complaint_num,
                "error": f"Invalid wallet address: {addr_val.get('error')}"
            }

        detected_family = addr_val["family"]
        # Format overrides hint: e.g. SYN-0009 Tron address with ETH hint
        chain_norm = detected_family
        mismatch_logged = False
        if chain_hint and chain_hint not in ("ethereum", "eth", "evm") and detected_family == "evm":
            chain_norm = chain_hint  # specific EVM chain like polygon
        elif chain_hint and chain_hint != detected_family:
            mismatch_logged = True
            logger.warning(
                f"Chain hint mismatch for complaint {complaint_num}: hint was '{chain_hint}' "
                f"but address format is '{detected_family}'. Using format '{detected_family}'."
            )

        norm_address = normalize(chain_norm, raw_wallet)

        # 3. Amount lost (blank -> amount_unknown=True, never default to 0)
        raw_amount = row.get("amount_inr")
        amount_lost_inr = 0.0
        amount_unknown = False
        if raw_amount is None or str(raw_amount).strip() == "":
            amount_unknown = True
            amount_lost_inr = 0.0
        else:
            try:
                amount_lost_inr = float(str(raw_amount).strip())
            except ValueError:
                amount_unknown = True
                amount_lost_inr = 0.0

        amount_lost_usd = round(amount_lost_inr / getattr(settings, "USD_INR", 83.50), 2) if not amount_unknown else 0.0

        # 4. Incident date
        incident_date_raw = row.get("incident_date") or row.get("incident_at")
        incident_at = ComplaintIngestionPipeline.parse_incident_date(incident_date_raw)

        # 5. PII Encryption (Fernet encrypt at rest via EncryptedString in models)
        victim_ref_raw = (row.get("victim_id_masked") or row.get("victim_ref") or row.get("victim_name") or f"V****{complaint_num[-4:]}").strip()

        # 6. Tx Hash normalization & validation
        txn_hash_raw = (row.get("txn_hash") or "").strip()
        valid_tx_hash = None
        if txn_hash_raw:
            if validate_tx_hash(txn_hash_raw, chain=chain_norm):
                valid_tx_hash = txn_hash_raw
            else:
                logger.warning(f"Invalid tx_hash format '{txn_hash_raw}' on chain '{chain_norm}' for complaint {complaint_num}")

        # 7. Claimed VASP cross-check against FIU snapshot
        claimed_vasp = (row.get("bank_or_exchange_named") or row.get("claimed_vasp_hint") or "").strip() or None
        claimed_fiu_info = None
        if claimed_vasp:
            match_res = FiuVaspService.match_vasp(db, claimed_vasp)
            claimed_fiu_info = match_res.get("status")

        # 8. Check known VASP label on reported wallet
        vasp_label = db.query(Label).filter(
            Label.chain == chain_norm,
            Label.address == norm_address,
            Label.category.in_(["VASP", "CEX", "vasp", "cex"]),
            Label.record_status == "active"
        ).first()

        vasp_flag = None
        if vasp_label:
            vasp_flag = "reported wallet is a known VASP"

        # 9. Priority calculation
        if amount_unknown:
            priority = "Medium"
        elif amount_lost_inr > 2000000:
            priority = "Critical"
        elif amount_lost_inr >= 500000:
            priority = "High"
        else:
            priority = "Medium"

        # 10. Cross-complaint linking using complaint_wallets table
        matching_wallets = db.query(ComplaintWallet).filter(
            ComplaintWallet.chain == chain_norm,
            ComplaintWallet.normalized_address == norm_address
        ).all()

        linked_ids = []
        if matching_wallets:
            existing_complaint_ids = set(w.complaint_id for w in matching_wallets)
            existing_complaints = db.query(Complaint).filter(Complaint.id.in_(existing_complaint_ids)).all()
            for ec in existing_complaints:
                linked_ids.append(ec.complaint_number)
                # Bi-directional update
                try:
                    ec_linked = json.loads(ec.linked_complaint_ids or "[]")
                except Exception:
                    ec_linked = []
                if complaint_num not in ec_linked:
                    ec_linked.append(complaint_num)
                    ec.linked_complaint_ids = json.dumps(ec_linked)

            # Raise linked complaint alert
            alert = Alert(
                alert_type="NEW_LINKED_COMPLAINT",
                severity="Medium",
                title=f"New Linked Complaint Discovered: {complaint_num}",
                message=f"Wallet {norm_address} on {chain_norm} links {complaint_num} with existing complaints: {linked_ids}",
                address=norm_address,
                chain=chain_norm
            )
            db.add(alert)

        # 11. Check for Sanctions match on reported wallet (CRITICAL alert)
        sanction_label = db.query(Label).filter(
            Label.address == norm_address,
            Label.category.in_(["sanctioned", "Sanctioned", "SANCTIONED"]),
            Label.record_status == "active"
        ).first()

        if sanction_label:
            crit_alert = Alert(
                alert_type="SANCTIONED_ENTITY_HIT",
                severity="Critical",
                title=f"CRITICAL: Sanctioned Wallet Reported in Complaint {complaint_num}",
                message=f"Reported wallet {norm_address} on {chain_norm} matches OFAC SDN entity: '{sanction_label.entity}'",
                address=norm_address,
                chain=chain_norm
            )
            db.add(crit_alert)

        # 12. Create Complaint record
        complaint = Complaint(
            complaint_number=complaint_num,
            source_system=source_system,
            source=source_system,
            data_origin=data_origin,
            victim_name="Masked Complainant",
            victim_ref=victim_ref_raw,
            victim_state=victim_state,
            fraud_type=fraud_type,
            reported_wallets=json.dumps([raw_wallet]),
            chain=chain_norm,
            amount_lost_inr=amount_lost_inr,
            amount_lost_usd=amount_lost_usd,
            amount_unknown=amount_unknown,
            incident_at=incident_at,
            reported_at=datetime.utcnow(),
            txn_hash=valid_tx_hash,
            claimed_vasp_hint=claimed_vasp,
            linked_complaint_ids=json.dumps(linked_ids),
            vasp_flag=vasp_flag,
            status="New",
            priority=priority,
            raw_payload=json.dumps({
                "chain_hint_mismatch": mismatch_logged,
                "detected_family": detected_family,
                "claimed_fiu_status": claimed_fiu_info,
                "api_key_id": key_id
            })
        )
        db.add(complaint)
        db.flush()

        # Insert into complaint_wallets table
        cw = ComplaintWallet(
            complaint_id=complaint.id,
            chain=chain_norm,
            normalized_address=norm_address,
            is_primary=True,
            created_at=datetime.utcnow()
        )
        db.add(cw)

        # 13. Auto-Case Creation (decisions.md item 2: AUTO_CASE_MIN_PRIORITY = "High")
        case_created = False
        min_auto_priority = getattr(settings, "AUTO_CASE_MIN_PRIORITY", "High")
        priority_levels = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}

        if priority_levels.get(priority, 1) >= priority_levels.get(min_auto_priority, 3):
            # Only auto-create case if reported wallet is NOT a known VASP
            if not vasp_flag:
                case_title = f"{fraud_type} Investigation - {complaint_num}"
                new_case = Case(
                    case_number=f"CASE-{complaint_num}",
                    title=case_title,
                    description=f"Auto-generated from complaint {complaint_num}. State: {victim_state}",
                    primary_chain=chain_norm,
                    primary_address=norm_address,
                    status="Active",
                    priority=priority,
                    data_origin=data_origin,
                    created_by=f"auto-triage:{source_system}"
                )
                db.add(new_case)
                db.flush()

                cc = CaseComplaint(case_id=new_case.id, complaint_id=complaint.id)
                db.add(cc)
                case_created = True

        db.commit()

        return {
            "status": "accepted",
            "complaint_id": complaint.id,
            "complaint_number": complaint.complaint_number,
            "chain": chain_norm,
            "priority": priority,
            "amount_unknown": amount_unknown,
            "linked_complaints": linked_ids,
            "vasp_flag": vasp_flag,
            "case_created": case_created,
            "sanctions_hit": bool(sanction_label)
        }
