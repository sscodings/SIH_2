import os
import json
import time
import hmac
import hashlib
from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock

from app.db.models import Complaint, ComplaintWallet, Case, Alert, Label, ApiKey, AuditLog, OutboxMessage
from app.services.complaint_source import MockNcrpSource, ComplaintIngestionPipeline
from app.services.file_drop import scan_and_process_drop_dir
from app.services.outbox import enqueue_outbox, process_outbox_batch, generate_sahyog_notice
from app.api.v1.ingest import hash_api_key

def test_mock_ncrp_fixture_ingestion_pipeline(db_session):
    """
    Tests complete fixture ingestion across SYN-0001 through SYN-0012:
    - SYN-0001 accepted, priority Medium.
    - SYN-0001 duplicate replay rejected cleanly without DB dups.
    - SYN-0007: blank amount -> amount_unknown=True, blank txn_hash.
    - SYN-0008: links to SYN-0001 via complaint_wallets and raises NEW_LINKED_COMPLAINT alert.
    - SYN-0009: chain hint is ETH, but address format is Tron -> Tron overrides hint, warning logged.
    - SYN-0010: matches OFAC sanctioned entity -> CRITICAL alert raised.
    - SYN-0011: bad checksum -> rejected.
    - SYN-0012: matches known VASP hot wallet -> vasp_flag set, trace/case not auto-created.
    """
    # 1. Seed OFAC label for SYN-0010 Central Bank of Iran
    ofac_label = Label(
        chain="tron",
        address="TNiq9AXBp9EjUqhDhrwrfvAA8U3GUQZH81",
        entity="CENTRAL BANK OF THE ISLAMIC REPUBLIC OF IRAN",
        category="sanctioned",
        source="OFAC SDN",
        record_status="active"
    )
    db_session.add(ofac_label)

    # 2. Seed VASP label for SYN-0012 Binance Hot Wallet 2
    vasp_label = Label(
        chain="tron",
        address="TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi",
        entity="Binance",
        category="VASP",
        source="Exchange CSV",
        record_status="active"
    )
    db_session.add(vasp_label)
    db_session.commit()

    source = MockNcrpSource()
    rows = source.fetch_complaints()
    assert len(rows) >= 12

    results = {}
    for r in rows:
        cid = r["complaint_id"]
        res = ComplaintIngestionPipeline.process_record(db_session, r, source_system="NCRP")
        if cid not in results:
            results[cid] = []
        results[cid].append(res)

    # SYN-0001: Initial ingest accepted, replay duplicate
    assert len(results["SYN-0001"]) == 2
    assert results["SYN-0001"][0]["status"] == "accepted"
    assert results["SYN-0001"][0]["chain"] == "tron"
    assert results["SYN-0001"][1]["status"] == "duplicate"

    c1_count = db_session.query(Complaint).filter(Complaint.complaint_number == "SYN-0001").count()
    assert c1_count == 1

    # SYN-0007: blank amount
    assert results["SYN-0007"][0]["status"] == "accepted"
    assert results["SYN-0007"][0]["amount_unknown"] is True
    c7 = db_session.query(Complaint).filter(Complaint.complaint_number == "SYN-0007").first()
    assert c7.amount_unknown is True
    assert c7.txn_hash is None or c7.txn_hash == ""

    # SYN-0008: suspect wallet matches SYN-0001 (TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2)
    assert results["SYN-0008"][0]["status"] == "accepted"
    assert "SYN-0001" in results["SYN-0008"][0]["linked_complaints"]

    # Verify bi-directional link in DB
    c1 = db_session.query(Complaint).filter(Complaint.complaint_number == "SYN-0001").first()
    c8 = db_session.query(Complaint).filter(Complaint.complaint_number == "SYN-0008").first()
    assert "SYN-0008" in json.loads(c1.linked_complaint_ids or "[]")
    assert "SYN-0001" in json.loads(c8.linked_complaint_ids or "[]")

    # Verify NEW_LINKED_COMPLAINT alert
    link_alert = db_session.query(Alert).filter(Alert.alert_type == "NEW_LINKED_COMPLAINT").first()
    assert link_alert is not None
    assert "SYN-0008" in link_alert.title or "SYN-0008" in link_alert.message

    # SYN-0009: Tron format overrides ETH hint
    assert results["SYN-0009"][0]["status"] == "accepted"
    assert results["SYN-0009"][0]["chain"] == "tron"
    c9 = db_session.query(Complaint).filter(Complaint.complaint_number == "SYN-0009").first()
    assert c9.chain == "tron"
    payload_info = json.loads(c9.raw_payload or "{}")
    assert payload_info.get("chain_hint_mismatch") is True

    # SYN-0010: OFAC Sanctions Hit -> Critical Alert
    assert results["SYN-0010"][0]["status"] == "accepted"
    assert results["SYN-0010"][0]["sanctions_hit"] is True
    sanct_alert = db_session.query(Alert).filter(Alert.alert_type == "SANCTIONED_ENTITY_HIT").first()
    assert sanct_alert is not None
    assert sanct_alert.severity == "Critical"
    assert "CENTRAL BANK OF THE ISLAMIC REPUBLIC OF IRAN" in sanct_alert.message

    # SYN-0011: Bad Tron Checksum -> Rejected
    assert results["SYN-0011"][0]["status"] == "rejected"
    assert "Invalid wallet address" in results["SYN-0011"][0]["error"]
    c11 = db_session.query(Complaint).filter(Complaint.complaint_number == "SYN-0011").first()
    assert c11 is None

    # SYN-0012: Known VASP Hot Wallet -> Flagged, Case NOT Auto-Created
    assert results["SYN-0012"][0]["status"] == "accepted"
    assert results["SYN-0012"][0]["vasp_flag"] == "reported wallet is a known VASP"
    assert results["SYN-0012"][0]["case_created"] is False
    c12_case = db_session.query(Case).filter(Case.case_number == "CASE-SYN-0012").first()
    assert c12_case is None

