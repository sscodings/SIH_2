import csv
import io
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.db.models import Entity, EntityAddress, Label, LabelSource, User
from app.core.security import require_user, require_role
from app.core.audit import log_audit_action
from app.core.validators import validate_crypto_address

router = APIRouter(prefix="", tags=["Entities & Labels"])

class LabelRequest(BaseModel):
    address: str
    chain: str
    entity: str
    category: str = "VASP"
    source: str = "Internal"
    confidence: float = 0.90

@router.get("/entities/vasps")
def list_vasps(db: Session = Depends(get_db)):
    vasps = db.query(Entity).all()
    results = []
    for v in vasps:
        addrs = db.query(EntityAddress).filter(EntityAddress.entity_id == v.id).all()
        results.append({
            "id": v.id,
            "name": v.name,
            "category": v.category,
            "jurisdiction": v.jurisdiction,
            "compliance_contact": v.compliance_contact,
            "response_sla": v.response_sla,
            "description": v.description,
            "known_addresses": [
                {"address": a.address, "chain": a.chain, "type": a.address_type}
                for a in addrs
            ]
        })
    return {"vasps": results}

@router.get("/labels")
def list_labels(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    chain: Optional[str] = None,
    entity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Label)
    if chain:
        query = query.filter(Label.chain == chain.lower())
    if entity:
        query = query.filter(Label.entity.ilike(f"%{entity}%"))
    
    total = query.count()
    labels = query.order_by(Label.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "labels": [
            {
                "id": l.id,
                "address": l.address,
                "chain": l.chain,
                "entity": l.entity,
                "category": l.category,
                "source": l.source,
                "confidence": l.confidence,
                "created_at": l.created_at.isoformat()
            }
            for l in labels
        ]
    }

@router.post("/labels")
def add_label(
    payload: LabelRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    addr_clean = payload.address.strip()
    chain_clean = payload.chain.lower().strip()

    if not validate_crypto_address(addr_clean, chain_clean):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid address format for chain '{chain_clean}': '{addr_clean}'"
        )

    # Analyst labels start as pending until supervisor or admin approves
    status = "active" if current_user.role in ("admin", "supervisor") else "pending"
    weight_tier = "analyst_approved" if status == "active" else "unverified_official"

    label = Label(
        address=addr_clean,
        chain=chain_clean,
        entity=payload.entity,
        category=payload.category,
        source=payload.source or f"Analyst ({current_user.email})",
        confidence=payload.confidence,
        record_status=status,
        weight_tier=weight_tier,
        wallet_type="unknown"
    )
    db.add(label)
    db.commit()
    db.refresh(label)

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="CREATE_LABEL",
        entity_type="LABEL",
        entity_id=str(label.id),
        details={"address": label.address, "entity": label.entity, "chain": label.chain, "status": status}
    )

    return {"status": "created" if status == "active" else "pending_approval", "id": label.id, "record_status": status}

@router.post("/labels/{label_id}/approve")
def approve_label(
    label_id: int,
    current_user: User = Depends(require_role("supervisor", "admin")),
    db: Session = Depends(get_db)
):
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    label.record_status = "active"
    label.weight_tier = "analyst_approved"
    label.verified_at = datetime.utcnow()
    db.commit()
    db.refresh(label)

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="APPROVE_LABEL",
        entity_type="LABEL",
        entity_id=str(label.id),
        details={"address": label.address, "entity": label.entity, "approved_by": current_user.email}
    )

    return {"status": "approved", "id": label.id, "record_status": "active"}

@router.post("/labels/bulk-import")
async def bulk_import_labels(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files supported for bulk label import")

    content_bytes = await file.read()
    if len(content_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="CSV file size exceeds limit of 5MB")

    content_str = content_bytes.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(content_str))
    count = 0

    for row in reader:
        addr = row.get("address", "").strip()
        chain = row.get("chain", "tron").lower().strip()
        entity = row.get("entity", "").strip()
        category = row.get("category", "VASP").strip()
        confidence = float(row.get("confidence", 0.90))

        if addr and entity and validate_crypto_address(addr, chain):
            l = Label(
                address=addr,
                chain=chain,
                entity=entity,
                category=category,
                source="Bulk Import",
                confidence=confidence
            )
            db.add(l)
            count += 1
            if count >= 2000:
                break
    db.commit()

    log_audit_action(
        db=db,
        user_email=current_user.email,
        action="BULK_IMPORT_LABELS",
        entity_type="LABEL",
        entity_id="BULK",
        details={"imported_count": count}
    )

    return {"status": "imported", "count": count}
