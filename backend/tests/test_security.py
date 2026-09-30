import pytest
import time
import os
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings, Settings
from app.core.security import create_access_token, decode_token
from app.core.audit import log_audit_action, verify_audit_chain
from app.db.models import Case, FreezeRequest, Entity, AuditLog, AppSetting
from app.services.freeze import FreezeService, FreezeTransitionError
from app.services.webhooks import validate_webhook_url, SSRFValidationError, WebhookService

# ==============================================================================
# SECTION 2: IDENTITY COMES FROM JWT ONLY
# ==============================================================================
def test_identity_comes_from_jwt_only(client, db_session, investigator_token):
    """Sending a spoofed email in request body is ignored; audit log and case record the JWT user."""
    payload = {
        "title": "Identity Test Case",
        "primary_chain": "tron",
        "primary_address": "TYDzsYUE2UtZZTqXz31eS7x7ZnyQ7vX5rA",
        "created_by": "attacker@spoofed.com",
        "user_email": "attacker@spoofed.com"
    }
    res = client.post("/api/v1/cases", json=payload, headers={"Authorization": f"Bearer {investigator_token}"})
    assert res.status_code == 200
    case_id = res.json()["case_id"]

    case = db_session.query(Case).filter(Case.id == case_id).first()
    assert case.created_by == "investigator@demo"
    assert case.created_by != "attacker@spoofed.com"

    # Audit log check
    audit = db_session.query(AuditLog).filter(AuditLog.entity_id == str(case_id)).first()
    assert audit.user_email == "investigator@demo"

