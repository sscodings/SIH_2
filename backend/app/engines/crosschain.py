import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.db.models import Transfer, Label

class CrossChainEngine:
    @staticmethod
    def match_bridge_transfer(
        db: Session,
        source_chain: str,
        source_tx_hash: str,
        bridge_deposit_address: str,
        deposit_amount: float,
        deposit_time: datetime,
        time_window_hours: int = 12,
        fee_tolerance_pct: float = 0.05
    ) -> Optional[Dict[str, Any]]:
        """
        Matches a bridge deposit on source_chain to a release on destination chains.
        Match score = 0.5 * amount_match + 0.3 * time_proximity + 0.2 * uniqueness.
        """
        # Find candidate releases across all other chains around this time window
        min_amount = deposit_amount * (1.0 - fee_tolerance_pct)
        max_amount = deposit_amount * (1.0 + fee_tolerance_pct)
        start_time = deposit_time
        end_time = deposit_time + timedelta(hours=time_window_hours)

        candidates = db.query(Transfer).filter(
            Transfer.chain != source_chain,
            Transfer.timestamp >= start_time,
            Transfer.timestamp <= end_time,
            Transfer.amount >= min_amount,
            Transfer.amount <= max_amount
        ).all()

        if not candidates:
            return None

        # Score candidates
        best_candidate = None
        highest_score = 0.0

        for cand in candidates:
            # 1. Amount match score (0 to 1)
            amt_diff_ratio = abs(cand.amount - deposit_amount) / max(deposit_amount, 0.001)
            amt_score = max(0.0, 1.0 - (amt_diff_ratio / fee_tolerance_pct))

            # 2. Time proximity score (0 to 1)
            seconds_diff = (cand.timestamp - deposit_time).total_seconds()
            time_score = max(0.0, 1.0 - (seconds_diff / (time_window_hours * 3600)))

            # 3. Uniqueness score
            uniqueness_score = 1.0 if len(candidates) == 1 else 0.8

            composite_score = round((0.5 * amt_score + 0.3 * time_score + 0.2 * uniqueness_score) * 100, 1)

            if composite_score > highest_score:
                highest_score = composite_score
                best_candidate = {
                    "source_chain": source_chain,
                    "source_tx_hash": source_tx_hash,
                    "destination_chain": cand.chain,
                    "destination_tx_hash": cand.tx_hash,
                    "bridge_address": bridge_deposit_address,
                    "destination_wallet": cand.to_address,
                    "deposit_amount": deposit_amount,
                    "released_amount": cand.amount,
                    "token": cand.token,
                    "time_delta_seconds": int(seconds_diff),
                    "confidence": highest_score,
                    "evidence": f"Cross-chain bridge match between {source_chain.upper()} and {cand.chain.upper()} ({highest_score}% confidence)"
                }

        return best_candidate if highest_score >= 60.0 else None

    @staticmethod
    def detect_dex_swaps(db: Session, chain: str, tx_hash: str) -> List[Dict[str, Any]]:
        """
        Parses DEX router swaps by matching paired transfers within the same transaction hash.
        """
        transfers = db.query(Transfer).filter(
            Transfer.chain == chain,
            Transfer.tx_hash == tx_hash
        ).all()

        if len(transfers) >= 2:
            return [{
                "chain": chain,
                "tx_hash": tx_hash,
                "in_token": transfers[0].token,
                "in_amount": transfers[0].amount,
                "out_token": transfers[1].token,
                "out_amount": transfers[1].amount,
                "router": transfers[0].to_address,
                "user": transfers[0].from_address,
                "swap_target": transfers[1].to_address
            }]
        return []
