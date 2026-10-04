import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import FreezeRequest, Entity, Case, CaseComplaint, Complaint, CaseTask
from app.core.audit import log_audit_action
from app.legal.provisions import get_citation

ALLOWED_FREEZE_TRANSITIONS = {
    "Draft": {"Pending Approval"},
    "Pending Approval": {"Approved", "Rejected"},
    "Approved": {"Sent"},
    "Sent": {"Acknowledged", "Rejected"},
    "Acknowledged": {"Frozen", "Rejected"},
    "Frozen": set(),
    "Rejected": set()
}

def get_legal_basis_advisory() -> str:
    c_seize = get_citation("seizure_of_property")
    return (
        f"High Courts have taken different views on whether police may debit-freeze under {c_seize['citation']} "
        "without a Magistrate's order; confirm with your legal officer or public prosecutor for your jurisdiction."
    )


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
        legal_order_ref: Optional[str] = None,
        notes: str = "",
        created_by: str = "investigator@demo",
        victim_loss_inr: Optional[float] = None,
        victim_loss_usd: Optional[float] = None,
        fir_number: Optional[str] = None,
        fir_date: Optional[Any] = None,
        police_station: Optional[str] = None,
        district_state: Optional[str] = None,
        offence_sections: Optional[List[str]] = None,
        io_name: Optional[str] = None,
        io_designation: Optional[str] = None,
        io_contact: Optional[str] = None,
        legal_basis: Optional[str] = None,
        court_order_ref: Optional[str] = None,
        court_order_date: Optional[Any] = None,
        freeze_amount: Optional[float] = None,
        traced_tainted_amount: Optional[float] = None,
        supporting_tx_hashes: Optional[List[str]] = None,
        over_limit_justification: Optional[str] = None,
        data_origin: str = "LIVE"
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

        # Watermark determination
        watermark = "DRAFT - NOT FOR DISPATCH"
        if data_origin in ("SYNTHETIC", "DEMO"):
            watermark = "SYNTHETIC / DEMO - NOT FOR LEGAL USE"

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
            legal_order_ref=legal_order_ref,
            fir_number=fir_number,
            fir_date=fir_date,
            police_station=police_station,
            district_state=district_state,
            offence_sections=json.dumps(offence_sections) if offence_sections else None,
            io_name=io_name,
            io_designation=io_designation,
            io_contact=io_contact,
            legal_basis=legal_basis,
            court_order_ref=court_order_ref,
            court_order_date=court_order_date,
            freeze_amount=freeze_amount,
            traced_tainted_amount=float(traced_tainted_amount or loss_usd),
            supporting_tx_hashes=json.dumps(supporting_tx_hashes or []),
            over_limit_justification=over_limit_justification,
            data_origin=data_origin,
            watermark=watermark,
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

        # Transitioning out of Draft -> Validate mandatory statutory fields (E2)
        if current_status == "Draft" and new_status == "Pending Approval":
            missing_fields = []
            required_checks = {
                "fir_number": fr.fir_number,
                "fir_date": fr.fir_date,
                "police_station": fr.police_station,
                "district_state": fr.district_state,
                "offence_sections": fr.offence_sections,
                "io_name": fr.io_name,
                "io_designation": fr.io_designation,
                "io_contact": fr.io_contact,
                "legal_basis": fr.legal_basis,
                "freeze_amount": fr.freeze_amount
            }
            for field_name, field_val in required_checks.items():
                if field_val is None or str(field_val).strip() == "" or field_val == "[]":
                    missing_fields.append(field_name)

            if missing_fields:
                raise FreezeTransitionError(
                    f"Notice cannot leave Draft. Missing required statutory fields: {missing_fields}. "
                    "Draft remains with 'DRAFT - NOT FOR DISPATCH' watermark.",
                    status_code=422
                )

            # Validate legal_basis specifics
            if fr.legal_basis == "bnss_107_attachment":
                if not fr.court_order_ref or not fr.court_order_date:
                    raise FreezeTransitionError(
                        "Legal basis 'bnss_107_attachment' requires court_order_ref and court_order_date.",
                        status_code=422
                    )
            elif fr.legal_basis == "court_order":
                if not fr.court_order_ref:
                    raise FreezeTransitionError(
                        "Legal basis 'court_order' requires court_order_ref.",
                        status_code=422
                    )

            # Proportionality enforcement: freeze_amount <= traced_tainted_amount
            if fr.traced_tainted_amount and fr.freeze_amount and (fr.freeze_amount > fr.traced_tainted_amount):
                if not fr.over_limit_justification or not fr.over_limit_justification.strip():
                    raise FreezeTransitionError(
                        f"Proportionality check failed: freeze_amount (${fr.freeze_amount:,.2f}) exceeds traced tainted amount (${fr.traced_tainted_amount:,.2f}). "
                        "A written over_limit_justification is mandatory before dispatch.",
                        status_code=422
                    )

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

            # VASP Routing nodal contact check
            vasp = db.query(Entity).filter(Entity.id == fr.vasp_id).first() if fr.vasp_id else None
            # Check if nodal contact exists
            has_nodal_contact = False
            if vasp:
                if (vasp.nodal_officer_email and vasp.nodal_officer_email.strip()) or \
                   (vasp.compliance_contact and vasp.compliance_contact.strip()) or \
                   (vasp.nodal_officer_phone and vasp.nodal_officer_phone.strip()):
                    has_nodal_contact = True
            
            if not has_nodal_contact and fr.data_origin == "LIVE":
                raise FreezeTransitionError(
                    "VASP nodal contact not on file - analyst must add before auto-dispatch.",
                    status_code=422
                )

            fr.sent_at = now_utc

            # Reporting reminder: when status becomes Sent under seizure basis, create Magistrate reporting task
            if fr.legal_basis == "bnss_106_seizure":
                existing_task = db.query(CaseTask).filter(
                    CaseTask.case_id == fr.case_id,
                    CaseTask.title == "Report seizure to the jurisdictional Magistrate forthwith"
                ).first()
                if not existing_task:
                    seize_cit = get_citation("seizure_of_property")["citation"]
                    mag_task = CaseTask(
                        case_id=fr.case_id,
                        title="Report seizure to the jurisdictional Magistrate forthwith",
                        description=(
                            f"Debit-freeze seizure executed under {seize_cit} for Freeze Request {fr.request_number}. "
                            "Report seizure to the jurisdictional Magistrate forthwith."
                        ),
                        owner=fr.created_by or effective_email,
                        is_due=True,
                        is_completed=False,
                        magistrate_reference=None
                    )
                    db.add(mag_task)
                    log_audit_action(
                        db=db,
                        user_email=effective_email,
                        action="CREATE_MAGISTRATE_REPORT_TASK",
                        entity_type="CASE_TASK",
                        entity_id=str(fr.case_id),
                        details={
                            "freeze_request_number": fr.request_number,
                            "legal_basis": "bnss_106_seizure",
                            "instruction": "Report seizure to the jurisdictional Magistrate forthwith"
                        }
                    )

        elif new_status == "Acknowledged":
            fr.acknowledged_at = now_utc

        elif new_status == "Frozen":
            if effective_role not in ("supervisor", "admin"):
                raise FreezeTransitionError("Only a Supervisor or Admin can finalize Frozen status", status_code=403)

            amt = frozen_amount_usd if frozen_amount_usd is not None else (fr.victim_loss_usd or fr.freeze_amount or 0.0)
            limit_val = fr.victim_loss_usd if (fr.victim_loss_usd and fr.victim_loss_usd > 0) else (fr.traced_tainted_amount or fr.freeze_amount or 0.0)
            if amt < 0 or (limit_val > 0 and amt > limit_val):
                raise FreezeTransitionError(
                    f"Invalid frozen amount ${amt:,.2f}. Must be > 0 and <= allowed limit of ${limit_val:,.2f}",
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
                "approved_by": fr.approved_by,
                "legal_basis": fr.legal_basis
            }
        )
        return fr