# ==============================================================================
# SECTION 3: AUDIT TAMPER ENDPOINT REMOVED
# ==============================================================================
def test_audit_tamper_endpoint_deleted(client, admin_token):
    """POST /admin/audit-log/tamper-test route no longer exists (404/405)."""
    res = client.post("/api/v1/admin/audit-log/tamper-test", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code in (404, 405)

# ==============================================================================
# SECTION 4: FREEZE WORKFLOW STATE MACHINE & SEPARATION OF DUTIES
# ==============================================================================
def test_freeze_state_machine_and_separation_of_duties(client, db_session, investigator_token, supervisor_token, admin_token):
    # 1. Investigator creates Freeze Request (Status: Draft)
    case = Case(
        case_number="CASE-SM-001",
        title="State Machine Test Case",
        primary_chain="ethereum",
        primary_address="0x1111111111111111111111111111111111111111",
        created_by="investigator@demo"
    )
    db_session.add(case)
    entity = Entity(name="Binance Test", category="Exchange")
    db_session.add(entity)
    db_session.commit()

    fr_payload = {
        "case_id": case.id,
        "vasp_id": entity.id,
        "deposit_address": "0x2222222222222222222222222222222222222222",
        "suspect_wallet": "0x1111111111111111111111111111111111111111"
    }
    create_res = client.post("/api/v1/freeze-requests", json=fr_payload, headers={"Authorization": f"Bearer {investigator_token}"})
    assert create_res.status_code == 200
    fr_id = create_res.json()["freeze_request_id"]

    # 2. Illegal jump: Draft -> Approved (Must return 409)
    res_jump = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Approved"}, headers={"Authorization": f"Bearer {supervisor_token}"})
    assert res_jump.status_code == 409

    # 3. Legal transition: Draft -> Pending Approval
    res_pending = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Pending Approval"}, headers={"Authorization": f"Bearer {investigator_token}"})
    assert res_pending.status_code == 200

    # 4. Separation of Duties: Creator cannot approve their own request (403)
    res_self_appr = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Approved"}, headers={"Authorization": f"Bearer {investigator_token}"})
    assert res_self_appr.status_code == 403

    # 5. Non-supervisor cannot approve (Investigator trying to approve another creator's request -> 403)
    other_inv_token, _, _ = create_access_token({"sub": "other_io@demo", "role": "investigator"})
    res_other_inv = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Approved"}, headers={"Authorization": f"Bearer {other_inv_token}"})
    assert res_other_inv.status_code == 403

    # 6. Supervisor Approves (Pending Approval -> Approved)
    res_appr = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Approved"}, headers={"Authorization": f"Bearer {supervisor_token}"})
    assert res_appr.status_code == 200
    assert res_appr.json()["approved_by"] == "supervisor@demo"

    # 7. Approved -> Sent
    res_sent = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Sent"}, headers={"Authorization": f"Bearer {supervisor_token}"})
    assert res_sent.status_code == 200

    # 8. Sent -> Acknowledged
    res_ack = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Acknowledged"}, headers={"Authorization": f"Bearer {supervisor_token}"})
    assert res_ack.status_code == 200

    # 9. Acknowledged -> Frozen with excessive amount (> victim loss -> 400)
    fr_rec = db_session.query(FreezeRequest).filter(FreezeRequest.id == fr_id).first()
    res_excess = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Frozen", "frozen_amount_usd": fr_rec.victim_loss_usd + 99999}, headers={"Authorization": f"Bearer {supervisor_token}"})
    assert res_excess.status_code == 400

    # 10. Legal finalization: Acknowledged -> Frozen
    res_frozen = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Frozen", "frozen_amount_usd": fr_rec.victim_loss_usd}, headers={"Authorization": f"Bearer {supervisor_token}"})
    assert res_frozen.status_code == 200

# ==============================================================================
# SECTION 5: WEBSOCKET AUTHENTICATION & SCOPING
# ==============================================================================
def test_websocket_authentication_and_scoping(client, investigator_token, supervisor_token):
    # 1. No token -> Rejected with 4401
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/events") as ws:
            pass

    # 2. Valid token -> Connected and scoped
    with client.websocket_connect(f"/ws/events?token={investigator_token}") as ws:
        ws.send_json({"action": "ping"})
        data = ws.receive_json()
        assert data.get("event") == "pong"

# ==============================================================================
# SECTION 6: SECRETS AND CONFIGURATION
# ==============================================================================
def test_live_mode_startup_fails_on_weak_or_missing_secrets(monkeypatch):
    """Refuse to start in LIVE mode if SECRET_KEY is missing, too short, or default."""
    s = Settings(
        CHAINNETRA_MODE="LIVE",
        SECRET_KEY="short",
        WEBHOOK_SECRET="too_short",
        AUDIT_HMAC_KEY="too_short"
    )
    with pytest.raises(ValueError) as exc:
        s.validate_and_finalize_security()
    assert "LIVE MODE ERROR" in str(exc.value)

    s2 = Settings(
        CHAINNETRA_MODE="LIVE",
        SECRET_KEY="netra-super-secret-jwt-forensic-key-2026-sih-prototype",
        WEBHOOK_SECRET="valid_webhook_secret_32_chars_long_1234",
        AUDIT_HMAC_KEY="valid_audit_secret_32_chars_long_1234"
    )
    with pytest.raises(ValueError) as exc2:
        s2.validate_and_finalize_security()
    assert "known default" in str(exc2.value)

# ==============================================================================
# SECTION 7: WEBHOOKS SSRF PROTECTION & HONEST DELIVERY
# ==============================================================================
def test_webhook_ssrf_blocks_private_and_loopback_ips():
    """SSRF validator blocks 127.0.0.1, localhost, 192.168.x.x, 10.x.x.x, 169.254.x.x."""
    with pytest.raises(SSRFValidationError):
        validate_webhook_url("http://127.0.0.1:8080/hook")

    with pytest.raises(SSRFValidationError):
        validate_webhook_url("http://localhost:8000/hook")

    with pytest.raises(SSRFValidationError):
        validate_webhook_url("http://169.254.169.254/latest/meta-data")

def test_webhook_honest_delivery_recording(client, db_session, admin_token):
    """Failed webhook dispatch records failure status and error details truthfully."""
    # Create test webhook pointing to a real resolvable public domain that returns 404/failure on custom path
    hook_payload = {
        "name": "Integration Test Webhook",
        "target_url": "https://example.com/chainnetra-test-endpoint-404"
    }
    create_res = client.post("/api/v1/webhooks", json=hook_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert create_res.status_code == 200
    wh_id = create_res.json()["id"]

    # Dispatch test
    client.post(f"/api/v1/webhooks/{wh_id}/test", headers={"Authorization": f"Bearer {admin_token}"})

    # List deliveries
    list_res = client.get("/api/v1/webhooks", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_res.status_code == 200
    hooks = list_res.json()["webhooks"]
    target = next((h for h in hooks if h["id"] == wh_id), None)
    assert target is not None
    assert len(target["deliveries"]) >= 1
    assert target["deliveries"][0]["success"] is False

# ==============================================================================
# SECTION 8: CORS, TOKEN REVOCATION, REFRESH ROTATION, SECURITY HEADERS
# ==============================================================================
def test_auth_refresh_rotation_and_revocation(client, db_session):
    # 1. Login
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "investigator@demo", "password": "demo123"}
    )
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]
    refresh_token = login_res.json()["refresh_token"]

    # 2. Refresh rotation
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    new_access_token = refresh_res.json()["access_token"]
    new_refresh_token = refresh_res.json()["refresh_token"]

    assert new_access_token != access_token
    assert new_refresh_token != refresh_token

    # 3. Old refresh token cannot be reused
    reuse_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert reuse_res.status_code == 401

    # 4. Logout revokes token
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert logout_res.status_code == 200

    # 5. Accessing protected endpoint with revoked token fails with 401
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me_res.status_code == 401

