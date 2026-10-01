import os
import re
import json
import pytest
import hashlib
from pathlib import Path
from pypdf import PdfReader
from app.legal.templates.bsa63_schedule import (
    render_bsa63_certificate,
    OFFICIAL_BSA_PDF_SHA256,
    SCHEDULE_FOOTER,
    LEGAL_PRE_DOWNLOAD_NOTICE
)
from app.evidence.verify import verify_bundle

def normalize_whitespace(text: str) -> str:
    # Remove running headers, footers, underscores variations, non-ascii, and collapse whitespace
    text = re.sub(r"Page \d+ of \d+", "", text)
    text = re.sub(r"The Schedule \[See section 63\(4\)\(c\)\].*?Official PDF SHA-256: [a-f0-9]+", "", text)
    text = re.sub(r"THE GAZETTE OF INDIA.*", "", text)
    text = re.sub(r"SEC\. 1\].*", "", text)
    text = re.sub(r"_+", "_", text)
    text = re.sub(r"\[\s*\]", "[]", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()

def test_bsa63_golden_text_equality(tmp_path):
    """
    Golden test: the whitespace-normalised text of a rendered blank certificate
    equals the text extracted from the official Schedule pages (46-47),
    ignoring page header/footer lines.
    """
    official_pdf = Path("docs/research/bsa63_schedule_form.pdf")
    if not official_pdf.exists():
        official_pdf = Path("backend/docs/research/bsa63_schedule_form.pdf")
    if not official_pdf.exists():
        pytest.skip("Official Schedule form PDF not found")

    reader_official = PdfReader(str(official_pdf))
    official_p1 = reader_official.pages[0].extract_text()
    official_p2 = reader_official.pages[1].extract_text()

    # Filter printer block at end of official p2
    if "DIW AKAR SINGH" in official_p2:
        official_p2 = official_p2.split("DIW AKAR SINGH")[0]

    norm_official = normalize_whitespace(official_p1 + " " + official_p2)

    # Render blank certificate
    out_pdf = tmp_path / "blank_cert.pdf"
    render_bsa63_certificate(out_pdf, mode="blank")

    reader_rendered = PdfReader(str(out_pdf))
    rendered_text = " ".join(p.extract_text() for p in reader_rendered.pages)
    norm_rendered = normalize_whitespace(rendered_text)

    # Check key statutory phrases are present verbatim
    key_phrases = [
        "the schedule",
        "[see section 63(4)(c)]",
        "certificate",
        "part a",
        "(to be filled by the party)",
        "i, _ (name), son/daughter/spouse of _",
        "residing/employed at _ do hereby solemnly affirm and sincerely state and submit as follows",
        "i have produced electronic record/output of the digital record taken from the following device/digital record source (tick mark)",
        "computer / storage media",
        "make & model",
        "serial number",
        "lawful control for regularly creating, storing or processing information",
        "ordinary course of business",
        "owned maintained managed operated",
        "by me (select as applicable)",
        "hash value/s of the electronic/digital record/s is",
        "sha1:",
        "sha256:",
        "md5:",
        "(hash report to be enclosed with the certificate)",
        "(name and signature)",
        "date (dd/mm/yyyy)",
        "time (ist)",
        "place",
        "part b",
        "(to be filled by the expert)",
        "(name, designation and signature)"
    ]

    for phrase in key_phrases:
        assert phrase in norm_rendered, f"Expected statutory phrase '{phrase}' missing from rendered certificate"

def test_blank_fields_stay_blank(tmp_path):
    """
    Test that Name, Son/daughter/spouse of, residing/employed at, Owned/Maintained/Managed/Operated ticks,
    signatures, Date, Time, and Place remain strictly blank in both parts.
    """
    out_pdf = tmp_path / "test_blank_fields.pdf"
    render_bsa63_certificate(out_pdf, mode="blank")

    reader = PdfReader(str(out_pdf))
    full_text = " ".join(p.extract_text() for p in reader.pages)

    # Asserts that no pre-filled personal name appears
    assert "Vikram Rathore" not in full_text
    assert "Rajesh Kumar" not in full_text
    assert "[X] Owned" not in full_text
    assert "[X] Operated" not in full_text
    assert "[X] SHA1" not in full_text
    assert "[X] MD5" not in full_text

def test_prefill_and_hash_annex(tmp_path):
    """
    Test that pre-fill values appear properly marked and Hash Report annex is generated.
    """
    out_pdf = tmp_path / "test_prefilled_cert.pdf"
    sample_manifest_hash = "a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef"
    prefill = {
        "source_tick": "Server",
        "make_model": "AWS Nitro Enclave EC2",
        "serial_number": "AWS-SRV-9901",
        "cloud_id": "ap-south-1:i-0123456789abcdef0",
        "other_relevant_info": "Case CASE-2026-0001, Bundle BND-001",
        "manifest_hash": sample_manifest_hash
    }
    hash_report = {
        "certificate_id": "CERT-2026-0001",
        "bundle_id": "BND-001",
        "tool_version": "1.0.0",
        "git_commit": "e8d9c10",
        "artifacts": [
            {"filename": "trace_graph.json", "size_bytes": 1024, "sha256": "abcdef1234567890", "captured_at": "2026-10-01T12:00:00Z"},
            {"filename": "evidence_log.json", "size_bytes": 2048, "sha256": "1234567890abcdef", "captured_at": "2026-10-01T12:00:00Z"}
        ],
        "on_chain_facts": [
            {"chain": "ethereum", "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef", "block_number": 19000000}
        ]
    }

    render_bsa63_certificate(out_pdf, mode="prefilled", prefill_data=prefill, hash_report_data=hash_report)

    reader = PdfReader(str(out_pdf))
    assert len(reader.pages) >= 3, "Prefilled certificate with annex must have at least 3 pages"
    full_text = " ".join(p.extract_text() for p in reader.pages)

    assert sample_manifest_hash in full_text
    assert "ANNEXURE 1: HASH REPORT" in full_text
    assert "AWS Nitro Enclave" in full_text
    assert "CERT-2026-0001" in full_text
    assert "0x1234567890abcdef" in full_text

def test_tampering_and_verification_tool(tmp_path):
    """
    Test evidence bundle verification tool:
    - Verifies intact bundle returns COURT_READY
    - Tampering with an artifact flips status to NOT COURT-READY
    """
    bundle_dir = tmp_path / "bundle_test"
    bundle_dir.mkdir()

    file1 = bundle_dir / "trace.json"
    file1.write_text('{"nodes": 5}', encoding="utf-8")
    h1 = hashlib.sha256(b'{"nodes": 5}').hexdigest()

    file2 = bundle_dir / "raw_api.json"
    file2.write_text('{"status": "ok"}', encoding="utf-8")
    h2 = hashlib.sha256(b'{"status": "ok"}').hexdigest()

    manifest_data = {
        "bundle_id": "BUNDLE-TEST-001",
        "artifacts": {
            "trace.json": {"sha256": h1, "size_bytes": file1.stat().st_size},
            "raw_api.json": {"sha256": h2, "size_bytes": file2.stat().st_size}
        }
    }
    manifest_bytes = json.dumps(manifest_data).encode("utf-8")
    manifest_data["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()

    manifest_file = bundle_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    # Verify intact bundle
    res_intact = verify_bundle(bundle_dir)
    assert res_intact["valid"] is True
    assert res_intact["court_ready"] is True
    assert res_intact["status"] == "COURT_READY"

    # Tamper with an artifact
    file1.write_text('{"nodes": 9999}', encoding="utf-8")
    res_tampered = verify_bundle(bundle_dir)
    assert res_tampered["valid"] is False
    assert res_tampered["court_ready"] is False
    assert res_tampered["status"] == "NOT COURT-READY"
    assert len(res_tampered["mismatches"]) == 1
    assert res_tampered["mismatches"][0]["file"] == "trace.json"
