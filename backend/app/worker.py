import os
import json
import time
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from arq.connections import RedisSettings
from arq import cron

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import (
    Case, CaseComplaint, Complaint, TraceJob, TraceSnapshot,
    Attribution, FundsStatus, Alert, Watchlist, Label, AppSetting, SystemCounter
)
from app.engines.tracer import TracingEngine
from app.core.ws import ws_manager
from app.core.audit import log_audit_action

logger = logging.getLogger("chainnetra.worker")

# Shared in-memory / cache monitoring metrics for GET /api/v1/system/monitor
MONITOR_METRICS = {
    "last_run": None,
    "wallets_checked": 0,
    "alerts_generated": 0,
    "errors_count": 0,
    "stuck_jobs_swept": 0
}

async def sweep_stuck_jobs(ctx: Optional[dict] = None, db: Optional[Session] = None) -> int:
    """Marks orphaned or timed-out running jobs as failed."""
    owns_db = False
    if db is None:
        if isinstance(ctx, dict) and "db" in ctx:
            db = ctx["db"]
        else:
            db = SessionLocal()
            owns_db = True
    count = 0
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=30)
        stuck_jobs = db.query(TraceJob).filter(
            TraceJob.status == "running",
            TraceJob.started_at < cutoff
        ).all()

        for j in stuck_jobs:
            j.status = "failed"
            j.error_message = "Trace job timed out or worker process was terminated (stuck job sweep)"
            j.completed_at = datetime.utcnow()
            count += 1

        db.commit()
        MONITOR_METRICS["stuck_jobs_swept"] += count
        if count > 0:
            logger.info(f"Swept {count} stuck trace jobs to status 'failed'")
    except Exception as e:
        logger.error(f"Error during stuck job sweep: {e}")
        db.rollback()
    finally:
        if owns_db:
            db.close()
    return count

