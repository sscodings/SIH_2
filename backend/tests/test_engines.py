import pytest
import os
import json
import asyncio
from backend.app.engines.taint import TaintModel
from backend.app.engines.attribution import AttributionEngine
from backend.app.engines.tracer import TracingEngine
from backend.app.services.ingest import IngestionService
from backend.app.services.evidence import EvidenceService
from backend.app.services.reports import ReportService
from backend.app.core.audit import compute_entry_hash, verify_audit_chain
from backend.app.db.database import SessionLocal, Base, engine
from backend.app.db.models import Case, Report

def test_taint_models():
    haircut = TaintModel.calculate_taint("haircut", 500.0, 1000.0, 200.0)
    assert haircut == 100.0

    fifo = TaintModel.calculate_taint("fifo", 500.0, 1000.0, 200.0, remaining_taint_balance=150.0)
    assert fifo == 150.0

    poison = TaintModel.calculate_taint("poison", 50.0, 1000.0, 300.0)
    assert poison == 300.0

def test_confidence_formula():
    conf = AttributionEngine.calculate_confidence(
        label_source_weight=0.95,
        evidence_strength=1.0,
        cluster_support=0.90,
        hops_from_label=2
    )
    assert 80.0 <= conf["confidence_score"] <= 85.0
    assert conf["hops_from_label"] == 2

def test_address_validation_and_chain_detection():
    tron_res = IngestionService.detect_chain_and_validate("TXDemoxHotWalletPrimary88888888888")
    assert tron_res["valid"] is True
    assert tron_res["chain"] == "tron"

    evm_res = IngestionService.detect_chain_and_validate("0x71C84949C6ff62E90D88F2c1598f6A7B8E9f6A40")
    assert evm_res["valid"] is True
    assert evm_res["chain"] == "ethereum"

    btc_res = IngestionService.detect_chain_and_validate("bc1qveilmixprivacytumbler00000000")
    assert btc_res["valid"] is True
    assert btc_res["chain"] == "bitcoin"

    invalid_res = IngestionService.detect_chain_and_validate("invalid_crypto_address_999")
    assert invalid_res["valid"] is False

def test_audit_log_hash_chain():
    db = SessionLocal()
    try:
        check = verify_audit_chain(db)
        assert check["valid"] is True
        assert check["count"] >= 1
    finally:
        db.close()

def test_first_vasp_hit_case_zero():
    db = SessionLocal()
    try:
        c0 = db.query(Case).filter(Case.case_number == "CASE-2026-0001").first()
        assert c0 is not None

        tracer = TracingEngine(
            db=db,
            case_id=c0.id,
            start_address=c0.primary_address,
            chain=c0.primary_chain,
            initial_amount_usd=134500.0,
            max_depth=6,
            min_value_usd=50.0,
            stop_at_first_vasp=True
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(tracer.execute_trace("test_job_1"))
        loop.close()

        assert len(result["attributions"]) >= 1
        first_attr = result["attributions"][0]
        assert "DemoX Exchange" in first_attr["vasp_name"]
        assert first_attr["hops_from_suspect"] in [3, 4]
        assert first_attr["confidence_score"] >= 85.0
    finally:
        db.close()

def test_report_generation_and_evidence_verification():
    db = SessionLocal()
    try:
        c0 = db.query(Case).filter(Case.case_number == "CASE-2026-0001").first()
        report_meta = ReportService.generate_case_report(db, c0.id, "tester@demo")
        assert os.path.exists(report_meta["pdf_path"])

        # Check authentic verification
        check_auth = EvidenceService.verify_hash(db, report_meta["pdf_hash"])
        assert check_auth["status"] == "Authentic"
        assert check_auth["verified"] is True

        # Check tampered verification
        fake_hash = "a" * 64
        check_tampered = EvidenceService.verify_hash(db, fake_hash)
        assert "Tampered" in check_tampered["status"]
        assert check_tampered["verified"] is False
    finally:
        db.close()
