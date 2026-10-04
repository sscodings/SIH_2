import pytest
from app.db.models import Case, Label, FreezeRequest, Entity
from app.core.config import settings

def test_api_health_and_root(client, auth_client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["platform"] == "ChainNetra"
    assert data["docs"] == "/docs"

    health = auth_client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

def test_api_cases_crud_smoke(auth_client, db_session):
    # Create case
    create_payload = {
        "title": "Crypto Extortion Investigation",
        "description": "Victim reported ransomware ransom payment",
        "primary_chain": "tron",
        "primary_address": "TYDzsYUE2UtZZTqXz31eS7x7ZnyQ7vX5rA",
        "priority": "Critical",
        "complaint_ids": []
    }
    res = auth_client.post("/api/v1/cases", json=create_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "created"
    case_id = data["case_id"]

    # Read case
    get_res = auth_client.get(f"/api/v1/cases/{case_id}")
    assert get_res.status_code == 200
    case_data = get_res.json()
    assert case_data["title"] == "Crypto Extortion Investigation"
    assert case_data["primary_address"] == "TYDzsYUE2UtZZTqXz31eS7x7ZnyQ7vX5rA"

    # Read graph
    graph_res = auth_client.get(f"/api/v1/cases/{case_id}/graph")
    assert graph_res.status_code == 200
    assert len(graph_res.json()["nodes"]) >= 1

def test_api_freeze_requests_workflow(client, db_session, investigator_token, supervisor_token):
    # Create Case
    case = Case(
        case_number="CASE-FREEZE-TEST",
        title="Freeze Target Case",
        primary_chain="ethereum",
        primary_address="0x1111111111111111111111111111111111111111",
        status="Active",
        priority="High",
        created_by="investigator@demo"
    )
    db_session.add(case)

    # Create entity
    entity = Entity(
        name="WazirX Exchange",
        category="VASP",
        jurisdiction="India",
        compliance_contact="nodal@wazirx.demo",
        response_sla="4 Hours"
    )
    db_session.add(entity)
    db_session.commit()

    # Incomplete freeze request (Draft)
    draft_incomplete = {
        "case_id": case.id,
        "vasp_id": entity.id,
        "deposit_address": "0x2222222222222222222222222222222222222222",
        "suspect_wallet": "0x1111111111111111111111111111111111111111",
        "notes": "Draft incomplete"
    }
    res_draft = client.post("/api/v1/freeze-requests", json=draft_incomplete, headers={"Authorization": f"Bearer {investigator_token}"})
    assert res_draft.status_code == 200
    draft_id = res_draft.json()["freeze_request_id"]

    # Transitioning to Pending Approval with missing statutory fields must return 422
    p_err = client.patch(f"/api/v1/freeze-requests/{draft_id}/status", json={"status": "Pending Approval"}, headers={"Authorization": f"Bearer {investigator_token}"})
    assert p_err.status_code == 422
    assert "Missing required statutory fields" in p_err.json()["detail"]

    # Create freeze request with statutory fields (Draft)
    freeze_payload = {
        "case_id": case.id,
        "vasp_id": entity.id,
        "deposit_address": "0x2222222222222222222222222222222222222222",
        "suspect_wallet": "0x1111111111111111111111111111111111111111",
        "legal_order_ref": "Cr.No 120/2026",
        "notes": "Emergency statutory hold",
        "fir_number": "Cr.No 120/2026",
        "fir_date": "2026-02-10",
        "police_station": "Cyber PS Mumbai",
        "district_state": "Mumbai, Maharashtra",
        "offence_sections": ["BNS 318(4)"],
        "io_name": "PI R. Patil",
        "io_designation": "Police Inspector",
        "io_contact": "+91-9876543211",
        "legal_basis": "bnss_106_seizure",
        "freeze_amount": 25000.0,
        "traced_tainted_amount": 25000.0
    }
    res = client.post("/api/v1/freeze-requests", json=freeze_payload, headers={"Authorization": f"Bearer {investigator_token}"})
    assert res.status_code == 200
    fr_id = res.json()["freeze_request_id"]

    # Submit for approval (Draft -> Pending Approval)
    p_res = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Pending Approval"}, headers={"Authorization": f"Bearer {investigator_token}"})
    assert p_res.status_code == 200

    # Approve (Pending Approval -> Approved by supervisor)
    appr_res = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Approved"}, headers={"Authorization": f"Bearer {supervisor_token}"})
    assert appr_res.status_code == 200

    # Mark as Sent (Approved -> Sent)
    sent_res = client.patch(f"/api/v1/freeze-requests/{fr_id}/status", json={"status": "Sent"}, headers={"Authorization": f"Bearer {supervisor_token}"})
    assert sent_res.status_code == 200
    assert sent_res.json()["new_status"] == "Sent"

def test_api_cryptographic_verification(client):
    # Verification of non-existent/tampered hash
    fake_hash = "f" * 64
    res = client.get(f"/api/v1/verify/{fake_hash}")
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is False
    assert "Tampered" in data["status"] or "Unregistered" in data["status"]

def test_e2e_demo_mode_case_zero_smoke(auth_client, monkeypatch):
    """Clearly labelled End-To-End DEMO-mode verification test."""
    monkeypatch.setattr(settings, "CHAINNETRA_MODE", "DEMO")
    
    # Ingest test complaint
    ingest_payload = {
        "victim_name": "Demo Victim User",
        "victim_state": "Maharashtra",
        "fraud_type": "Investment Scam",
        "reported_wallets": ["TYDzsYUE2UtZZTqXz31eS7x7ZnyQ7vX5rA"],
        "amount_lost_inr": 5000000.0
    }
    res = auth_client.post("/api/v1/ingest/ncrp", json=ingest_payload)
    assert res.status_code == 200
    complaint_data = res.json()
    assert complaint_data["status"] == "ingested"
    assert "complaint_id" in complaint_data
    assert "complaint_number" in complaint_data
