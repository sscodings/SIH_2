import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import patch, MagicMock

from app.db.models import (
    Case, TraceJob, Alert, Watchlist, Label, SystemCounter, get_next_sequence_number
)
from app.worker import sweep_stuck_jobs, monitor_watchlist_wallets, run_trace_job
from app.core.config import Settings

def test_locked_sequence_counters(db_session, client, investigator_token):
    """Tests thread-safe locked sequential numbering for cases and freeze requests."""
    c1 = get_next_sequence_number(db_session, "case", "CASE")
    c2 = get_next_sequence_number(db_session, "case", "CASE")
    assert c1 == "CASE-2026-001001"
    assert c2 == "CASE-2026-001002"

    fr1 = get_next_sequence_number(db_session, "freeze", "FR")
    assert fr1 == "FR-2026-001001"

    # Test create case API assigns sequential case number
    resp = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {investigator_token}"},
        json={
            "title": "Sequence Test Case",
            "primary_chain": "tron",
            "primary_address": "TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2",
            "priority": "High"
        }
    )
    assert resp.status_code == 200
    case_data = resp.json()
    assert case_data["case_number"] == "CASE-2026-001003"

def test_trace_job_lifecycle_and_cancellation(db_session, client, investigator_token):
    """
    Tests TraceJob creation, queuing, and cancellation:
    - POST /cases/{id}/trace creates TraceJob in DB with status 'queued'
    - DELETE /cases/{id}/trace/{job_id} marks job 'cancelled'
    """
    case = Case(
        case_number="CASE-TRACE-001",
        title="Trace Test",
        primary_chain="tron",
        primary_address="TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2",
        status="Active",
        created_by="investigator@demo"
    )
    db_session.add(case)
    db_session.commit()

    resp = client.post(
        f"/api/v1/cases/{case.id}/trace",
        headers={"Authorization": f"Bearer {investigator_token}"},
        json={"max_depth": 2, "min_value_usd": 100.0}
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Verify job in DB
    job = db_session.query(TraceJob).filter(TraceJob.id == job_id).first()
    assert job is not None
    assert job.status in ("queued", "running", "completed")

    # Cancel trace
    cancel_resp = client.delete(
        f"/api/v1/cases/{case.id}/trace/{job_id}",
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    db_session.refresh(job)
    assert job.cancelled is True
    assert job.status == "cancelled"

def test_stuck_job_sweeper(db_session):
    """Tests sweeper marks orphaned/timed-out running jobs as failed."""
    past_time = datetime.utcnow() - timedelta(minutes=45)

    stuck_job = TraceJob(
        id="job-stuck-001",
        case_id=1,
        status="running",
        started_at=past_time
    )
    db_session.add(stuck_job)
    db_session.commit()

    # Run sweeper
    swept = asyncio.run(sweep_stuck_jobs(db=db_session))
    assert swept >= 1

    db_session.refresh(stuck_job)
    assert stuck_job.status == "failed"
    assert "stuck job sweep" in stuck_job.error_message

def test_watchlist_monitoring_and_alert_severities(db_session):
    """
    Tests watchlist monitoring and decisions.md item 4 severity rules:
    - Sanctioned hit -> Critical
    - VASP transfer -> High
    - Deduplication prevents duplicate alerts on repeated runs
    """
    # 1. Monitored wallet
    watch_addr = "TNiq9AXBp9EjUqhDhrwrfvAA8U3GUQZH81"
    item = Watchlist(
        address=watch_addr,
        chain="tron",
        label="Target Mule",
        reason="Investment fraud suspect"
    )
    db_session.add(item)

    # 2. Seed active OFAC label for this address
    lbl = Label(
        chain="tron",
        address=watch_addr,
        entity="CENTRAL BANK OF THE ISLAMIC REPUBLIC OF IRAN",
        category="sanctioned",
        source="OFAC SDN",
        record_status="active"
    )
    db_session.add(lbl)
    db_session.commit()

    res1 = asyncio.run(monitor_watchlist_wallets(db=db_session))
    assert res1["checked"] >= 1
    assert res1["new_alerts"] >= 1

    # Check alert severity
    alert = db_session.query(Alert).filter(Alert.address == watch_addr).first()
    assert alert is not None
    assert alert.severity == "Critical"
    assert alert.alert_type == "SANCTIONED_ENTITY_HIT"
    assert alert.status == "new"

    # 3. Repeated run should not duplicate alert (dedup_key)
    res2 = asyncio.run(monitor_watchlist_wallets(db=db_session))
    assert res2["new_alerts"] == 0

    total_alerts = db_session.query(Alert).filter(Alert.address == watch_addr).count()
    assert total_alerts == 1

def test_alerts_ack_and_resolve_lifecycle(client, db_session, investigator_token):
    """Tests alert listing, acknowledgment, and resolution endpoints."""
    alert = Alert(
        alert_type="NEW_INFLOW",
        severity="Medium",
        title="New Inflow Detected",
        message="5,000 USDT received",
        address="TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2",
        chain="tron",
        status="new"
    )
    db_session.add(alert)
    db_session.commit()

    # 1. List alerts with status filter
    r_list = client.get(
        "/api/v1/alerts?status=new",
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert r_list.status_code == 200
    assert len(r_list.json()["alerts"]) >= 1

    # 2. Acknowledge alert
    r_ack = client.post(
        f"/api/v1/alerts/{alert.id}/ack",
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert r_ack.status_code == 200
    assert r_ack.json()["status"] == "acknowledged"

    db_session.refresh(alert)
    assert alert.status == "ack"
    assert alert.is_acknowledged is True
    assert alert.acknowledged_by == "investigator@demo"

    # 3. Resolve alert
    r_res = client.post(
        f"/api/v1/alerts/{alert.id}/resolve",
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert r_res.status_code == 200
    assert r_res.json()["status"] == "resolved"

    db_session.refresh(alert)
    assert alert.status == "resolved"
    assert alert.resolved_by == "investigator@demo"
    assert alert.resolved_at is not None

def test_monitor_status_endpoint(client, investigator_token):
    """Tests GET /api/v1/alerts/monitor/status returns healthy monitoring metrics."""
    resp = client.get(
        "/api/v1/alerts/monitor/status",
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "wallets_checked" in data["metrics"]
    assert "alerts_generated" in data["metrics"]
