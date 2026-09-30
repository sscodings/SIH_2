import json
import random
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.db.database import get_db
from backend.app.db.models import Complaint
from backend.app.services.ingest import IngestionService
from backend.app.core.ws import ws_manager
from backend.app.core.config import settings

router = APIRouter(prefix="", tags=["Complaints"])

class IngestRequest(BaseModel):
    victim_name: str
    victim_state: str = "Maharashtra"
    fraud_type: str = "Investment Scam"
    reported_wallets: List[str]
    amount_lost_inr: float
    complaint_number: Optional[str] = None

@router.get("/complaints")
def list_complaints(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    chain: Optional[str] = None,
    fraud_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == status)
    if chain:
        query = query.filter(Complaint.chain == chain)
    if fraud_type:
        query = query.filter(Complaint.fraud_type == fraud_type)

    total = query.count()
    items = query.order_by(Complaint.reported_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "complaint_number": c.complaint_number,
                "source": c.source,
                "victim_name": c.victim_name,
                "victim_state": c.victim_state,
                "fraud_type": c.fraud_type,
                "reported_wallets": json.loads(c.reported_wallets or "[]"),
                "chain": c.chain,
                "amount_lost_inr": c.amount_lost_inr,
                "amount_lost_usd": c.amount_lost_usd,
                "reported_at": c.reported_at.isoformat(),
                "status": c.status,
                "priority": c.priority
            }
            for c in items
        ]
    }

@router.get("/complaints/{id}")
def get_complaint(id: int, db: Session = Depends(get_db)):
    c = db.query(Complaint).filter(Complaint.id == id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {
        "id": c.id,
        "complaint_number": c.complaint_number,
        "source": c.source,
        "victim_name": c.victim_name,
        "victim_state": c.victim_state,
        "fraud_type": c.fraud_type,
        "reported_wallets": json.loads(c.reported_wallets or "[]"),
        "chain": c.chain,
        "amount_lost_inr": c.amount_lost_inr,
        "amount_lost_usd": c.amount_lost_usd,
        "reported_at": c.reported_at.isoformat(),
        "status": c.status,
        "priority": c.priority
    }

@router.post("/ingest/ncrp")
async def ingest_ncrp(payload: IngestRequest, db: Session = Depends(get_db)):
    complaint = IngestionService.ingest_single_complaint(
        db=db,
        victim_name=payload.victim_name,
        victim_state=payload.victim_state,
        fraud_type=payload.fraud_type,
        reported_wallets=payload.reported_wallets,
        amount_lost_inr=payload.amount_lost_inr,
        source="NCRP",
        complaint_number=payload.complaint_number
    )
    # Broadcast to WebSocket
    await ws_manager.broadcast_event(
        "inbox",
        "new_complaint",
        {
            "id": complaint.id,
            "complaint_number": complaint.complaint_number,
            "source": "NCRP",
            "victim_name": complaint.victim_name,
            "amount_lost_inr": complaint.amount_lost_inr,
            "chain": complaint.chain
        }
    )
    return {"status": "success", "complaint_id": complaint.id, "complaint_number": complaint.complaint_number}

@router.post("/ingest/sahyog")
async def ingest_sahyog(payload: IngestRequest, db: Session = Depends(get_db)):
    complaint = IngestionService.ingest_single_complaint(
        db=db,
        victim_name=payload.victim_name,
        victim_state=payload.victim_state,
        fraud_type=payload.fraud_type,
        reported_wallets=payload.reported_wallets,
        amount_lost_inr=payload.amount_lost_inr,
        source="SAHYOG",
        complaint_number=payload.complaint_number
    )
    await ws_manager.broadcast_event(
        "inbox",
        "new_complaint",
        {
            "id": complaint.id,
            "complaint_number": complaint.complaint_number,
            "source": "SAHYOG",
            "victim_name": complaint.victim_name,
            "amount_lost_inr": complaint.amount_lost_inr,
            "chain": complaint.chain
        }
    )
    return {"status": "success", "complaint_id": complaint.id, "complaint_number": complaint.complaint_number}

@router.post("/ingest/csv")
async def ingest_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8")
    result = IngestionService.process_csv_upload(db, text)
    return result

@router.post("/complaints/simulate")
async def simulate_complaint(db: Session = Depends(get_db)):
    """
    Simulates a live incoming cybercrime fraud complaint from NCRP / SAHYOG feed.
    """
    states = ["Maharashtra", "Karnataka", "Delhi", "Gujarat", "Telangana", "Uttar Pradesh", "West Bengal", "Punjab"]
    fraud_types = ["Investment Scam", "Task-Based Fraud", "Sextortion", "Phishing Drainer", "Fake Trading App"]
    chains = ["tron", "ethereum", "bsc", "bitcoin"]

    chain = random.choice(chains)
    mock_addr = (
        f"T{random.randint(1000000000, 9999999999)}SimTronAddr" if chain == "tron"
        else (f"0x{random.randint(1000000000, 9999999999):x}abcdef40hexevm" if chain in ["ethereum", "bsc"]
        else f"bc1q{random.randint(1000000000, 9999999999)}simbtcaddr")
    )
    inr_amt = random.randint(250000, 3500000)

    cmp = IngestionService.ingest_single_complaint(
        db=db,
        victim_name=f"Simulated Citizen ({random.choice(['Tech Worker', 'Doctor', 'Retired Officer', 'Student', 'Merchant'])})",
        victim_state=random.choice(states),
        fraud_type=random.choice(fraud_types),
        reported_wallets=[mock_addr],
        amount_lost_inr=inr_amt,
        source=random.choice(["NCRP", "SAHYOG"])
    )

    data = {
        "id": cmp.id,
        "complaint_number": cmp.complaint_number,
        "source": cmp.source,
        "victim_name": cmp.victim_name,
        "amount_lost_inr": cmp.amount_lost_inr,
        "amount_lost_usd": cmp.amount_lost_usd,
        "chain": cmp.chain,
        "reported_at": cmp.reported_at.isoformat(),
        "priority": cmp.priority,
        "fraud_type": cmp.fraud_type
    }

    await ws_manager.broadcast_event("inbox", "new_complaint", data)

    return {"status": "simulated", "complaint": data}

@router.post("/complaints/validate-address")
def validate_address(payload: dict):
    addr = payload.get("address", "")
    return IngestionService.detect_chain_and_validate(addr)
