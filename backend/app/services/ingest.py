import re
import json
import csv
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models import Complaint, Case, CaseComplaint
from backend.app.core.config import settings

TRON_REGEX = re.compile(r"^T[1-9A-HJ-NP-za-km-z]{33}$")
BTC_REGEX = re.compile(r"^(1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{11,70})$")
EVM_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")

class IngestionService:
    @staticmethod
    def detect_chain_and_validate(address: str) -> Dict[str, Any]:
        address = address.strip()
        if TRON_REGEX.match(address):
            return {"valid": True, "chain": "tron", "standard": "TRC-20 / Base58", "address": address}
        if BTC_REGEX.match(address):
            return {"valid": True, "chain": "bitcoin", "standard": "Bitcoin (Legacy/SegWit/Bech32)", "address": address}
        if EVM_REGEX.match(address):
            return {"valid": True, "chain": "ethereum", "supported_evm_chains": ["ethereum", "bsc", "polygon", "arbitrum"], "standard": "EVM (ERC-20 / BEP-20)", "address": address}
        
        return {"valid": False, "chain": "unknown", "error": "Address does not conform to Tron, Bitcoin, or EVM formats", "address": address}

    @staticmethod
    def ingest_single_complaint(
        db: Session,
        victim_name: str,
        victim_state: str,
        fraud_type: str,
        reported_wallets: List[str],
        amount_lost_inr: float,
        source: str = "NCRP",
        complaint_number: Optional[str] = None
    ) -> Complaint:
        if not complaint_number:
            c_count = db.query(Complaint).count() + 1001
            complaint_number = f"{source}-2026-{c_count:06d}"

        chain = "tron"
        if reported_wallets:
            detection = IngestionService.detect_chain_and_validate(reported_wallets[0])
            if detection["valid"]:
                chain = detection["chain"]

        amount_lost_usd = round(amount_lost_inr / settings.USD_INR, 2)
        priority = "Critical" if amount_lost_inr > 2000000 else ("High" if amount_lost_inr > 700000 else "Medium")

        existing_matches = []
        for w in reported_wallets:
            prev = db.query(Complaint).filter(Complaint.reported_wallets.contains(w)).all()
            if prev:
                existing_matches.extend(prev)

        complaint = Complaint(
            complaint_number=complaint_number,
            source=source,
            victim_name=victim_name,
            victim_state=victim_state,
            fraud_type=fraud_type,
            reported_wallets=json.dumps(reported_wallets),
            chain=chain,
            amount_lost_inr=amount_lost_inr,
            amount_lost_usd=amount_lost_usd,
            reported_at=datetime.now(timezone.utc),
            status="New",
            priority=priority,
            raw_payload=json.dumps({"duplicate_hits": len(existing_matches)})
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return complaint

    @staticmethod
    def process_csv_upload(db: Session, file_content: str) -> Dict[str, Any]:
        reader = csv.DictReader(io.StringIO(file_content))
        total_rows = 0
        valid_rows = 0
        errors = []
        created_complaints = []

        for idx, row in enumerate(reader, start=1):
            total_rows += 1
            wallet = row.get("wallet", row.get("address", "")).strip()
            amount_str = row.get("amount_inr", row.get("amount", "0")).replace(",", "").strip()

            if not wallet:
                errors.append(f"Row {idx}: Missing wallet address")
                continue

            val = IngestionService.detect_chain_and_validate(wallet)
            if not val["valid"]:
                errors.append(f"Row {idx}: Invalid address format '{wallet}'")
                continue

            try:
                amt = float(amount_str)
            except ValueError:
                amt = 50000.0

            cmp = IngestionService.ingest_single_complaint(
                db=db,
                victim_name=row.get("victim_name", f"Victim {idx}"),
                victim_state=row.get("victim_state", "Maharashtra"),
                fraud_type=row.get("fraud_type", "Investment Scam"),
                reported_wallets=[wallet],
                amount_lost_inr=amt,
                source="Bulk"
            )
            created_complaints.append(cmp.complaint_number)
            valid_rows += 1

        return {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "error_count": len(errors),
            "errors": errors[:10],
            "created_complaints": created_complaints
        }
