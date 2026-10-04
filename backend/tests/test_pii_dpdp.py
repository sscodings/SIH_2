import os
import logging
import pytest
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from sqlalchemy import text
from app.db.models import Complaint, PIIAccessLog
from app.core.crypto import encrypt_pii, decrypt_pii, set_custom_fernet_keys, get_multi_fernet
from app.core.logging_redactor import PIIRedactionFilter
from app.services.retention import purge_expired_records
from app.core.time import utcnow

def test_pii_columns_are_ciphertext_in_db(db_session):
    """
    Test that PII columns (victim_ref) stored in the database are ciphertext,
    not plaintext, and transparently decrypt when read through ORM models.
    """
    secret_value = "VICTIM-AADHAAR-REF-987654321012"
    complaint = Complaint(
        complaint_number="CMP-TEST-PII-001",
        source="NCRP",
        victim_name="Victim (Masked)",
        victim_ref=secret_value,
        reported_wallets="[\"0x123\"]",
        chain="ethereum",
        amount_lost_inr=100000.0,
        amount_lost_usd=1200.0
    )
    db_session.add(complaint)
    db_session.commit()

    # Query raw database row using raw SQL to verify ciphertext at rest
    raw_val = db_session.execute(
        text("SELECT victim_ref FROM complaints WHERE complaint_number = 'CMP-TEST-PII-001'")
    ).scalar()


    assert raw_val != secret_value, "Raw database value must NOT be plaintext"
    assert raw_val.startswith("gAAAAA"), "Raw database value must be Fernet ciphertext"

    # Query through ORM model to verify transparent decryption
    fetched = db_session.query(Complaint).filter(Complaint.complaint_number == "CMP-TEST-PII-001").first()
    assert fetched.victim_ref == secret_value, "ORM query must decrypt ciphertext back to original value"

def test_key_rotation_re_reads_old_rows():
    """
    Test MultiFernet key rotation:
    - Data encrypted with Old Key can still be decrypted when New Key is prepended to the keyring.
    """
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()

    # Set old key as primary
    set_custom_fernet_keys([old_key])
    plaintext = "CONFIDENTIAL-VICTIM-CONTACT-DATA"
    ciphertext = encrypt_pii(plaintext)
    assert ciphertext.startswith("gAAAAA")

    # Rotate keys: New key is primary (first), Old key is retained for decryption
    set_custom_fernet_keys([new_key, old_key])
    decrypted = decrypt_pii(ciphertext)
    assert decrypted == plaintext, "MultiFernet must decrypt ciphertext created with rotated old key"

def test_unmasking_access_control_and_logging(client, investigator_token, supervisor_token, db_session):
    """
    Test unmasked access rules:
    - Default view masks personal data
    - Investigator cannot unmask (HTTP 403)
    - Supervisor without reason is rejected (HTTP 422)
    - Supervisor with reason receives unmasked data and view is logged to pii_access_log
    """
    secret_ref = "UNMASKED-IDENTITY-REF-888999"
    c = Complaint(
        complaint_number="CMP-UNMASK-001",
        source="NCRP",
        victim_name="Ramesh Sharma",
        victim_ref=secret_ref,
        reported_wallets="[\"0xabc\"]",
        chain="tron",
        amount_lost_inr=50000.0
    )
    db_session.add(c)
    db_session.commit()

    # 1. Default request by investigator: masked
    resp = client.get(
        f"/api/v1/complaints/{c.id}",
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["victim_ref"] == "REDACTED"
    assert data["victim_name"] == "Victim (Masked)"

    # 2. Investigator attempts unmasking: forbidden (403)
    resp_inv_unmask = client.get(
        f"/api/v1/complaints/{c.id}?unmask=true&reason=Investigating+case",
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert resp_inv_unmask.status_code == 403

    # 3. Supervisor attempts unmasking without reason: rejected (422)
    resp_sup_no_reason = client.get(
        f"/api/v1/complaints/{c.id}?unmask=true",
        headers={"Authorization": f"Bearer {supervisor_token}"}
    )
    assert resp_sup_no_reason.status_code == 422

    # 4. Supervisor unmasks with mandatory reason: success
    resp_sup_valid = client.get(
        f"/api/v1/complaints/{c.id}?unmask=true&reason=Court+summons+verification+under+warrant",
        headers={"Authorization": f"Bearer {supervisor_token}"}
    )
    assert resp_sup_valid.status_code == 200
    unmasked_data = resp_sup_valid.json()
    assert unmasked_data["victim_ref"] == secret_ref

    # Verify PII access log entry was created
    log_entry = db_session.query(PIIAccessLog).filter(PIIAccessLog.record_id == str(c.id)).first()
    assert log_entry is not None
    assert log_entry.user_email == "supervisor@demo"
    assert "Court summons verification" in log_entry.reason

def test_log_redaction_filter():
    """
    Test that PIIRedactionFilter strips Aadhaar, phone, and email from log records.
    """
    logger = logging.getLogger("test_redactor")
    logger.addFilter(PIIRedactionFilter())

    record = logging.LogRecord(
        name="test_redactor",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Victim Aadhaar 1234 5678 9012, Phone +91 9876543210, Email victim@example.com reported fraud.",
        args=(),
        exc_info=None
    )
    filter_instance = PIIRedactionFilter()
    filter_instance.filter(record)

    assert "1234 5678 9012" not in record.msg
    assert "[REDACTED_AADHAAR]" in record.msg
    assert "9876543210" not in record.msg
    assert "[REDACTED_PHONE]" in record.msg
    assert "victim@example.com" not in record.msg
    assert "[REDACTED_EMAIL]" in record.msg

def test_retention_purge_skips_legal_hold(db_session):
    """
    Test that retention purge anonymizes expired records but skips records marked with legal_hold=True.
    """
    past_date = utcnow() - timedelta(days=400)

    # Expired complaint without legal hold
    c_expired = Complaint(
        complaint_number="CMP-EXPIRED-001",
        source="NCRP",
        victim_name="John Doe",
        victim_ref="SENSITIVE-DATA-1",
        reported_wallets="[\"0x111\"]",
        chain="tron",
        reported_at=past_date,
        legal_hold=False
    )
    # Expired complaint WITH legal hold
    c_hold = Complaint(
        complaint_number="CMP-HOLD-002",
        source="NCRP",
        victim_name="Jane Smith",
        victim_ref="SENSITIVE-DATA-2",
        reported_wallets="[\"0x222\"]",
        chain="tron",
        reported_at=past_date,
        legal_hold=True
    )
    db_session.add_all([c_expired, c_hold])
    db_session.commit()

    # Execute purge with 365 days window
    res = purge_expired_records(db_session, retention_days=365, actor_email="admin@demo")
    assert res["purged_count"] == 1
    assert res["skipped_legal_hold"] == 1

    # Verify c_expired is anonymized
    db_session.refresh(c_expired)
    assert c_expired.victim_ref is None
    assert c_expired.victim_name == "ANONYMIZED_PURGED"

    # Verify c_hold remains intact
    db_session.refresh(c_hold)
    assert c_hold.victim_ref == "SENSITIVE-DATA-2"
    assert c_hold.victim_name == "Jane Smith"
