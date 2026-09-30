import os
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.db.models import FreezeRequest, Entity, Case, CaseComplaint, Complaint
from backend.app.core.audit import log_audit_action

class FreezeService:
    @staticmethod
    def create_freeze_request(
        db: Session,
        case_id: int,
        vasp_id: int,
        deposit_address: str,
        suspect_wallet: str,
        legal_order_ref: str,
        notes: str,
        created_by: str = "investigator@demo"
    ) -> FreezeRequest:
        case = db.query(Case).filter(Case.id == case_id).first()
        vasp = db.query(Entity).filter(Entity.id == vasp_id).first()
        vasp_name = vasp.name if vasp else "Target Exchange"

        # Calculate loss from linked complaints
        linked_complaints = db.query(Complaint).join(CaseComplaint, CaseComplaint.complaint_id == Complaint.id).filter(CaseComplaint.case_id == case_id).all()
        loss_inr = sum(c.amount_lost_inr for c in linked_complaints) if linked_complaints else 11200000.0
        loss_usd = sum(c.amount_lost_usd for c in linked_complaints) if linked_complaints else 134500.0

        req_count = db.query(FreezeRequest).count() + 1
        request_number = f"FR-2026-{req_count:04d}"

        fr = FreezeRequest(
            request_number=request_number,
            case_id=case_id,
            vasp_id=vasp_id,
            vasp_name=vasp_name,
            deposit_address=deposit_address,
            suspect_wallet=suspect_wallet,
            victim_loss_inr=loss_inr,
            victim_loss_usd=loss_usd,
            tx_hashes=json.dumps([]),
            status="Draft",
            legal_order_ref=legal_order_ref or "Cr.No 402/2026 U/S 66D IT Act & 420 IPC",
            notes=notes,
            created_by=created_by
        )
        db.add(fr)
        db.commit()
        db.refresh(fr)

        log_audit_action(
            db=db,
            user_email=created_by,
            action="CREATE_FREEZE_REQUEST",
            entity_type="FREEZE_REQUEST",
            entity_id=str(fr.id),
            details={"request_number": request_number, "vasp": vasp_name, "status": "Draft"}
        )
        return fr

    @staticmethod
    def update_freeze_status(
        db: Session,
        request_id: int,
        new_status: str,
        user_email: str,
        frozen_amount_usd: float = 0.0
    ) -> FreezeRequest:
        fr = db.query(FreezeRequest).filter(FreezeRequest.id == request_id).first()
        if not fr:
            raise ValueError(f"Freeze request {request_id} not found")

        valid_transitions = ["Draft", "Pending Approval", "Sent", "Acknowledged", "Frozen", "Rejected"]
        if new_status not in valid_transitions:
            raise ValueError(f"Invalid freeze status: {new_status}")

        fr.status = new_status
        if new_status == "Pending Approval":
            fr.approved_by = None
        elif new_status == "Sent":
            fr.approved_by = user_email
            fr.sent_at = datetime.now(timezone.utc)
        elif new_status == "Acknowledged":
            fr.acknowledged_at = datetime.now(timezone.utc)
        elif new_status == "Frozen":
            fr.frozen_amount_usd = frozen_amount_usd or fr.victim_loss_usd

        db.commit()
        db.refresh(fr)

        log_audit_action(
            db=db,
            user_email=user_email,
            action=f"UPDATE_FREEZE_STATUS_{new_status.upper().replace(' ', '_')}",
            entity_type="FREEZE_REQUEST",
            entity_id=str(fr.id),
            details={"new_status": new_status, "frozen_amount_usd": fr.frozen_amount_usd}
        )
        return fr