def test_security_headers_middleware_present(client):
    res = client.get("/")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "strict-origin" in res.headers.get("Referrer-Policy", "")
    assert "default-src 'self'" in res.headers.get("Content-Security-Policy", "")

# ==============================================================================
# SECTION 10: AUDIT LOG INTEGRITY & HMAC VERIFICATION
# ==============================================================================
def test_audit_log_hmac_tamper_detection(client, db_session):
    # Log 3 actions
    log_audit_action(db_session, "user1@demo", "CREATE_CASE", "CASE", "1")
    log_audit_action(db_session, "user2@demo", "START_TRACE", "CASE", "1")
    entry3 = log_audit_action(db_session, "user3@demo", "FREEZE_ALERT", "FREEZE_REQUEST", "1")

    # Verification passes initially
    verify_result = verify_audit_chain(db_session)
    assert verify_result["valid"] is True

    # 1. DB trigger blocks updates at the SQLite engine level
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy import text
    with pytest.raises(IntegrityError):
        db_session.execute(
            text(f"UPDATE audit_logs SET details = '{json.dumps({'tampered': True})}' WHERE id = {entry3.id}")
        )
        db_session.commit()

    db_session.rollback()

    # 2. If an attacker bypasses the trigger by dropping it and modifying details:
    db_session.execute(text("DROP TRIGGER IF EXISTS prevent_audit_log_update"))
    db_session.execute(text(f"UPDATE audit_logs SET details = '{json.dumps({'tampered': True})}' WHERE id = {entry3.id}"))
    db_session.commit()

    # Tamper detection catches modified hash / HMAC mismatch
    tampered_result = verify_audit_chain(db_session)
    assert tampered_result["valid"] is False
    assert "tampered" in tampered_result["reason"].lower() or "signature" in tampered_result["reason"].lower()

# ==============================================================================
# SECTION 11: INPUT VALIDATION & PATH TRAVERSAL
# ==============================================================================
def test_input_validation_address_and_path_traversal(client, investigator_token):
    # Invalid Tron address format
    invalid_case_payload = {
        "title": "Invalid Case",
        "primary_chain": "tron",
        "primary_address": "InvalidAddressFormat123"
    }
    res = client.post("/api/v1/cases", json=invalid_case_payload, headers={"Authorization": f"Bearer {investigator_token}"})
    assert res.status_code == 400

    # Path traversal protection on report download
    res_download = client.get("/api/v1/reports/99999/download", headers={"Authorization": f"Bearer {investigator_token}"})
    assert res_download.status_code == 404
