import os
import shutil
import csv
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.complaint_source import ComplaintIngestionPipeline

logger = logging.getLogger("chainnetra.services.file_drop")

def get_drop_directory(custom_path: Optional[str] = None) -> str:
    if custom_path:
        base = custom_path
    else:
        # Default to data/drop relative to project root or backend
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "drop"))
    return base

def ensure_drop_folders(drop_dir: str):
    os.makedirs(drop_dir, exist_ok=True)
    os.makedirs(os.path.join(drop_dir, "processed"), exist_ok=True)
    os.makedirs(os.path.join(drop_dir, "failed"), exist_ok=True)

def scan_and_process_drop_dir(db: Session, drop_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Scans the drop folder for inbound CSV complaint files.
    Processes each file through the ComplaintIngestionPipeline.
    Moves successfully processed files to processed/, failed to failed/ with .err sidecar.
    """
    target_dir = get_drop_directory(drop_dir)
    ensure_drop_folders(target_dir)

    processed_dir = os.path.join(target_dir, "processed")
    failed_dir = os.path.join(target_dir, "failed")

    summary = {
        "files_processed": [],
        "files_failed": [],
        "total_records": 0,
        "total_accepted": 0,
        "total_duplicate": 0,
        "total_rejected": 0
    }

    # Only look at top-level files in target_dir
    try:
        entries = os.listdir(target_dir)
    except Exception as e:
        logger.error(f"Cannot list drop directory '{target_dir}': {e}")
        return summary

    for filename in entries:
        file_path = os.path.join(target_dir, filename)
        if not os.path.isfile(file_path):
            continue
        if not filename.lower().endswith(".csv"):
            continue

        file_accepted = 0
        file_duplicate = 0
        file_rejected = 0
        file_errors = []

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                raise ValueError("CSV file is empty or missing headers")

            for idx, row in enumerate(rows):
                res = ComplaintIngestionPipeline.process_record(db, row, source_system="FILE_DROP")
                status = res.get("status")
                if status == "accepted":
                    file_accepted += 1
                elif status == "duplicate":
                    file_duplicate += 1
                elif status == "rejected":
                    file_rejected += 1
                    file_errors.append(f"Row {idx+1}: {res.get('error')}")

            # Destination
            dest_path = os.path.join(processed_dir, filename)
            # If already exists in processed, overwrite or timestamp
            if os.path.exists(dest_path):
                os.remove(dest_path)
            shutil.move(file_path, dest_path)

            summary["files_processed"].append({
                "filename": filename,
                "accepted": file_accepted,
                "duplicate": file_duplicate,
                "rejected": file_rejected
            })
            summary["total_records"] += len(rows)
            summary["total_accepted"] += file_accepted
            summary["total_duplicate"] += file_duplicate
            summary["total_rejected"] += file_rejected

        except Exception as exc:
            logger.error(f"Failed processing drop file '{filename}': {exc}")
            dest_path = os.path.join(failed_dir, filename)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            shutil.move(file_path, dest_path)

            err_path = os.path.join(failed_dir, f"{filename}.err")
            with open(err_path, "w", encoding="utf-8") as ef:
                ef.write(f"Error: {str(exc)}\n")
                if file_errors:
                    ef.write("\nRow errors:\n" + "\n".join(file_errors))

            summary["files_failed"].append({
                "filename": filename,
                "error": str(exc)
            })

    return summary