async def run_trace_job(ctx: dict, case_id: int, job_id: str, params: dict, actor_email: str, db: Optional[Session] = None):
    """Worker task executing TracingEngine with retry backoff and cancellation checks."""
    owns_db = False
    if db is None:
        if isinstance(ctx, dict) and "db" in ctx:
            db = ctx["db"]
        else:
            db = SessionLocal()
            owns_db = True
    try:
        job_rec = db.query(TraceJob).filter(TraceJob.id == job_id).first()
        if not job_rec:
            logger.error(f"TraceJob {job_id} not found in DB")
            return

        if job_rec.cancelled:
            job_rec.status = "cancelled"
            db.commit()
            return

        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            job_rec.status = "failed"
            job_rec.error_message = f"Case {case_id} not found"
            db.commit()
            return

        job_rec.status = "running"
        db.commit()

        # Calculate initial trace amount from linked complaints or caller param
        linked_complaints = db.query(Complaint).join(
            CaseComplaint, CaseComplaint.complaint_id == Complaint.id
        ).filter(CaseComplaint.case_id == case_id).all()

        if linked_complaints:
            initial_amt = sum(c.amount_lost_usd for c in linked_complaints)
        else:
            initial_amt = float(params.get("initial_amount_usd") or 1000.0)

        tracer = TracingEngine(
            db=db,
            case_id=case_id,
            start_address=case.primary_address,
            chain=case.primary_chain,
            initial_amount_usd=initial_amt,
            max_depth=params.get("max_depth", 6),
            min_value_usd=params.get("min_value_usd", 50.0),
            max_nodes=params.get("max_nodes", 400),
            time_window_hours=params.get("time_window_hours", 72),
            taint_model=params.get("taint_model", "haircut"),
            stop_at_first_vasp=params.get("stop_at_first_vasp", True)
        )

        # Dynamic cancellation check via DB query
        class DbCancelToken:
            def get(self, key, default=None):
                if key == "cancelled":
                    check_db = SessionLocal()
                    try:
                        j = check_db.query(TraceJob).filter(TraceJob.id == job_id).first()
                        return bool(j and j.cancelled)
                    finally:
                        check_db.close()
                return default

        cancel_token = DbCancelToken()
        result = await tracer.execute_trace(job_id=job_id, cancel_token=cancel_token)

        # Reload job_rec in current session
        job_rec = db.query(TraceJob).filter(TraceJob.id == job_id).first()
        if cancel_token.get("cancelled"):
            job_rec.status = "cancelled"
        else:
            job_rec.status = "completed"
        job_rec.completed_at = datetime.utcnow()
        job_rec.elapsed_seconds = result.get("elapsed_seconds", 0.0)

        # Update case time_to_vasp_seconds
        if result.get("time_to_vasp_seconds"):
            case.time_to_vasp_seconds = result["time_to_vasp_seconds"]

        # Save Attributions
        if result.get("attributions"):
            first_attr = result["attributions"][0]
            existing_attr = db.query(Attribution).filter(Attribution.case_id == case_id).first()
            if not existing_attr:
                existing_attr = Attribution(case_id=case_id)
                db.add(existing_attr)
            existing_attr.vasp_name = first_attr["vasp_name"]
            existing_attr.vasp_category = first_attr["vasp_category"]
            existing_attr.deposit_address = first_attr["deposit_address"]
            existing_attr.tx_hash = first_attr["tx_hash"]
            existing_attr.amount = first_attr["amount"]
            existing_attr.timestamp = datetime.fromisoformat(first_attr["timestamp"]) if isinstance(first_attr["timestamp"], str) else first_attr["timestamp"]
            existing_attr.hops_from_suspect = first_attr["hops_from_suspect"]
            existing_attr.confidence_score = first_attr["confidence_score"]
            existing_attr.evidence_breakdown = json.dumps(first_attr["evidence_breakdown"])

        # Save Funds Status
        if result.get("funds_status"):
            fs = db.query(FundsStatus).filter(FundsStatus.case_id == case_id).first()
            if not fs:
                fs = FundsStatus(case_id=case_id)
                db.add(fs)
            f_data = result["funds_status"]
            fs.total_traced_usd = f_data["total_traced_usd"]
            fs.vasp_amount_usd = f_data["vasp_amount_usd"]
            fs.mixer_amount_usd = f_data["mixer_amount_usd"]
            fs.dormant_amount_usd = f_data["dormant_amount_usd"]
            fs.unaccounted_usd = f_data["unaccounted_usd"]

        # Save Canonical Snapshot
        import hashlib
        snapshot_json = json.dumps(result, sort_keys=True)
        s_hash = hashlib.sha256(snapshot_json.encode('utf-8')).hexdigest()
        db.add(TraceSnapshot(case_id=case_id, snapshot_json=snapshot_json, sha256_hash=s_hash))

        db.commit()

        log_audit_action(
            db=db,
            user_email=actor_email,
            action="EXECUTE_TRACE",
            entity_type="CASE",
            entity_id=str(case_id),
            details={
                "job_id": job_id,
                "nodes": len(result.get("nodes", [])),
                "edges": len(result.get("edges", [])),
                "vasps_found": len(result.get("attributions", []))
            }
        )

        # Notify via WebSocket topic
        await ws_manager.broadcast_event(
            topic=f"trace:{case_id}",
            event_type="trace_complete",
            data={"job_id": job_id, "case_id": case_id, "nodes_count": len(result.get("nodes", []))}
        )

    except Exception as exc:
        logger.error(f"Trace job {job_id} encountered error: {exc}", exc_info=True)
        db.rollback()
        job_rec = db.query(TraceJob).filter(TraceJob.id == job_id).first()
        if job_rec:
            job_rec.retry_count += 1
            if job_rec.retry_count >= job_rec.max_retries:
                job_rec.status = "failed"
                job_rec.error_message = str(exc)
            else:
                job_rec.status = "queued"  # Will be picked up or retried
            db.commit()
    finally:
        if owns_db:
            db.close()

