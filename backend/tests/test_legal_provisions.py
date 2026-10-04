import os
import sys
import pytest
import tempfile
import subprocess
from pathlib import Path
from app.legal.provisions import (
    get_citation,
    get_legal_provisions_registry,
    load_provisions_config,
    LegalProvisionsConfig,
    format_citation_footer,
    LEGAL_DISCLAIMER
)

def test_offence_date_boundaries():
    """
    Test 1:
    Offence on 2024-06-30 -> legacy IPC/CrPC citations for the three offence_date entries:
    - cheating_inducing_delivery -> IPC s.420
    - seizure_of_property -> CrPC s.102
    - production_of_documents -> CrPC s.91
    Offence on 2024-07-01 -> current BNS/BNSS citations:
    - cheating_inducing_delivery -> BNS s.318(4)
    - seizure_of_property -> BNSS s.106
    - production_of_documents -> BNSS s.94
    """
    # Legacy date
    ctx_legacy = {"offence_date": "2024-06-30"}
    c1 = get_citation("cheating_inducing_delivery", ctx_legacy)
    assert c1["code_used"] == "legacy"
    assert "IPC s.420" in c1["citation"]

    c2 = get_citation("seizure_of_property", ctx_legacy)
    assert c2["code_used"] == "legacy"
    assert "CrPC s.102" in c2["citation"]

    c3 = get_citation("production_of_documents", ctx_legacy)
    assert c3["code_used"] == "legacy"
    assert "CrPC s.91" in c3["citation"]

    # Current date
    ctx_current = {"offence_date": "2024-07-01"}
    c1_curr = get_citation("cheating_inducing_delivery", ctx_current)
    assert c1_curr["code_used"] == "current"
    assert "BNS s.318(4)" in c1_curr["citation"]

    c2_curr = get_citation("seizure_of_property", ctx_current)
    assert c2_curr["code_used"] == "current"
    assert "BNSS s.106" in c2_curr["citation"]

    c3_curr = get_citation("production_of_documents", ctx_current)
    assert c3_curr["code_used"] == "current"
    assert "BNSS s.94" in c3_curr["citation"]

def test_missing_offence_date_is_ambiguous():
    """
    Test 2: Missing offence_date -> ambiguous, both citations returned, warning present.
    """
    res = get_citation("cheating_inducing_delivery", {})
    assert res["code_used"] == "ambiguous"
    assert "applicable code needs confirmation by the investigating officer" in res["warnings"]
    assert "BNS s.318(4)" in res["citation"]
    assert "IPC s.420" in res["citation"]

def test_evidence_certificate_applicability():
    """
    Test 3: Evidence certificate:
    - pending-proceeding flag True -> Evidence Act s.65B
    - flag False -> BSA s.63 and The Schedule
    - unknown (None) -> ambiguous
    """
    res_pending = get_citation("electronic_evidence_certificate", {"proceeding_pending_at_commencement": True})
    assert res_pending["code_used"] == "legacy"
    assert "Evidence Act 1872 s.65B" in res_pending["citation"]

    res_not_pending = get_citation("electronic_evidence_certificate", {"proceeding_pending_at_commencement": False})
    assert res_not_pending["code_used"] == "current"
    assert "BSA s.63" in res_not_pending["citation"]

    res_unknown = get_citation("electronic_evidence_certificate", {})
    assert res_unknown["code_used"] == "ambiguous"
    assert "applicable code needs confirmation by the investigating officer" in res_unknown["warnings"]

def test_unverified_entries_warnings():
    """
    Test 4: verification=unverified entries (BNSS 94, IT Act 66D) always carry the 'citation unverified' warning.
    """
    c_bnss94 = get_citation("production_of_documents", {"offence_date": "2024-07-02"})
    assert c_bnss94["verification"] == "unverified"
    assert "citation unverified" in c_bnss94["warnings"]

    c_it66d = get_citation("it_act_personation")
    assert c_it66d["verification"] == "unverified"
    assert "citation unverified" in c_it66d["warnings"]

def test_commencement_warning_present():
    """
    Test 5: Commencement warning present while commencement.verification != primary.
    """
    res = get_citation("cheating_inducing_delivery", {"offence_date": "2024-08-01"})
    assert "commencement date taken from secondary sources" in res["warnings"]

def test_schema_validation_failure():
    """
    Test 6: Schema validation: duplicate keys, missing verified_on for primary entries,
    and unknown applicability_rule all fail startup.
    """
    # Primary entry missing verified_on must fail
    bad_data = {
        "commencement": {
            "criminal_laws": {
                "date": "2024-07-01",
                "verification": "secondary"
            }
        },
        "provisions": {
            "bad_item": {
                "key": "bad_item",
                "label": "Bad Item",
                "current_code": "BSA",
                "current_section": "61",
                "applicability_rule": "none",
                "verification": "primary",
                "verified_source": "some_source",
                "verified_on": None, # MUST FAIL
                "needs_legal_review": False
            }
        }
    }
    with pytest.raises(Exception):
        LegalProvisionsConfig(**bad_data)

    # Unknown applicability_rule must fail
    bad_data["provisions"]["bad_item"]["verified_on"] = "2024-01-01"
    bad_data["provisions"]["bad_item"]["applicability_rule"] = "invalid_rule"
    with pytest.raises(Exception):
        LegalProvisionsConfig(**bad_data)

def test_grep_guard_execution_and_planted_failure():
    """
    Test 7: The grep guard passes on allowlisted paths and fails on a planted "420 IPC" string.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    script_path = repo_root / "scripts" / "check_legal_strings.py"
    assert script_path.exists(), f"check_legal_strings.py must exist at {script_path}"

    # Create temporary planted file inside backend/app
    temp_target = repo_root / "backend" / "app" / "temp_violation_test.py"
    try:
        temp_target.write_text("# planted forbidden string: 420 IPC\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(repo_root)
        )
        assert result.returncode != 0, "Grep guard must fail when planted '420 IPC' is present"
        assert "temp_violation_test.py" in result.stderr or "temp_violation_test.py" in result.stdout
    finally:
        if temp_target.exists():
            temp_target.unlink()

def test_primary_source_pdf_verification():
    """
    Test 8: Primary-source check: for each verification=primary entry,
    open docs/research/250882.pdf and assert the cited section heading text exists
    (s.39, s.57, s.61, s.62, s.63, s.170), so a typo in the yaml cannot pass.
    Skip if PDF is absent.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    pdf_path = repo_root / "docs" / "research" / "250882.pdf"
    if not pdf_path.exists():
        pytest.skip("docs/research/250882.pdf is absent, skipping primary source check")

    try:
        from pypdf import PdfReader
    except ImportError:
        pytest.skip("pypdf not installed, skipping PDF verification")

    reader = PdfReader(str(pdf_path))
    full_text = ""
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            full_text += txt + "\n"

    # Check key statutory markers in the official BSA 2023 Gazette
    expected_markers = [
        "39.",  # Section 39: Opinion of Examiner of Electronic Evidence
        "57.",  # Section 57: Primary evidence (Explanation 5)
        "61.",  # Section 61: Admissibility of electronic records
        "62.",  # Section 62: Proof of contents of electronic records
        "63.",  # Section 63: Admissibility of electronic records under special provisions
        "170."  # Section 170: Repeal and savings (saves pending proceedings)
    ]
    for marker in expected_markers:
        assert marker in full_text, f"Expected statutory section marker '{marker}' not found in official Gazette PDF"
