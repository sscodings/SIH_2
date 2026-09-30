from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.services.evidence import EvidenceService

router = APIRouter(prefix="/verify", tags=["Cryptographic Verification"])

@router.get("/{hash_val}")
def verify_by_hash(hash_val: str, db: Session = Depends(get_db)):
    result = EvidenceService.verify_hash(db, hash_val)
    return result

@router.post("/upload")
async def verify_uploaded_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    result = EvidenceService.verify_uploaded_pdf(db, content)
    result["filename"] = file.filename
    return result
