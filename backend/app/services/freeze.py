import os
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import FreezeRequest, Entity, Case, CaseComplaint, Complaint
from app.core.audit import log_audit_action

ALLOWED_FREEZE_TRANSITIONS = {
    "Draft": {"Pending Approval"},
    "Pending Approval": {"Approved", "Rejected"},
    "Approved": {"Sent"},
    "Sent": {"Acknowledged", "Rejected"},
    "Acknowledged": {"Frozen", "Rejected"},
    "Frozen": set(),
    "Rejected": set()
}

class FreezeTransitionError(Exception):
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code

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
        created_by: str = "investigator@demo",
        victim_loss_inr: Optional[float] = None,
        victim_loss_usd: Optional[float] = None
    ) -> FreezeRequest:
        case = db.query(Case).filter(Case.id == case_id).first()
        vasp = db.query(Entity).filter(Entity.id == vasp_id).first()
        vasp_name = vasp.name if vasp else "Target Exchange"

        # Calculate loss from linked complaints or caller parameters (never hardcode constants)
        linked_complaints = db.query(Complaint).join(CaseComplaint, CaseComplaint.complaint_id == Complaint.id).filter(CaseComplaint.case_id == case_id).all()
        if linked_complaints:
            loss_inr = sum(c.amount_lost_inr for c in linked_complaints)
            loss_usd = sum(c.amount_lost_usd for c in linked_complaints)
        else:
            loss_inr = float(victim_loss_inr or 0.0)
            loss_usd = float(victim_loss_usd or 0.0)

        from app.db.models import get_next_sequence_number
        request_number = get_next_sequence_number(db, "freeze", "FR")

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
        actor_email: Optional[str] = None,
        actor_role: Optional[str] = None,
        user_email: Optional[str] = None,
        frozen_amount_usd: Optional[float] = None
    ) -> FreezeRequest:
        fr = db.query(FreezeRequest).filter(FreezeRequest.id == request_id).first()
        if not fr:
            raise FreezeTransitionError(f"Freeze request {request_id} not found", status_code=404)

        effective_email = actor_email or user_email or "supervisor@demo"
        effective_role = (actor_role or "supervisor").lower()

        current_status = fr.status
        allowed_next = ALLOWED_FREEZE_TRANSITIONS.get(current_status, set())

        # Validate state transition legality
        if new_status not in allowed_next:
            raise FreezeTransitionError(
                f"Illegal state transition from '{current_status}' to '{new_status}'. Allowed: {list(allowed_next)}",
                status_code=409
            )

        now_utc = datetime.now(timezone.utc)

        # Transition-specific validations & separation of duties
        if new_status in ("Approved", "Rejected") and current_status == "Pending Approval":
            # Must be supervisor or admin
            if effective_role not in ("supervisor", "admin"):
                raise FreezeTransitionError("Only a Supervisor or Admin can approve/reject freeze requests", status_code=403)
            # Separation of duties: Approver must NOT be creator
            if fr.created_by and fr.created_by.lower() == effective_email.lower():
                raise FreezeTransitionError("Separation of duties violation: Creator cannot approve or reject their own freeze request", status_code=403)

            if new_status == "Approved":
                fr.approved_by = effective_email
                fr.approved_at = now_utc

        elif new_status == "Sent":
            if effective_role not in ("supervisor", "admin", "system"):
                raise FreezeTransitionError("Only Supervisor/Admin or automated dispatch can mark request as Sent", status_code=403)
            fr.sent_at = now_utc

        elif new_status == "Acknowledged":
            fr.acknowledged_at = now_utc

        elif new_status == "Frozen":
            if effective_role not in ("supervisor", "admin"):
                raise FreezeTransitionError("Only a Supervisor or Admin can finalize Frozen status", status_code=403)

            amt = frozen_amount_usd if frozen_amount_usd is not None else fr.victim_loss_usd
            if amt < 0 or amt > fr.victim_loss_usd:
                raise FreezeTransitionError(
                    f"Invalid frozen amount ${amt:,.2f}. Must be > 0 and <= victim loss of ${fr.victim_loss_usd:,.2f}",
                    status_code=400
                )
            fr.frozen_amount_usd = amt

        old_status = fr.status
        fr.status = new_status
        db.commit()
        db.refresh(fr)

        log_audit_action(
            db=db,
            user_email=effective_email,
            action=f"FREEZE_TRANSITION_{new_status.upper()}",
            entity_type="FREEZE_REQUEST",
            entity_id=str(fr.id),
            details={
                "old_status": old_status,
                "new_status": new_status,
                "frozen_amount_usd": fr.frozen_amount_usd,
                "approved_by": fr.approved_by
            }
        )
        return fr
