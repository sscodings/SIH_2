import hashlib
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.db.models import Report, TraceSnapshot, Case

class EvidenceService:
    @staticmethod
    def verify_hash(db: Session, target_hash: str) -> Dict[str, Any]:
        target_hash = target_hash.strip().lower()

        # Check Report PDF hash or snapshot hash
        report = db.query(Report).filter(
            (Report.sha256_hash.ilike(target_hash)) | (Report.snapshot_sha256.ilike(target_hash))
        ).first()

        if report:
            case = db.query(Case).filter(Case.id == report.case_id).first()
            return {
                "status": "Authentic",
                "verified": True,
                "type": "Investigation Report",
                "report_number": report.report_number,
                "case_number": case.case_number if case else "Unknown",
                "case_title": case.title if case else "N/A",
                "generated_by": report.generated_by,
                "generated_at": report.created_at.isoformat(),
                "snapshot_sha256": report.snapshot_sha256,
                "pdf_sha256": report.sha256_hash,
                "message": "Cryptographic integrity verified. Digital evidence matches authentic law-enforcement records."
            }

        # Check Snapshot hash directly
        snapshot = db.query(TraceSnapshot).filter(TraceSnapshot.sha256_hash.ilike(target_hash)).first()
        if snapshot:
            case = db.query(Case).filter(Case.id == snapshot.case_id).first()
            return {
                "status": "Authentic",
                "verified": True,
                "type": "Trace Snapshot",
                "case_number": case.case_number if case else "Unknown",
                "case_title": case.title if case else "N/A",
                "generated_at": snapshot.created_at.isoformat(),
                "snapshot_sha256": snapshot.sha256_hash,
                "message": "Trace ledger snapshot hash verified authentic."
            }

        # Check if hash looks like a valid sha256 but is tampered
        if len(target_hash) == 64 and all(c in "0123456789abcdef" for c in target_hash):
            return {
                "status": "Tampered / Unrecognized",
                "verified": False,
                "message": "Hash does not match any sealed digital evidence in the ChainNetra ledger. Potential tampering or unregistered file."
            }

        return {
            "status": "Invalid",
            "verified": False,
            "message": "Supplied input is not a valid 64-character SHA-256 hash."
        }

    @staticmethod
    def verify_uploaded_pdf(db: Session, file_bytes: bytes) -> Dict[str, Any]:
        uploaded_hash = hashlib.sha256(file_bytes).hexdigest()
        result = EvidenceService.verify_hash(db, uploaded_hash)
        result["computed_sha256"] = uploaded_hash
        return result
