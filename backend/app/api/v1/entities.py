import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.db.database import get_db
from backend.app.db.models import Entity, EntityAddress, Label, LabelSource

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
def list_labels(chain: Optional[str] = None, entity: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Label)
    if chain:
        query = query.filter(Label.chain == chain.lower())
    if entity:
        query = query.filter(Label.entity.ilike(f"%{entity}%"))
    labels = query.order_by(Label.created_at.desc()).limit(200).all()
    return {
        "total": len(labels),
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
def create_label(payload: LabelRequest, db: Session = Depends(get_db)):
    label = Label(
        address=payload.address.strip(),
        chain=payload.chain.lower(),
        entity=payload.entity.strip(),
        category=payload.category,
        source=payload.source,
        confidence=payload.confidence
    )
    db.add(label)
    db.commit()
    db.refresh(label)
    return {"status": "created", "label_id": label.id}

@router.delete("/labels/{id}")
def delete_label(id: int, db: Session = Depends(get_db)):
    label = db.query(Label).filter(Label.id == id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    db.delete(label)
    db.commit()
    return {"status": "deleted", "id": id}

@router.post("/labels/import")
async def import_labels_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    imported = 0
    for row in reader:
        addr = row.get("address", "").strip()
        chain = row.get("chain", "tron").strip().lower()
        entity = row.get("entity", "Unknown").strip()
        category = row.get("category", "VASP").strip()
        source = row.get("source", "CSV Import").strip()
        conf = float(row.get("confidence", 0.9))

        if addr and entity:
            lbl = Label(address=addr, chain=chain, entity=entity, category=category, source=source, confidence=conf)
            db.add(lbl)
            imported += 1

    db.commit()
    return {"status": "success", "imported_count": imported}
