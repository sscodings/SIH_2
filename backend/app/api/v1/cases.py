import json
import uuid
import asyncio
import random
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import (
    Case, CaseComplaint, Complaint, TraceJob, TraceSnapshot,
    Attribution, FundsStatus, GraphNode, GraphEdge, CaseNote, Cluster, ClusterMember, User,
    get_next_sequence_number
)
from app.engines.tracer import TracingEngine
from app.engines.recommend import RecommendationEngine
from app.engines.risk import RiskEngine
from app.engines.typology import TypologyEngine
from app.core.audit import log_audit_action
from app.core.security import require_user
from app.core.validators import validate_crypto_address
from app.services.queue import enqueue_trace_job

router = APIRouter(prefix="/cases", tags=["Cases & Tracing"])

# Active background trace cancellation tokens: job_id -> {"cancelled": bool}
active_trace_jobs: Dict[str, dict] = {}

class CreateCaseRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    primary_chain: str = "tron"
    primary_address: str
    complaint_ids: Optional[List[int]] = []
    priority: str = "High"

class TraceRequest(BaseModel):
    initial_amount_usd: Optional[float] = None
    max_depth: int = 6
    min_value_usd: float = 50.0
    max_nodes: int = 400
    time_window_hours: int = 72
    taint_model: str = "haircut"  # haircut, fifo, poison
    stop_at_first_vasp: bool = True

class NoteRequest(BaseModel):
    content: str

class MergeCaseRequest(BaseModel):
    case_ids: List[int]
    syndicate_title: str

@router.get("")
def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    chain: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    if chain:
        query = query.filter(Case.primary_chain == chain)
    if priority:
        query = query.filter(Case.priority == priority)

    total = query.count()
    items = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "case_number": c.case_number,
                "title": c.title,
                "description": c.description,
                "primary_chain": c.primary_chain,
                "primary_address": c.primary_address,
                "status": c.status,
                "priority": c.priority,
                "time_to_vasp_seconds": c.time_to_vasp_seconds,
                "created_by": c.created_by,
                "created_at": c.created_at.isoformat()
            }
            for c in items
        ]
    }

@router.post("")
def create_case(
    payload: CreateCaseRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    # Validate crypto address
    if not validate_crypto_address(payload.primary_address, payload.primary_chain):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid crypto address format for chain '{payload.primary_chain}': '{payload.primary_address}'"
        )

    case_number = get_next_sequence_number(db, "case", "CASE")

    case = Case(
        case_number=case_number,
        title=payload.title,
        description=payload.description or "",
        primary_chain=payload.primary_chain.lower(),
        primary_address=payload.primary_address.strip(),
        status="Active",
        priority=payload.priority,
        created_by=current_user.email
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    # Link complaints if provided
    for cmp_id in payload.complaint_ids:
        db.add(CaseComplaint(case_id=case.id, complaint_id=cmp_id))
    db.commit()

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="CREATE_CASE",
        entity_type="CASE",
        entity_id=str(case.id),
        details={"case_number": case.case_number, "address": case.primary_address}
    )

    return {"status": "created", "case_id": case.id, "case_number": case.case_number}

