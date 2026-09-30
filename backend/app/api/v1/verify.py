import os
from fastapi import APIRouter, Depends, UploadFile, File, Request, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.evidence import EvidenceService
from app.core.security import rate_limit_public

router = APIRouter(prefix="/verify", tags=["Cryptographic Verification"])

@router.get("/{hash_val}", dependencies=[Depends(rate_limit_public)])
def verify_by_hash(hash_val: str, db: Session = Depends(get_db)):
    result = EvidenceService.verify_hash(db, hash_val)
    return result

@router.post("/upload", dependencies=[Depends(rate_limit_public)])
async def verify_uploaded_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    safe_filename = os.path.basename(file.filename or "uploaded_document.pdf")
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Uploaded file exceeds 15MB limit")
    
    result = EvidenceService.verify_uploaded_pdf(db, content)
    result["filename"] = safe_filename
    return result
