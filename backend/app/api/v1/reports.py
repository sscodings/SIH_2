import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Report, User
from app.services.reports import ReportService
from app.core.security import require_user
from app.core.audit import log_audit_action

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("")
def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    total = db.query(Report).count()
    reports = db.query(Report).order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
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
def generate_report(
    case_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    try:
        report_meta = ReportService.generate_case_report(db, case_id, current_user.email)
        log_audit_action(
            db=db,
            user_email=current_user.email,
            action="GENERATE_REPORT",
            entity_type="REPORT",
            entity_id=str(report_meta.get("report_id", "")),
            details={"case_id": case_id, "report_number": report_meta.get("report_number")}
        )
        return {"status": "success", "report": report_meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/download")
def download_report(
    id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == id).first()
    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="Report record not found")

    # Safe path resolution - prevent directory traversal
    base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports_storage"))
    file_path = os.path.abspath(report.pdf_path)

    # Ensure file_path is strictly within base_dir
    if not file_path.startswith(base_dir) or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report PDF file not found on disk")

    safe_filename = os.path.basename(file_path)
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=safe_filename
    )
