import argparse
import asyncio
import logging
from datetime import datetime, timezone
from app.db.database import SessionLocal
from app.labels.ofac import OfacLabelSource
from app.labels.fiu import FiuVaspService
from app.labels.exchange_csv import ExchangeCsvLabelSource
from app.labels.service import LabelService
from app.adapters.factory import get_chain_adapter
from app.adapters.base import AdapterError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("chainnetra.labels.sync")

async def verify_address_activity(chain: str, address: str) -> str:
    """Verifies recent activity of an address using adapters."""
    try:
        adapter = get_chain_adapter(chain)
        transfers = await adapter.get_transfers(address, limit=5)
        if transfers and len(transfers) > 0:
            latest_time = max(t.timestamp for t in transfers)
            days_ago = (datetime.now(timezone.utc) - latest_time.replace(tzinfo=timezone.utc if latest_time.tzinfo is None else latest_time.tzinfo)).days
            if days_ago <= 180:
                return "active_recently"
            else:
                return f"inactive_since_{latest_time.strftime('%Y-%m-%d')}"
        return "inactive_since_unknown"
    except Exception as e:
        logger.warning(f"Could not verify activity for {address} on {chain}: {e}")
        return "unverified"

async def run_sync(source: str, verify: bool = False):
    db = SessionLocal()
    try:
        sources_to_run = [source.lower()] if source.lower() != "all" else ["ofac", "fiu", "exchange_csv"]
        
        for src in sources_to_run:
            if src in ("ofac", "ofac_sdn"):
                logger.info("Syncing OFAC SDN Advanced XML labels...")
                ofac = OfacLabelSource()
                records = ofac.fetch()
                res = LabelService.save_records(db, records)
                logger.info(f"OFAC Sync completed: Added {res['added']}, Updated {res['updated']}")

            elif src in ("fiu", "fiu_vasp"):
                logger.info("Syncing FIU-IND VASP entities...")
                loaded = FiuVaspService.load_fiu_vasp_list(db)
                logger.info(f"FIU-IND VASP Sync completed: {loaded} entities loaded")

            elif src in ("exchange_csv", "exchanges"):
                logger.info("Syncing Exchange CSV labels...")
                ex_src = ExchangeCsvLabelSource()
                records = ex_src.fetch()

                if verify:
                    logger.info("Verifying recent on-chain activity for exchange addresses...")
                    for r in records:
                        if r.record_status == "active":
                            act_status = await verify_address_activity(r.chain, r.address)
                            if act_status.startswith("inactive"):
                                r.record_status = "inactive"
                                r.raw_wallet_type = f"{r.raw_wallet_type or ''} (verified: {act_status})"
                            elif act_status == "active_recently":
                                r.raw_wallet_type = f"{r.raw_wallet_type or ''} (verified: active_recently)"

                res = LabelService.save_records(db, records)
                logger.info(f"Exchange CSV Sync completed: Added {res['added']}, Updated {res['updated']}")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChainNetra Label Ingestion CLI")
    parser.add_argument("--source", type=str, default="all", choices=["ofac", "fiu", "exchange_csv", "all"], help="Label source to sync")
    parser.add_argument("--verify", action="store_true", help="Verify on-chain activity via blockchain adapters")
    args = parser.parse_args()

    asyncio.run(run_sync(args.source, verify=args.verify))
