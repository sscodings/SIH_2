from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.db.models import Transfer

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
        Mixer results are explicitly flagged as probabilistic with caveats.
        """
        start_time = deposit_time
        end_time = deposit_time + timedelta(hours=window_hours)

        # Standard mixer denominations or tolerance
        outflows = db.query(Transfer).filter(
            Transfer.chain == chain,
            Transfer.from_address.ilike(mixer_address),
            Transfer.timestamp >= start_time,
            Transfer.timestamp <= end_time
        ).order_by(Transfer.timestamp.asc()).all()

        results = []
        for out in outflows:
            # Check round denominations or close amounts
            amt_diff = abs(out.amount - deposit_amount)
            pct_diff = amt_diff / max(deposit_amount, 0.0001)

            # Mixer fee usually 0.5% - 5%
            if pct_diff <= 0.10 or out.amount in [0.1, 1.0, 10.0, 100.0, 1000.0, 5000.0]:
                score = round(max(20.0, 65.0 - (pct_diff * 100.0)), 1)
                results.append({
                    "tx_hash": out.tx_hash,
                    "target_address": out.to_address,
                    "withdrawal_amount": out.amount,
                    "token": out.token,
                    "timestamp": out.timestamp.isoformat(),
                    "time_delta_minutes": int((out.timestamp - deposit_time).total_seconds() / 60),
                    "confidence_score": score,
                    "confidence_level": "LOW_PROBABILISTIC",
                    "caveat": "Mixer transactions break deterministic link. This continuation represents a candidate withdrawal based on amount and timing correlation only."
                })

        # Rank candidates by score
        results.sort(key=lambda x: x["confidence_score"], reverse=True)
        return results[:5]
