"""Evidence verification and chain of custody management."""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

def hash_file(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_bundle(bundle_path: Path) -> Dict[str, Any]:
    """
    Verifies cryptographic integrity of an evidence bundle against its manifest.
    Supports statutory evidence custody requirements for electronic records.
    """
    if not bundle_path.exists():
        return {
            "valid": False,
            "court_ready": False,
            "error": f"Bundle path does not exist: {bundle_path}",
            "mismatches": [],
            "missing_files": []
        }

    manifest_file = bundle_path / "manifest.json" if bundle_path.is_dir() else bundle_path
    if not manifest_file.exists():
        return {
            "valid": False,
            "court_ready": False,
            "error": "manifest.json not found in bundle",
            "mismatches": [],
            "missing_files": []
        }

    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        return {
            "valid": False,
            "court_ready": False,
            "error": f"Failed to parse manifest: {e}",
            "mismatches": [],
            "missing_files": []
        }

    base_dir = manifest_file.parent
    artifacts = manifest.get("artifacts", {})
    mismatches = []
    missing_files = []
    verified_files = []

    for rel_name, meta in artifacts.items():
        art_path = base_dir / rel_name
        if not art_path.exists():
            missing_files.append(rel_name)
            continue

        expected_hash = meta.get("sha256", "").lower()
        actual_hash = hash_file(art_path).lower()

        if expected_hash != actual_hash:
            mismatches.append({
                "file": rel_name,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash
            })
        else:
            verified_files.append(rel_name)

    is_valid = len(mismatches) == 0 and len(missing_files) == 0 and len(artifacts) > 0
    court_ready = is_valid

    return {
        "valid": is_valid,
        "court_ready": court_ready,
        "bundle_id": manifest.get("bundle_id"),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "total_artifacts": len(artifacts),
        "verified_count": len(verified_files),
        "mismatches": mismatches,
        "missing_files": missing_files,
        "status": "COURT_READY" if court_ready else "NOT COURT-READY"
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.evidence.verify <bundle_dir_or_manifest>")
        sys.exit(1)

    target = Path(sys.argv[1])
    res = verify_bundle(target)
    print(json.dumps(res, indent=2))
    if not res.get("court_ready", False):
        sys.exit(1)
    sys.exit(0)
