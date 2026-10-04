from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Transfer
from app.core.service_registry import ServiceRegistry
from app.core.addresses import normalize

class MixerEngine:
    @staticmethod
    def match_mixer_pool_withdrawals(
        db: Session,
        chain: str,
        mixer_address: str,
        deposit_amount: float,
        deposit_time: datetime,
        window_hours: int = 48
    ) -> List[Dict[str, Any]]:
        """
        Probabilistic amount-and-time matcher for mixer withdrawals.
        Only runs when mixer_address is registered in ServiceRegistry.
        Uses per-mixer denomination lists and caps confidence strictly at probabilistic levels (<= 40%).
        """
        chain = chain.lower()
        norm_mixer = normalize(chain, mixer_address)
        mixer_entry = ServiceRegistry.lookup(chain, norm_mixer)
        if not mixer_entry or mixer_entry.kind != "mixer":
            return []

        start_time = deposit_time
        end_time = deposit_time + timedelta(hours=window_hours)

        outflows = db.query(Transfer).filter(
            Transfer.chain == chain,
            Transfer.from_address == norm_mixer,
            Transfer.timestamp >= start_time,
            Transfer.timestamp <= end_time
        ).order_by(Transfer.timestamp.asc()).limit(100).all()

        results = []
        mixer_denominations = mixer_entry.denominations or [0.1, 0.5, 1.0, 5.0, 10.0, 100.0]

        for out in outflows:
            amt_diff = abs(out.amount - deposit_amount)
            pct_diff = amt_diff / max(deposit_amount, 0.0001)

            # Match either close percentage amount (deducting mixer fee) or matching standard pool denomination
            matches_denomination = any(abs(out.amount - d) < 0.001 for d in mixer_denominations)
            is_close_amount = pct_diff <= 0.10

            if is_close_amount or matches_denomination:
                # Confidence is strictly capped at 40.0% for any mixer continuation
                base_score = 35.0 if matches_denomination else 30.0
                decay = min(15.0, pct_diff * 100.0)
                score = round(min(40.0, max(10.0, base_score - decay)), 1)

                out_ts = out.timestamp.replace(tzinfo=timezone.utc if out.timestamp.tzinfo is None else out.timestamp.tzinfo)
                dep_ts = deposit_time.replace(tzinfo=timezone.utc if deposit_time.tzinfo is None else deposit_time.tzinfo)
                time_delta_mins = int(abs((out_ts - dep_ts).total_seconds()) / 60)

                results.append({
                    "tx_hash": out.tx_hash,
                    "target_address": out.to_address,
                    "withdrawal_amount": out.amount,
                    "token": out.token,
                    "chain": chain,
                    "timestamp": out.timestamp.isoformat(),
                    "time_delta_minutes": time_delta_mins,
                    "confidence_score": score,
                    "confidence_level": "LOW_PROBABILISTIC",
                    "probabilistic": True,
                    "mixer_name": mixer_entry.name,
                    "caveat": "Mixer zero-knowledge pool breaks cryptographic ledger links. This candidate represents an unverified heuristic correlation only."
                })

        # Rank candidates by score and return top-5
        results.sort(key=lambda x: x["confidence_score"], reverse=True)
        return results[:5]