async def monitor_watchlist_wallets(ctx: Optional[dict] = None, db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Watches monitored watchlist addresses for suspicious inflows and counterparties.
    Applies decisions.md item 4 severity mapping and deduplication.
    """
    owns_db = False
    if db is None:
        if isinstance(ctx, dict) and "db" in ctx:
            db = ctx["db"]
        else:
            db = SessionLocal()
            owns_db = True
    checked = 0
    new_alerts = 0
    errors = 0

    try:
        watchlist_items = db.query(Watchlist).all()
        now = datetime.utcnow()

        for item in watchlist_items:
            checked += 1
            norm_addr = item.address
            chain = item.chain

            # Check if address itself is newly sanctioned
            sanctioned = db.query(Label).filter(
                Label.address == norm_addr,
                Label.category.in_(["sanctioned", "Sanctioned"]),
                Label.record_status == "active"
            ).first()

            if sanctioned:
                dedup = f"{norm_addr}:sanctioned:{sanctioned.entity}"
                exists = db.query(Alert).filter(Alert.dedup_key == dedup).first()
                if not exists:
                    alert = Alert(
                        alert_type="SANCTIONED_ENTITY_HIT",
                        severity="Critical",
                        title=f"CRITICAL: Watchlist Wallet Sanctioned - {sanctioned.entity}",
                        message=f"Monitored wallet {norm_addr} matches OFAC sanctioned entity '{sanctioned.entity}'",
                        address=norm_addr,
                        chain=chain,
                        case_id=item.case_id,
                        dedup_key=dedup,
                        status="new"
                    )
                    db.add(alert)
                    new_alerts += 1

            # Check if address moved to a registered or unregistered VASP
            vasp = db.query(Label).filter(
                Label.chain == chain,
                Label.address == norm_addr,
                Label.category.in_(["VASP", "CEX", "vasp"]),
                Label.record_status == "active"
            ).first()

            if vasp:
                dedup = f"{norm_addr}:vasp_transfer:{vasp.entity}"
                exists = db.query(Alert).filter(Alert.dedup_key == dedup).first()
                if not exists:
                    alert = Alert(
                        alert_type="VASP_TRANSFER",
                        severity="High",
                        title=f"HIGH: Monitored Wallet Identified as VASP - {vasp.entity}",
                        message=f"Wallet {norm_addr} is labeled as active VASP {vasp.entity} ({vasp.wallet_type or 'hot'})",
                        address=norm_addr,
                        chain=chain,
                        case_id=item.case_id,
                        dedup_key=dedup,
                        status="new"
                    )
                    db.add(alert)
                    new_alerts += 1

            item.last_checked_at = now

        db.commit()

        MONITOR_METRICS["last_run"] = now.isoformat()
        MONITOR_METRICS["wallets_checked"] = checked
        MONITOR_METRICS["alerts_generated"] += new_alerts

    except Exception as e:
        logger.error(f"Watchlist monitor error: {e}")
        db.rollback()
        errors += 1
        MONITOR_METRICS["errors_count"] += errors
    finally:
        if owns_db:
            db.close()

    return {"checked": checked, "new_alerts": new_alerts, "errors": errors}

async def sync_labels_job(ctx: Optional[dict] = None):
    """Daily label synchronization cron job."""
    from app.labels.sync import LabelSyncService
    db: Session = SessionLocal()
    try:
        summary = LabelSyncService.sync_all(db)
        logger.info(f"Daily label sync completed: {summary}")
    except Exception as e:
        logger.error(f"Daily label sync failed: {e}")
    finally:
        db.close()

async def refresh_prices_job(ctx: Optional[dict] = None):
    """Refreshes cached asset prices periodically."""
    from app.services.pricing import PricingService
    try:
        svc = PricingService()
        prices = await svc.get_bulk_prices(["BTC", "ETH", "SOL", "TRX"])
        logger.info(f"Price cache refreshed: {prices}")
    except Exception as e:
        logger.warning(f"Price refresh warning: {e}")

async def create_audit_checkpoint_job(ctx: Optional[dict] = None):
    """Generates scheduled tamper-evident audit log checkpoint."""
    from app.core.audit import create_audit_checkpoint
    db: Session = SessionLocal()
    try:
        cp = create_audit_checkpoint(db)
        if cp:
            logger.info(f"Audit checkpoint created: ID {cp.id}, Hash: {cp.last_entry_hash[:12]}...")
    except Exception as e:
        logger.error(f"Audit checkpoint job failed: {e}")
    finally:
        db.close()

async def startup(ctx: dict):
    logger.info("ChainNetra arq background worker started. Running startup stuck-job sweep...")
    await sweep_stuck_jobs(ctx)

async def shutdown(ctx: dict):
    logger.info("ChainNetra arq background worker shutting down...")

class WorkerSettings:
    """arq Worker configuration with cron schedules and concurrency controls."""
    functions = [
        run_trace_job,
        sweep_stuck_jobs,
        monitor_watchlist_wallets,
        sync_labels_job,
        refresh_prices_job,
        create_audit_checkpoint_job
    ]
    cron_jobs = [
        cron(monitor_watchlist_wallets, second=0),
        cron(sync_labels_job, hour=2, minute=0),
        cron(refresh_prices_job, minute={0, 15, 30, 45}),
        cron(sweep_stuck_jobs, minute={5, 25, 45}),
        cron(create_audit_checkpoint_job, hour={0, 6, 12, 18}, minute=0)
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 1800  # 30 minutes
    on_startup = startup
    on_shutdown = shutdown
