import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Report
from backend.app.services.reports import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("")
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return {
        "reports": [
            {
                "id": r.id,
                "case_id": r.case_id,
                "report_number": r.report_number,
                "sha256_hash": r.sha256_hash,
                "snapshot_sha256": r.snapshot_sha256,
                "generated_by": r.generated_by,
                "created_at": r.created_at.isoformat()
            }
            for r in reports
        ]
    }

@router.post("/{case_id}")
def generate_report(case_id: int, user_email: str = "investigator@demo", db: Session = Depends(get_db)):
    try:
        report_meta = ReportService.generate_case_report(db, case_id, user_email)
        return {"status": "success", "report": report_meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/download")
def download_report(id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == id).first()
    if not report or not os.path.exists(report.pdf_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(
        report.pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(report.pdf_path)
    )