def test_pii_role_based_access(client, db_session, investigator_token, supervisor_token, admin_token):
    """
    Tests Fernet PII encryption at rest and role-based unmasking:
    - Supervisor / Admin see unmasked victim_ref.
    - Investigator sees 'REDACTED'.
    """
    row = {
        "complaint_id": "SYN-PII-001",
        "state": "Maharashtra",
        "category": "Investment Fraud",
        "amount_inr": "600000",
        "victim_id_masked": "REAL_AADHAAR_9876",
        "suspect_wallet_address": "TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2",
        "chain": "tron"
    }
    res = ComplaintIngestionPipeline.process_record(db_session, row, source_system="NCRP")
    assert res["status"] == "accepted"
    complaint_id = res["complaint_id"]

    # Verify encrypted at rest
    raw_record = db_session.query(Complaint).filter(Complaint.id == complaint_id).first()
    assert raw_record.victim_ref != "REAL_AADHAAR_9876"
    assert "REAL_AADHAAR_9876" not in raw_record.victim_ref

    # 1. Investigator gets redacted
    inv_resp = client.get(
        f"/api/v1/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert inv_resp.status_code == 200
    assert inv_resp.json()["victim_ref"] == "REDACTED"

    # 2. Supervisor gets unmasked
    sup_resp = client.get(
        f"/api/v1/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {supervisor_token}"}
    )
    assert sup_resp.status_code == 200
    assert sup_resp.json()["victim_ref"] == "REAL_AADHAAR_9876"

    # 3. Admin gets unmasked
    adm_resp = client.get(
        f"/api/v1/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert adm_resp.status_code == 200
    assert adm_resp.json()["victim_ref"] == "REAL_AADHAAR_9876"

def test_rest_ingest_auth_and_hmac(client, db_session):
    """
    Tests REST ingestion API key auth, scope enforcement, clock skew, and HMAC signature:
    - Missing key -> 401
    - Invalid key -> 401
    - Lacks scope -> 403
    - Timestamp skew > 300s -> 400
    - Invalid HMAC signature -> 401
    - Valid HMAC signature -> 200 accepted
    """
    raw_key = "sk_live_1234567890abcdef"
    secret = "test_hmac_secret_key_555"

    api_key = ApiKey(
        name="LEA Portal Key",
        key_prefix=raw_key[:16],
        hashed_key=hash_api_key(raw_key),
        secret=secret,
        scopes="ingest:write",
        role="investigator",
        is_active=True
    )
    db_session.add(api_key)
    db_session.commit()

    payload = {
        "complaint_id": "REST-001",
        "suspect_wallet_address": "TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2",
        "chain": "tron",
        "amount_inr": 250000,
        "category": "Cyber Scam"
    }
    body_str = json.dumps(payload)

    # 1. Missing X-API-Key
    r1 = client.post("/api/v1/ingest/complaints", content=body_str)
    assert r1.status_code == 401
    assert "Missing X-API-Key" in r1.json()["detail"]

    # 2. Invalid API key
    r2 = client.post(
        "/api/v1/ingest/complaints",
        content=body_str,
        headers={"X-API-Key": "wrong_key_prefix"}
    )
    assert r2.status_code == 401

    # 3. Scoped key lacks ingest:write
    readonly_key = ApiKey(
        name="Readonly Key",
        key_prefix="sk_read_12345678",
        hashed_key=hash_api_key("sk_read_12345678"),
        scopes="read:only",
        role="investigator",
        is_active=True
    )
    db_session.add(readonly_key)
    db_session.commit()

    r3 = client.post(
        "/api/v1/ingest/complaints",
        content=body_str,
        headers={"X-API-Key": "sk_read_12345678"}
    )
    assert r3.status_code == 403
    assert "lacks 'ingest:write' scope" in r3.json()["detail"]

    # 4. Timestamp skew > 300s
    old_ts = str(time.time() - 400)
    r4 = client.post(
        "/api/v1/ingest/complaints",
        content=body_str,
        headers={
            "X-API-Key": raw_key,
            "X-Timestamp": old_ts,
            "X-Signature-SHA256": "any_sig"
        }
    )
    assert r4.status_code == 400
    assert "Timestamp skew exceeds 300 seconds" in r4.json()["detail"]

    # 5. Invalid HMAC signature
    now_ts = str(time.time())
    r5 = client.post(
        "/api/v1/ingest/complaints",
        content=body_str,
        headers={
            "X-API-Key": raw_key,
            "X-Timestamp": now_ts,
            "X-Signature-SHA256": "bad_hex_signature"
        }
    )
    assert r5.status_code == 401
    assert "Invalid HMAC signature" in r5.json()["detail"]

    # 6. Valid HMAC signature
    msg = f"{now_ts}.{body_str}".encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    r6 = client.post(
        "/api/v1/ingest/complaints",
        content=body_str,
        headers={
            "X-API-Key": raw_key,
            "X-Timestamp": now_ts,
            "X-Signature-SHA256": valid_sig,
            "Content-Type": "application/json"
        }
    )
    assert r6.status_code == 200
    res_data = r6.json()
    assert res_data["status"] == "success"
    assert res_data["results"][0]["complaint_number"] == "REST-001"

    # Verify per-key audit log entry
    audit = db_session.query(AuditLog).filter(
        AuditLog.user_email == "api_key:LEA Portal Key"
    ).first()
    assert audit is not None
    assert audit.action == "INGEST_REST_COMPLAINT"

def test_file_drop_watcher(tmp_path, db_session):
    """
    Tests file drop directory watcher:
    - Successfully processes CSV files, moving them to processed/
    - Moves corrupt files to failed/ and creates .err sidecar
    """
    drop_dir = str(tmp_path / "drop")
    os.makedirs(drop_dir, exist_ok=True)

    # 1. Create a valid CSV
    valid_csv = os.path.join(drop_dir, "batch_01.csv")
    with open(valid_csv, "w", encoding="utf-8") as f:
        f.write("complaint_id,state,category,amount_inr,suspect_wallet_address,chain\n")
        f.write("DROP-001,Maharashtra,Fraud,100000,TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2,tron\n")

    # 2. Create an empty / corrupt CSV
    corrupt_csv = os.path.join(drop_dir, "corrupt_01.csv")
    with open(corrupt_csv, "w", encoding="utf-8") as f:
        f.write("")  # empty file

    summary = scan_and_process_drop_dir(db_session, drop_dir=drop_dir)

    assert len(summary["files_processed"]) == 1
    assert summary["files_processed"][0]["filename"] == "batch_01.csv"
    assert summary["total_accepted"] == 1

    assert len(summary["files_failed"]) == 1
    assert summary["files_failed"][0]["filename"] == "corrupt_01.csv"

    # Verify file locations
    assert os.path.exists(os.path.join(drop_dir, "processed", "batch_01.csv"))
    assert os.path.exists(os.path.join(drop_dir, "failed", "corrupt_01.csv"))
    assert os.path.exists(os.path.join(drop_dir, "failed", "corrupt_01.csv.err"))

def test_sahyog_outbound_notice_and_outbox(client, db_session):
    """
    Tests SAHYOG notice generation and outbox queue:
    - Generates outbound notice with strict IT Act disclaimer
    - Outbox enqueues and tracks pending status
    """
    complaint = Complaint(
        complaint_number="SAHYOG-TEST-001",
        source_system="NCRP",
        source="NCRP",
        victim_name="Victim",
        victim_state="Delhi",
        fraud_type="Digital Arrest",
        reported_wallets=json.dumps(["TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2"]),
        chain="tron",
        amount_lost_inr=500000,
        amount_lost_usd=6000,
        claimed_vasp_hint="WazirX"
    )
    db_session.add(complaint)
    db_session.commit()

    notice = generate_sahyog_notice(complaint)
    assert notice["notice_type"] == "IT_ACT_S79_3_B"
    assert "UNVERIFIED PROTOTYPE EXPORT" in notice["disclaimer"]
    assert notice["complaint_number"] == "SAHYOG-TEST-001"
    assert notice["claimed_vasp"] == "WazirX"

    outbox_msg = enqueue_outbox(
        db=db_session,
        event_type="sahyog_notice",
        destination_url="https://compliance.wazirx.in/notices",
        payload=notice
    )
    assert outbox_msg.id is not None
    assert outbox_msg.status == "pending"

    # Test outbox processing with mocked response
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        import asyncio
        results = asyncio.run(process_outbox_batch(db_session))
        assert len(results) >= 1
        assert results[0]["status"] == "sent"

    db_session.refresh(outbox_msg)
    assert outbox_msg.status == "sent"
    assert outbox_msg.sent_at is not None
