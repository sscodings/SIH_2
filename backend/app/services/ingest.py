import re
import json
import csv
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Complaint, Case, CaseComplaint
from app.core.config import settings
from app.core.validators import validate_crypto_address, verify_tron_address, verify_bitcoin_address, verify_evm_address

MAX_CSV_ROWS = 5000
MAX_CSV_BYTES = 5 * 1024 * 1024  # 5MB

class IngestionValidationError(Exception):
    pass

class IngestionService:
    @staticmethod
    def detect_chain_and_validate(address: str) -> Dict[str, Any]:
        address = address.strip()
        if verify_tron_address(address):
            return {"valid": True, "chain": "tron", "standard": "TRC-20 / Base58Check", "address": address}
        if verify_bitcoin_address(address):
            return {"valid": True, "chain": "bitcoin", "standard": "Bitcoin (Base58Check / Bech32)", "address": address}
        if verify_evm_address(address):
            return {"valid": True, "chain": "ethereum", "supported_evm_chains": ["ethereum", "bsc", "polygon", "arbitrum"], "standard": "EVM (EIP-55 Checksum)", "address": address}
        
        return {"valid": False, "chain": "unknown", "error": "Address does not conform to Tron (Base58Check), Bitcoin (Bech32/Base58Check), or EVM formats", "address": address}

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
        if not reported_wallets:
            raise IngestionValidationError("At least one reported wallet address is required")

        # Validate addresses
        for w in reported_wallets:
            det = IngestionService.detect_chain_and_validate(w)
            if not det["valid"]:
                raise IngestionValidationError(f"Invalid cryptocurrency address '{w}': {det.get('error')}")

        if not complaint_number:
            from app.db.models import get_next_sequence_number
            complaint_number = get_next_sequence_number(db, "complaint", source)

        detection = IngestionService.detect_chain_and_validate(reported_wallets[0])
        chain = detection.get("chain", "tron")

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
            source_system=source,
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
        db.flush()

        from app.db.models import ComplaintWallet
        from app.core.addresses import normalize
        for w in reported_wallets:
            cw = ComplaintWallet(
                complaint_id=complaint.id,
                chain=chain,
                normalized_address=normalize(chain, w),
                is_primary=True,
                created_at=datetime.utcnow()
            )
            db.add(cw)

        db.commit()
        db.refresh(complaint)
        return complaint

    @staticmethod
    def process_csv_upload(db: Session, file_content: str) -> Dict[str, Any]:
        if len(file_content.encode('utf-8')) > MAX_CSV_BYTES:
            raise IngestionValidationError("CSV file exceeds maximum allowed size of 5MB")

        reader = csv.DictReader(io.StringIO(file_content))
        total_rows = 0
        valid_rows = 0
        errors = []
        created_complaints = []

        for idx, row in enumerate(reader, start=1):
            total_rows += 1
            if total_rows > MAX_CSV_ROWS:
                errors.append(f"CSV exceeded maximum limit of {MAX_CSV_ROWS} rows. Remaining rows ignored.")
                break

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
                amt = float(amount_str) if amount_str else 0.0
            except ValueError:
                amt = 0.0

            victim = row.get("victim_name", f"Victim #{idx}").strip()
            state = row.get("victim_state", "Maharashtra").strip()
            fraud = row.get("fraud_type", "Investment Scam").strip()
            src = row.get("source", "Bulk CSV").strip()

            c = IngestionService.ingest_single_complaint(
                db=db,
                victim_name=victim,
                victim_state=state,
                fraud_type=fraud,
                reported_wallets=[wallet],
                amount_lost_inr=amt,
                source=src
            )
            created_complaints.append(c.complaint_number)
            valid_rows += 1

        return {
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "created_count": len(created_complaints),
            "errors": errors[:20],
            "complaint_numbers": created_complaints[:10]
        }
