import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import Transfer, Label
from app.core.service_registry import ServiceRegistry
from app.core.addresses import normalize

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
        Only runs when bridge_deposit_address is a verified bridge in ServiceRegistry.
        If two candidates score within 5 points, returns ambiguous results honestly.
        """
        source_chain = source_chain.lower()
        bridge_entry = ServiceRegistry.lookup(source_chain, bridge_deposit_address)
        if not bridge_entry or bridge_entry.kind != "bridge":
            # Unregistered address; never trigger heuristic bridge matching
            return None

        # Determine eligible release addresses from bridge configuration
        release_addrs_map = bridge_entry.release_addresses  # dest_chain -> release_address

        min_amount = deposit_amount * (1.0 - fee_tolerance_pct)
        max_amount = deposit_amount * (1.0 + fee_tolerance_pct)
        start_time = deposit_time
        end_time = deposit_time + timedelta(hours=time_window_hours)

        query = db.query(Transfer).filter(
            Transfer.chain != source_chain,
            Transfer.timestamp >= start_time,
            Transfer.timestamp <= end_time,
            Transfer.amount >= min_amount,
            Transfer.amount <= max_amount
        )

        # Filter to registered release addresses if configured
        if release_addrs_map:
            # Match destination chain and release address
            candidates = []
            all_cands = query.all()
            for cand in all_cands:
                expected_rel = release_addrs_map.get(cand.chain.lower())
                if expected_rel:
                    cand_from_norm = normalize(cand.chain, cand.from_address)
                    exp_norm = normalize(cand.chain, expected_rel)
                    if cand_from_norm == exp_norm:
                        candidates.append(cand)
                else:
                    # If dest_chain not restricted, include if it matches contract call
                    if cand.is_contract_call:
                        candidates.append(cand)
        else:
            candidates = query.all()

        if not candidates:
            return None

        scored_candidates = []
        num_candidates = len(candidates)

        for cand in candidates:
            # 1. Amount match score (0 to 1)
            amt_diff_ratio = abs(cand.amount - deposit_amount) / max(deposit_amount, 0.001)
            amt_score = max(0.0, 1.0 - (amt_diff_ratio / fee_tolerance_pct))

            # 2. Time proximity score (0 to 1)
            cand_ts = cand.timestamp.replace(tzinfo=timezone.utc if cand.timestamp.tzinfo is None else cand.timestamp.tzinfo)
            dep_ts = deposit_time.replace(tzinfo=timezone.utc if deposit_time.tzinfo is None else deposit_time.tzinfo)
            seconds_diff = abs((cand_ts - dep_ts).total_seconds())
            time_score = max(0.0, 1.0 - (seconds_diff / (time_window_hours * 3600)))

            # 3. Uniqueness score: computed dynamically from candidate count
            # Uniqueness decays with more competing candidates in the same window
            uniqueness_score = 1.0 / math.sqrt(num_candidates)

            composite_score = round((0.50 * amt_score + 0.30 * time_score + 0.20 * uniqueness_score) * 100, 1)

            cand_dict = {
                "source_chain": source_chain,
                "source_tx_hash": source_tx_hash,
                "destination_chain": cand.chain,
                "destination_tx_hash": cand.tx_hash,
                "bridge_address": bridge_deposit_address,
                "bridge_name": bridge_entry.name,
                "destination_wallet": cand.to_address,
                "release_contract": cand.from_address,
                "deposit_amount": deposit_amount,
                "released_amount": cand.amount,
                "token": cand.token,
                "time_delta_seconds": int(seconds_diff),
                "confidence": composite_score,
                "candidate_count": num_candidates,
                "is_ambiguous": False,
                "evidence": f"Cross-chain bridge match ({bridge_entry.name}) from {source_chain.upper()} to {cand.chain.upper()} ({composite_score}% confidence, {num_candidates} candidate(s))"
            }
            scored_candidates.append((composite_score, cand_dict))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        if not scored_candidates or scored_candidates[0][0] < 50.0:
            return None

        # Check for ambiguity: if second candidate is within 5.0 score points
        if len(scored_candidates) > 1:
            top_score = scored_candidates[0][0]
            second_score = scored_candidates[1][0]
            if (top_score - second_score) <= 5.0:
                # Ambiguous: flag result as ambiguous and return candidate details
                res = scored_candidates[0][1]
                res["is_ambiguous"] = True
                res["competing_candidates"] = [c[1] for c in scored_candidates[:3]]
                res["evidence"] += " [AMBIGUOUS: Multiple competing bridge release candidates within 5 score points]"
                return res

        return scored_candidates[0][1]

    @staticmethod
    def detect_dex_swaps(db: Session, chain: str, tx_hash: str) -> List[Dict[str, Any]]:
        """
        Parses DEX router swaps by grouping transfers within the same tx_hash by log_index.
        Identifies token in (to router) and token out (from router/pair to recipient).
        """
        chain = chain.lower()
        transfers = db.query(Transfer).filter(
            Transfer.chain == chain,
            Transfer.tx_hash == tx_hash
        ).order_by(Transfer.log_index.asc(), Transfer.timestamp.asc()).all()

        if len(transfers) < 2:
            return []

        # Find if any transfer involves a registered DEX router
        swaps = []
        for i in range(len(transfers) - 1):
            t_in = transfers[i]
            t_out = transfers[i + 1]

            # Check if t_in goes to a registered router or t_out comes from router/pool
            router_entry = ServiceRegistry.lookup(chain, t_in.to_address) or ServiceRegistry.lookup(chain, t_out.from_address)
            if router_entry and router_entry.kind == "dex_router":
                swaps.append({
                    "chain": chain,
                    "tx_hash": tx_hash,
                    "router_name": router_entry.name,
                    "router_address": router_entry.address,
                    "user_address": t_in.from_address,
                    "swap_recipient": t_out.to_address,
                    "in_token": t_in.token,
                    "in_amount": t_in.amount,
                    "in_amount_usd": t_in.amount_usd,
                    "out_token": t_out.token,
                    "out_amount": t_out.amount,
                    "out_amount_usd": t_out.amount_usd,
                    "in_log_index": t_in.log_index,
                    "out_log_index": t_out.log_index
                })

        return swaps