@router.get("/{id}")
def get_case(id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    complaints = db.query(Complaint).join(CaseComplaint, CaseComplaint.complaint_id == Complaint.id).filter(CaseComplaint.case_id == id).all()
    notes = db.query(CaseNote).filter(CaseNote.case_id == id).order_by(CaseNote.created_at.desc()).all()
    attribution = db.query(Attribution).filter(Attribution.case_id == id).first()
    funds = db.query(FundsStatus).filter(FundsStatus.case_id == id).first()

    return {
        "id": case.id,
        "case_number": case.case_number,
        "title": case.title,
        "description": case.description,
        "primary_chain": case.primary_chain,
        "primary_address": case.primary_address,
        "status": case.status,
        "priority": case.priority,
        "time_to_vasp_seconds": case.time_to_vasp_seconds,
        "created_by": case.created_by,
        "created_at": case.created_at.isoformat(),
        "complaints": [
            {
                "id": c.id,
                "complaint_number": c.complaint_number,
                "victim_name": c.victim_name,
                "amount_lost_inr": c.amount_lost_inr,
                "amount_lost_usd": c.amount_lost_usd,
                "fraud_type": c.fraud_type
            }
            for c in complaints
        ],
        "notes": [
            {
                "id": n.id,
                "author": n.author_email,
                "content": n.content,
                "created_at": n.created_at.isoformat()
            }
            for n in notes
        ],
        "attribution": {
            "vasp_name": attribution.vasp_name,
            "category": attribution.vasp_category,
            "deposit_address": attribution.deposit_address,
            "amount": attribution.amount,
            "hops": attribution.hops_from_suspect,
            "confidence": attribution.confidence_score,
            "evidence": json.loads(attribution.evidence_breakdown or "{}")
        } if attribution else None,
        "funds_status": {
            "total_traced_usd": funds.total_traced_usd,
            "vasp_amount_usd": funds.vasp_amount_usd,
            "mixer_amount_usd": funds.mixer_amount_usd,
            "dormant_amount_usd": funds.dormant_amount_usd,
            "unaccounted_usd": funds.unaccounted_usd
        } if funds else None
    }

async def run_trace_task(case_id: int, job_id: str, params: dict, actor_email: str):
    from app.db.database import SessionLocal
    db: Session = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return

        # Calculate initial trace amount from linked complaints or caller param
        linked_complaints = db.query(Complaint).join(CaseComplaint, CaseComplaint.complaint_id == Complaint.id).filter(CaseComplaint.case_id == case_id).all()
        if linked_complaints:
            initial_amt = sum(c.amount_lost_usd for c in linked_complaints)
        else:
            initial_amt = float(params.get("initial_amount_usd") or 1000.0)

        tracer = TracingEngine(
            db=db,
            case_id=case_id,
            start_address=case.primary_address,
            chain=case.primary_chain,
            initial_amount_usd=initial_amt,
            max_depth=params.get("max_depth", 6),
            min_value_usd=params.get("min_value_usd", 50.0),
            max_nodes=params.get("max_nodes", 400),
            time_window_hours=params.get("time_window_hours", 72),
            taint_model=params.get("taint_model", "haircut"),
            stop_at_first_vasp=params.get("stop_at_first_vasp", True)
        )

        cancel_token = active_trace_jobs.get(job_id, {"cancelled": False})
        result = await tracer.execute_trace(job_id=job_id, cancel_token=cancel_token)

        # Save result to DB
        job_rec = db.query(TraceJob).filter(TraceJob.id == job_id).first()
        if job_rec:
            job_rec.status = "completed" if not cancel_token.get("cancelled") else "cancelled"
            job_rec.completed_at = datetime.now(timezone.utc)
            job_rec.elapsed_seconds = result["elapsed_seconds"]

        # Update case time_to_vasp_seconds
        if result["time_to_vasp_seconds"]:
            case.time_to_vasp_seconds = result["time_to_vasp_seconds"]

        # Save Attributions
        if result["attributions"]:
            first_attr = result["attributions"][0]
            existing_attr = db.query(Attribution).filter(Attribution.case_id == case_id).first()
            if not existing_attr:
                existing_attr = Attribution(case_id=case_id)
                db.add(existing_attr)
            existing_attr.vasp_name = first_attr["vasp_name"]
            existing_attr.vasp_category = first_attr["vasp_category"]
            existing_attr.deposit_address = first_attr["deposit_address"]
            existing_attr.tx_hash = first_attr["tx_hash"]
            existing_attr.amount = first_attr["amount"]
            existing_attr.timestamp = datetime.fromisoformat(first_attr["timestamp"])
            existing_attr.hops_from_suspect = first_attr["hops_from_suspect"]
            existing_attr.confidence_score = first_attr["confidence_score"]
            existing_attr.evidence_breakdown = json.dumps(first_attr["evidence_breakdown"])

        # Save Funds Status
        fs = db.query(FundsStatus).filter(FundsStatus.case_id == case_id).first()
        if not fs:
            fs = FundsStatus(case_id=case_id)
            db.add(fs)
        f_data = result["funds_status"]
        fs.total_traced_usd = f_data["total_traced_usd"]
        fs.vasp_amount_usd = f_data["vasp_amount_usd"]
        fs.mixer_amount_usd = f_data["mixer_amount_usd"]
        fs.dormant_amount_usd = f_data["dormant_amount_usd"]
        fs.unaccounted_usd = f_data["unaccounted_usd"]

        # Save Canonical Snapshot
        import hashlib
        snapshot_json = json.dumps(result, sort_keys=True)
        s_hash = hashlib.sha256(snapshot_json.encode('utf-8')).hexdigest()
        db.add(TraceSnapshot(case_id=case_id, snapshot_json=snapshot_json, sha256_hash=s_hash))

        db.commit()

        log_audit_action(
            db=db,
            user_email=actor_email,
            action="EXECUTE_TRACE",
            entity_type="CASE",
            entity_id=str(case_id),
            details={
                "job_id": job_id,
                "nodes": len(result["nodes"]),
                "edges": len(result["edges"]),
                "vasps_found": len(result["attributions"])
            }
        )

    finally:
        active_trace_jobs.pop(job_id, None)
        db.close()

@router.post("/{id}/trace")
async def start_trace(
    id: int,
    payload: TraceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    job_id = f"job-{uuid.uuid4().hex[:12]}"
    active_trace_jobs[job_id] = {"cancelled": False}

    trace_job = TraceJob(
        id=job_id,
        case_id=id,
        status="queued",
        params=json.dumps(payload.dict()),
        started_at=datetime.now(timezone.utc)
    )
    db.add(trace_job)
    db.commit()

    await enqueue_trace_job(id, job_id, payload.dict(), current_user.email, background_tasks, db=db)

    return {
        "status": "started",
        "job_id": job_id,
        "case_id": id,
        "ws_topic": f"trace:{id}"
    }

@router.delete("/{id}/trace/{job_id}")
def cancel_trace(
    id: int,
    job_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    if job_id in active_trace_jobs:
        active_trace_jobs[job_id]["cancelled"] = True
    job_rec = db.query(TraceJob).filter(TraceJob.id == job_id).first()
    if job_rec:
        job_rec.cancelled = True
        job_rec.status = "cancelled"
        db.commit()

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="CANCEL_TRACE",
        entity_type="CASE",
        entity_id=str(id),
        details={"job_id": job_id}
    )
    return {"status": "cancelled", "job_id": job_id}

@router.get("/{id}/graph")
def get_case_graph(id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    snapshot = db.query(TraceSnapshot).filter(TraceSnapshot.case_id == id).order_by(TraceSnapshot.id.desc()).first()
    if snapshot:
        data = json.loads(snapshot.snapshot_json)
        return {
            "case_id": id,
            "nodes": data.get("nodes", []),
            "edges": data.get("edges", []),
            "attributions": data.get("attributions", []),
            "funds_status": data.get("funds_status", {})
        }

    # If no snapshot yet, return initial root node with value from linked complaints
    linked_complaints = db.query(Complaint).join(CaseComplaint, CaseComplaint.complaint_id == Complaint.id).filter(CaseComplaint.case_id == id).all()
    loss_val = sum(c.amount_lost_usd for c in linked_complaints) if linked_complaints else 0.0

    root_node = {
        "id": case.primary_address.lower(),
        "address": case.primary_address,
        "chain": case.primary_chain,
        "entity_type": "Suspect/Collector",
        "label": f"Root Suspect ({case.primary_address[:8]}...)",
        "risk_level": "High",
        "value_usd": loss_val,
        "depth": 0
    }
    return {
        "case_id": id,
        "nodes": [root_node],
        "edges": [],
        "attributions": [],
        "funds_status": {}
    }

@router.get("/{id}/attribution")
def get_case_attribution(id: int, db: Session = Depends(get_db)):
    attr = db.query(Attribution).filter(Attribution.case_id == id).first()
    if not attr:
        return {"attributed": False, "message": "No VASP attribution recorded yet. Run trace to identify deposit destination."}
    return {
        "attributed": True,
        "vasp_name": attr.vasp_name,
        "category": attr.vasp_category,
        "deposit_address": attr.deposit_address,
        "tx_hash": attr.tx_hash,
        "amount": attr.amount,
        "hops": attr.hops_from_suspect,
        "confidence_score": attr.confidence_score,
        "evidence_breakdown": json.loads(attr.evidence_breakdown or "{}")
    }

@router.get("/{id}/recommendations")
def get_case_recommendations(id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    snapshot = db.query(TraceSnapshot).filter(TraceSnapshot.case_id == id).order_by(TraceSnapshot.id.desc()).first()
    if snapshot:
        data = json.loads(snapshot.snapshot_json)
        recs = RecommendationEngine.generate_recommendations(
            attributions=data.get("attributions", []),
            dormant_wallets=data.get("dormant_wallets", []),
            mixer_events=data.get("mixer_events", []),
            cross_chain_events=data.get("cross_chain_events", []),
            complaint_matches=[]
        )
        return {"case_id": id, "recommendations": recs}

    return {"case_id": id, "recommendations": []}

@router.get("/{id}/timeline")
def get_case_timeline(id: int, db: Session = Depends(get_db)):
    snapshot = db.query(TraceSnapshot).filter(TraceSnapshot.case_id == id).order_by(TraceSnapshot.id.desc()).first()
    if not snapshot:
        return {"timeline": []}
    data = json.loads(snapshot.snapshot_json)
    edges = data.get("edges", [])
    sorted_edges = sorted(edges, key=lambda x: x.get("timestamp", ""))
    return {"timeline": sorted_edges}

@router.post("/{id}/notes")
def add_case_note(
    id: int,
    payload: NoteRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    note = CaseNote(
        case_id=id,
        author_email=current_user.email,
        content=payload.content,
        created_at=datetime.now(timezone.utc)
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"status": "added", "note_id": note.id}

@router.post("/merge")
def merge_cases_into_syndicate(
    payload: MergeCaseRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Merges multiple complaints / cases into a unified Syndicate Case
    """
    syndicate = Case(
        case_number=f"SYND-2026-{random.randint(100,999)}",
        title=payload.syndicate_title,
        description=f"Syndicate case consolidated from cases: {payload.case_ids}",
        primary_chain="tron",
        primary_address="TSyndicateCoreCollectorNexus77777",
        status="Active",
        priority="Critical",
        created_by=current_user.email
    )
    db.add(syndicate)
    db.commit()
    db.refresh(syndicate)

    # Link complaints from all merged cases
    for cid in payload.case_ids:
        links = db.query(CaseComplaint).filter(CaseComplaint.case_id == cid).all()
        for l in links:
            db.add(CaseComplaint(case_id=syndicate.id, complaint_id=l.complaint_id))
    db.commit()

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="MERGE_SYNDICATE_CASE",
        entity_type="CASE",
        entity_id=str(syndicate.id),
        details={"merged_cases": payload.case_ids, "syndicate_number": syndicate.case_number}
    )

    return {"status": "merged", "syndicate_case_id": syndicate.id, "case_number": syndicate.case_number}
