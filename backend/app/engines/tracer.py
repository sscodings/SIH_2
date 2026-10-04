import heapq
import asyncio
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.adapters.factory import get_chain_adapter
from app.adapters.base import AdapterError, Transfer as AdapterTransfer
from app.engines.taint import TaintModel, WalletTaintLedger
from app.engines.attribution import AttributionEngine
from app.engines.crosschain import CrossChainEngine
from app.engines.mixer import MixerEngine
from app.core.addresses import normalize, display_address, node_key, is_evm_chain
from app.core.service_registry import ServiceRegistry
from app.core.ws import ws_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

CONFIGURED_EVM_CHAINS = ["ethereum", "bsc", "polygon", "arbitrum"]

class TracingEngine:
    def __init__(
        self,
        db: Session,
        case_id: int,
        start_address: str,
        chain: str,
        initial_amount_usd: float,
        start_time: Optional[datetime] = None,
        max_depth: int = 6,
        min_value_usd: float = 50.0,
        max_nodes: int = 400,
        time_window_hours: int = 72,
        taint_model: str = "haircut",
        stop_at_first_vasp: bool = True,
        peel_chain_ratio: float = 0.80,
        follow_mixer_candidates: bool = True,
        max_adapter_calls: int = 250,
        max_trace_seconds: float = 60.0,
        demo_stream_delay_ms: int = 0
    ):
        self.db = db
        self.case_id = case_id
        self.start_address = start_address.strip()
        self.chain = (chain or "tron").lower().strip()
        self.initial_amount_usd = max(initial_amount_usd, 1.0)
        self.start_time = start_time or (datetime.now(timezone.utc) - timedelta(days=2))
        self.max_depth = max_depth
        self.min_value_usd = min_value_usd
        self.max_nodes = max_nodes
        self.time_window_hours = time_window_hours
        self.taint_model = taint_model.lower()
        self.stop_at_first_vasp = stop_at_first_vasp
        self.peel_chain_ratio = peel_chain_ratio
        self.follow_mixer_candidates = follow_mixer_candidates
        self.max_adapter_calls = max_adapter_calls
        self.max_trace_seconds = max_trace_seconds
        self.demo_stream_delay_ms = demo_stream_delay_ms

        # State tracking keyed by composite node_key f"{chain}:{normalized_address}"
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.visited_addresses: Set[str] = set()
        self.ledgers: Dict[str, WalletTaintLedger] = {}
        self.cached_labels: Dict[str, Any] = {}

        self.attributions: List[Dict[str, Any]] = []
        self.dormant_wallets: List[Dict[str, Any]] = []
        self.mixer_events: List[Dict[str, Any]] = []
        self.cross_chain_events: List[Dict[str, Any]] = []
        self.peel_chains_detected: List[Dict[str, Any]] = []
        self.incomplete_branches: List[Dict[str, Any]] = []
        self.first_vasp_found_time: Optional[float] = None  # Wall clock timestamp
        
        # Diagnostics
        self.adapter_call_count: int = 0
        self.adapter_time_seconds: float = 0.0
        self.is_truncated: bool = False
        self.truncation_reason: Optional[str] = None
        self.peel_hop_tracker: Dict[str, List[str]] = {}  # node_key -> sequence of peel addresses

    def _get_or_create_ledger(self, chain: str, address: str) -> WalletTaintLedger:
        nk = node_key(chain, address)
        if nk not in self.ledgers:
            self.ledgers[nk] = TaintModel.create_ledger(address, chain, self.taint_model)
        return self.ledgers[nk]

    async def execute_trace(self, job_id: str, cancel_token: Optional[dict] = None) -> Dict[str, Any]:
        """
        Executes priority-queue First-VASP-Hit search with live event streaming,
        composite (chain, address) keys, stateful taint ledgers, temporal bounds, and verified registry classifications.
        """
        trace_start_tick = time.perf_counter()
        
        # Priority Queue entries: (-tainted_amount, depth, current_chain, current_addr, arrival_time, is_probabilistic, prob_confidence)
        pq = []

        # Determine root chain(s)
        # If bare EVM chain ("evm", "all_evm", "any", "") is submitted, trace on all configured EVM chains as separate roots
        root_chains = [self.chain]
        if self.chain in ("evm", "all_evm", "any", "multi", ""):
            root_chains = CONFIGURED_EVM_CHAINS

        for r_chain in root_chains:
            r_norm = normalize(r_chain, self.start_address)
            r_key = node_key(r_chain, r_norm)
            r_display = display_address(r_chain, self.start_address)

            root_label = await asyncio.to_thread(
                AttributionEngine.resolve_label, self.db, r_norm, r_chain, self.cached_labels
            )
            root_entity_type = "Suspect/Collector"
            if root_label:
                root_entity_type = root_label["category"]

            self.nodes[r_key] = {
                "id": r_key,
                "address": r_display,
                "chain": r_chain,
                "entity_type": root_entity_type,
                "label": root_label["entity"] if root_label else f"Suspect Collector ({r_display[:8]}...)",
                "risk_level": "High",
                "value_usd": self.initial_amount_usd,
                "depth": 0,
                "taint": self.initial_amount_usd,
                "probabilistic": False
            }

            # Initialize root ledger
            r_ledger = self._get_or_create_ledger(r_chain, r_norm)
            r_ledger.add_inflow(
                amount=self.initial_amount_usd,
                tainted_amount=self.initial_amount_usd,
                timestamp=self.start_time,
                tx_hash="root_genesis"
            )

            heapq.heappush(
                pq,
                (-self.initial_amount_usd, 0, r_chain, r_norm, self.start_time, False, 100.0, [r_key])
            )

        # WebSocket emit: start event
        await ws_manager.broadcast_event(
            f"trace:{self.case_id}",
            "trace_started",
            {
                "case_id": self.case_id,
                "job_id": job_id,
                "start_address": self.start_address,
                "chain": self.chain,
                "initial_amount_usd": self.initial_amount_usd,
                "taint_model": self.taint_model
            }
        )

        time_to_vasp_sec = None

        while pq and len(self.nodes) < self.max_nodes:
            # Check cancellation token
            if cancel_token and cancel_token.get("cancelled"):
                self.is_truncated = True
                self.truncation_reason = "cancelled_by_user"
                break

            # Check trace budget limits
            elapsed_current = time.perf_counter() - trace_start_tick
            if elapsed_current > self.max_trace_seconds:
                self.is_truncated = True
                self.truncation_reason = f"max_time_exceeded ({self.max_trace_seconds}s)"
                break

            if self.adapter_call_count >= self.max_adapter_calls:
                self.is_truncated = True
                self.truncation_reason = f"max_adapter_calls_exceeded ({self.max_adapter_calls})"
                break

            neg_taint, depth, current_chain, current_addr, arrival_time, is_probabilistic, branch_confidence, path_history = heapq.heappop(pq)
            current_taint = -neg_taint
            current_node_k = node_key(current_chain, current_addr)

            if current_node_k in self.visited_addresses and depth > 0:
                continue
            self.visited_addresses.add(current_node_k)

            if depth >= self.max_depth:
                continue

            # Calculate temporal window for outgoing transfers
            # Transferred funds must occur on or after arrival_time and within time_window_hours
            since_bound = arrival_time
            until_bound = (arrival_time + timedelta(hours=self.time_window_hours)) if self.time_window_hours > 0 else None

            # Fetch outgoing transfers via adapter
            ad_start = time.perf_counter()
            self.adapter_call_count += 1
            try:
                adapter = get_chain_adapter(current_chain)
                outflows: List[AdapterTransfer] = await adapter.get_transfers(
                    address=current_addr,
                    direction="out",
                    since=since_bound,
                    until=until_bound,
                    limit=100
                )
            except AdapterError as e:
                logger.warning(f"AdapterError during trace for {current_addr} on {current_chain}: {e}")
                self.incomplete_branches.append({
                    "address": current_addr,
                    "chain": current_chain,
                    "reason": str(e),
                    "depth": depth
                })
                continue
            except Exception as e:
                logger.warning(f"Unexpected error during trace for {current_addr} on {current_chain}: {e}")
                self.incomplete_branches.append({
                    "address": current_addr,
                    "chain": current_chain,
                    "reason": str(e),
                    "depth": depth
                })
                continue
            finally:
                self.adapter_time_seconds += (time.perf_counter() - ad_start)

            # Check if this address is a Dormant Holding
            if not outflows:
                try:
                    bal_list = await adapter.get_balance(current_addr)
                    bal = bal_list[0].balance_usd if bal_list else current_taint
                except Exception:
                    bal = current_taint

                if bal >= self.min_value_usd:
                    self.dormant_wallets.append({
                        "address": display_address(current_chain, current_addr),
                        "node_key": current_node_k,
                        "chain": current_chain,
                        "balance_usd": bal,
                        "depth": depth
                    })
                    if current_node_k in self.nodes:
                        self.nodes[current_node_k]["entity_type"] = "Dormant holding (freeze candidate)"
                    await ws_manager.broadcast_event(
                        f"trace:{self.case_id}",
                        "dormant_found",
                        {"address": display_address(current_chain, current_addr), "chain": current_chain, "balance_usd": bal}
                    )
                continue

            # Check Generalized Peel-Chain Pattern:
            # 1 output carrying >= 80% (self.peel_chain_ratio) of value to next fresh wallet, plus 1+ smaller peels
            sorted_transfers = sorted(outflows, key=lambda x: x.amount_usd, reverse=True)
            total_out_val = sum(t.amount_usd for t in outflows)
            is_peel_hop = False
            peel_large_target = None

            if total_out_val > 0 and len(outflows) >= 2:
                top_tx = sorted_transfers[0]
                if (top_tx.amount_usd / total_out_val) >= self.peel_chain_ratio:
                    is_peel_hop = True
                    peel_large_target = top_tx.to_address

            current_seq = path_history
            if is_peel_hop:
                if current_node_k in self.nodes:
                    self.nodes[current_node_k]["entity_type"] = "Peel-chain wallet"

            # Replay outflows through stateful taint ledger
            ledger = self._get_or_create_ledger(current_chain, current_addr)

            for tx in outflows:
                target_addr = tx.to_address
                target_norm = normalize(current_chain, target_addr)
                target_node_k = node_key(current_chain, target_norm)
                target_display = display_address(current_chain, target_addr)

                # Compute propagated taint using stateful ledger
                out_res = ledger.compute_outflow_taint(
                    outflow_amount=tx.amount_usd,
                    timestamp=tx.timestamp,
                    tx_hash=tx.tx_hash
                )
                propagated_taint = out_res.tainted_amount

                if propagated_taint < self.min_value_usd:
                    continue

                # Add Edge
                edge_id = f"{current_node_k}->{target_node_k}:{tx.tx_hash}"
                edge_data = {
                    "id": edge_id,
                    "source": current_node_k,
                    "target": target_node_k,
                    "tx_hash": tx.tx_hash,
                    "amount": tx.amount,
                    "amount_usd": tx.amount_usd,
                    "tainted_usd": round(propagated_taint, 2),
                    "taint_model": self.taint_model,
                    "overestimates": out_res.overestimates,
                    "token": tx.token,
                    "chain": current_chain,
                    "timestamp": tx.timestamp.isoformat(),
                    "is_cross_chain": False,
                    "probabilistic": is_probabilistic
                }
                self.edges.append(edge_data)

                # Check Attribution & Entity Type
                attribution = await asyncio.to_thread(
                    AttributionEngine.resolve_label, self.db, target_norm, current_chain, self.cached_labels
                )
                node_type = "Intermediary (layering)"
                node_label = f"Mule {target_display[:6]}...{target_display[-4:]}"
                risk_lvl = "High"

                is_terminal_vasp = False
                is_mixer_entered = False

                if attribution:
                    node_label = attribution["entity"]
                    cat = attribution["category"].lower()
                    if "vasp" in cat or "exchange" in cat or "otc" in cat or "deposit" in cat:
                        if "deposit" in cat or "vault" in cat:
                            node_type = "VASP deposit address"
                        else:
                            node_type = "VASP hot wallet"
                        risk_lvl = "Low"
                        is_terminal_vasp = True

                        attr_entry = {
                            "vasp_name": attribution["entity"],
                            "vasp_category": attribution["category"],
                            "deposit_address": target_display,
                            "deposit_node_key": target_node_k,
                            "tx_hash": tx.tx_hash,
                            "amount": tx.amount_usd,
                            "timestamp": tx.timestamp.isoformat(),
                            "hops_from_suspect": depth + 1,
                            "confidence_score": attribution["confidence"],
                            "confidence_level": attribution.get("confidence_level", "HIGH"),
                            "evidence_breakdown": attribution["confidence_details"]
                        }
                        self.attributions.append(attr_entry)

                        if not self.first_vasp_found_time:
                            self.first_vasp_found_time = time.perf_counter()
                            time_to_vasp_sec = round(self.first_vasp_found_time - trace_start_tick, 2)

                        await ws_manager.broadcast_event(
                            f"trace:{self.case_id}",
                            "vasp_found",
                            attr_entry
                        )

                    elif "mixer" in cat or "tumbler" in cat or ServiceRegistry.is_mixer(current_chain, target_norm):
                        node_type = "Mixer"
                        risk_lvl = "Critical"
                        is_mixer_entered = True

                        mix_candidates = MixerEngine.match_mixer_pool_withdrawals(
                            self.db, current_chain, target_norm, tx.amount_usd, tx.timestamp
                        )
                        self.mixer_events.append({
                            "mixer_address": target_display,
                            "deposit_amount": tx.amount_usd,
                            "timestamp": tx.timestamp.isoformat(),
                            "candidates": mix_candidates
                        })
                        await ws_manager.broadcast_event(
                            f"trace:{self.case_id}",
                            "mixer_entered",
                            {"mixer_address": target_display, "candidates": mix_candidates}
                        )

                        # If follow_mixer_candidates is active, enqueue probabilistic withdrawal branches
                        if self.follow_mixer_candidates and mix_candidates:
                            for cand in mix_candidates:
                                cand_addr = cand["target_address"]
                                cand_norm = normalize(current_chain, cand_addr)
                                cand_node_k = node_key(current_chain, cand_norm)
                                cand_display = display_address(current_chain, cand_addr)

                                if cand_node_k not in self.nodes:
                                    self.nodes[cand_node_k] = {
                                        "id": cand_node_k,
                                        "address": cand_display,
                                        "chain": current_chain,
                                        "entity_type": "Probabilistic Mixer Withdrawal Candidate",
                                        "label": f"Candidate Cashout ({cand_display[:8]}...)",
                                        "risk_level": "Medium",
                                        "value_usd": cand["withdrawal_amount"],
                                        "depth": depth + 2,
                                        "taint": cand["withdrawal_amount"],
                                        "probabilistic": True,
                                        "probabilistic_confidence": cand["confidence_score"]
                                    }

                                cand_edge = {
                                    "id": f"mixer_cand:{target_node_k}->{cand_node_k}:{cand['tx_hash']}",
                                    "source": target_node_k,
                                    "target": cand_node_k,
                                    "tx_hash": cand["tx_hash"],
                                    "amount": cand["withdrawal_amount"],
                                    "amount_usd": cand["withdrawal_amount"],
                                    "tainted_usd": cand["withdrawal_amount"],
                                    "taint_model": "probabilistic_mixer",
                                    "token": cand["token"],
                                    "chain": current_chain,
                                    "timestamp": cand["timestamp"],
                                    "is_cross_chain": False,
                                    "probabilistic": True,
                                    "confidence": cand["confidence_score"]
                                }
                                self.edges.append(cand_edge)

                                # Enqueue candidate for subsequent exploration with decayed confidence
                                heapq.heappush(
                                    pq,
                                    (
                                        -cand["withdrawal_amount"],
                                        depth + 2,
                                        current_chain,
                                        cand_norm,
                                        datetime.fromisoformat(cand["timestamp"]),
                                        True,
                                        cand["confidence_score"] * 0.85,
                                        path_history + [cand_node_k]
                                    )
                                )

                    elif "bridge" in cat or ServiceRegistry.is_bridge(current_chain, target_norm):
                        node_type = "Bridge contract"
                        risk_lvl = "Medium"

                    elif "dex" in cat or ServiceRegistry.is_dex_router(current_chain, target_norm):
                        node_type = "DEX Router"
                        risk_lvl = "Medium"

                # Check for DEX swaps if router
                if ServiceRegistry.is_dex_router(current_chain, target_norm):
                    swaps = CrossChainEngine.detect_dex_swaps(self.db, current_chain, tx.tx_hash)
                    for sw in swaps:
                        recipient_norm = normalize(current_chain, sw["swap_recipient"])
                        recipient_k = node_key(current_chain, recipient_norm)
                        recipient_display = display_address(current_chain, sw["swap_recipient"])

                        if recipient_k not in self.nodes:
                            self.nodes[recipient_k] = {
                                "id": recipient_k,
                                "address": recipient_display,
                                "chain": current_chain,
                                "entity_type": "DEX Swap Recipient",
                                "label": f"Swap Recipient ({recipient_display[:8]}...)",
                                "risk_level": "High",
                                "value_usd": sw["out_amount_usd"],
                                "depth": depth + 2,
                                "taint": sw["out_amount_usd"],
                                "probabilistic": False
                            }

                        swap_edge = {
                            "id": f"swap:{target_node_k}->{recipient_k}:{tx.tx_hash}",
                            "source": target_node_k,
                            "target": recipient_k,
                            "tx_hash": tx.tx_hash,
                            "amount": sw["out_amount"],
                            "amount_usd": sw["out_amount_usd"],
                            "tainted_usd": sw["out_amount_usd"],
                            "taint_model": "dex_swap",
                            "token": sw["out_token"],
                            "chain": current_chain,
                            "timestamp": tx.timestamp.isoformat(),
                            "is_cross_chain": False,
                            "dex_swap_details": sw
                        }
                        self.edges.append(swap_edge)

                        # Enqueue recipient to continue tracing
                        heapq.heappush(
                            pq,
                            (
                                -sw["out_amount_usd"],
                                depth + 2,
                                current_chain,
                                recipient_norm,
                                tx.timestamp,
                                is_probabilistic,
                                branch_confidence,
                                path_history + [recipient_k]
                            )
                        )

                # Check for Cross-Chain Bridge release on another chain
                if ServiceRegistry.is_bridge(current_chain, target_norm) or "bridge" in node_type.lower():
                    matched_bridge = CrossChainEngine.match_bridge_transfer(
                        self.db,
                        source_chain=current_chain,
                        source_tx_hash=tx.tx_hash,
                        bridge_deposit_address=target_addr,
                        deposit_amount=tx.amount,
                        deposit_time=tx.timestamp,
                        time_window_hours=self.time_window_hours or 12
                    )
                    if matched_bridge:
                        self.cross_chain_events.append(matched_bridge)
                        dest_chain = matched_bridge["destination_chain"]
                        dest_wallet = matched_bridge["destination_wallet"]
                        dest_norm = normalize(dest_chain, dest_wallet)
                        dest_k = node_key(dest_chain, dest_norm)
                        dest_display = display_address(dest_chain, dest_wallet)

                        # Add destination node and cross-chain edge
                        self.nodes[dest_k] = {
                            "id": dest_k,
                            "address": dest_display,
                            "chain": dest_chain,
                            "entity_type": "Intermediary (layering)",
                            "label": f"Bridge Out ({dest_chain.upper()})",
                            "risk_level": "High",
                            "value_usd": matched_bridge["released_amount"],
                            "depth": depth + 2,
                            "taint": matched_bridge["released_amount"],
                            "probabilistic": matched_bridge.get("is_ambiguous", False)
                        }

                        bridge_edge = {
                            "id": f"bridge:{target_node_k}->{dest_k}",
                            "source": target_node_k,
                            "target": dest_k,
                            "tx_hash": matched_bridge["destination_tx_hash"],
                            "amount": matched_bridge["released_amount"],
                            "amount_usd": matched_bridge["released_amount"],
                            "tainted_usd": matched_bridge["released_amount"],
                            "taint_model": "cross_chain_bridge",
                            "token": matched_bridge["token"],
                            "chain": dest_chain,
                            "timestamp": tx.timestamp.isoformat(),
                            "is_cross_chain": True,
                            "confidence": matched_bridge["confidence"],
                            "is_ambiguous": matched_bridge.get("is_ambiguous", False)
                        }
                        self.edges.append(bridge_edge)

                        await ws_manager.broadcast_event(
                            f"trace:{self.case_id}",
                            "bridge_detected",
                            matched_bridge
                        )

                        # Enqueue destination address for further exploration on dest_chain
                        dest_ledger = self._get_or_create_ledger(dest_chain, dest_norm)
                        dest_ledger.add_inflow(
                            amount=matched_bridge["released_amount"],
                            tainted_amount=matched_bridge["released_amount"],
                            timestamp=tx.timestamp,
                            tx_hash=matched_bridge["destination_tx_hash"]
                        )
                        heapq.heappush(
                            pq,
                            (
                                -matched_bridge["released_amount"],
                                depth + 2,
                                dest_chain,
                                dest_norm,
                                tx.timestamp,
                                matched_bridge.get("is_ambiguous", False),
                                matched_bridge["confidence"],
                                path_history + [dest_k]
                            )
                        )

                # Add target node if not present
                if target_node_k not in self.nodes:
                    self.nodes[target_node_k] = {
                        "id": target_node_k,
                        "address": target_display,
                        "chain": current_chain,
                        "entity_type": node_type,
                        "label": node_label,
                        "risk_level": risk_lvl,
                        "value_usd": tx.amount_usd,
                        "depth": depth + 1,
                        "taint": round(propagated_taint, 2),
                        "probabilistic": is_probabilistic
                    }

                    # Emit hop_discovered event
                    await ws_manager.broadcast_event(
                        f"trace:{self.case_id}",
                        "hop_discovered",
                        {
                            "node": self.nodes[target_node_k],
                            "edge": edge_data,
                            "depth": depth + 1,
                            "narration": f"Funds traced to {target_display[:8]}... (${tx.amount_usd:,.2f} {tx.token}) [{node_type}]"
                        }
                    )

                    if self.demo_stream_delay_ms > 0:
                        await asyncio.sleep(self.demo_stream_delay_ms / 1000.0)

                # Update target ledger with incoming tainted funds
                target_ledger = self._get_or_create_ledger(current_chain, target_norm)
                target_ledger.add_inflow(
                    amount=tx.amount_usd,
                    tainted_amount=propagated_taint,
                    timestamp=tx.timestamp,
                    tx_hash=tx.tx_hash
                )

                # Track peel chain sequence length
                next_path = path_history + [target_node_k]
                if is_peel_hop and peel_large_target and normalize(current_chain, peel_large_target) == target_norm:
                    # Continuing along peel chain
                    if len(next_path) >= 4:  # 3 consecutive hops from root = 4 nodes in path
                        # Check if already recorded
                        peel_entry = {
                            "chain": current_chain,
                            "hops": len(next_path) - 1,
                            "wallets": [display_address(current_chain, k.split(":", 1)[1] if ":" in k else k) for k in next_path],
                            "evidence": f"Generalized peel chain with {len(next_path)-1} consecutive hops (>= {int(self.peel_chain_ratio*100)}% dominant output per hop)"
                        }
                        if not any(p["wallets"] == peel_entry["wallets"] for p in self.peel_chains_detected):
                            self.peel_chains_detected.append(peel_entry)

                # Stop exploration on this branch if terminal VASP reached and stop_at_first_vasp is active
                if is_terminal_vasp and self.stop_at_first_vasp:
                    continue

                # Stop deterministic exploration if entered mixer pool (candidates handled separately above)
                if is_mixer_entered:
                    continue

                # Push to Priority Queue to continue tracing
                heapq.heappush(
                    pq,
                    (
                        -propagated_taint,
                        depth + 1,
                        current_chain,
                        target_norm,
                        tx.timestamp,
                        is_probabilistic,
                        branch_confidence,
                        next_path
                    )
                )

        # Trace Complete Timing: measured purely via wall-clock timer
        elapsed = round(time.perf_counter() - trace_start_tick, 2)

        # Compute funds accounting status
        total_traced = self.initial_amount_usd
        vasp_total = sum(a["amount"] for a in self.attributions)
        mixer_total = sum(m["deposit_amount"] for m in self.mixer_events)
        dormant_total = sum(d["balance_usd"] for d in self.dormant_wallets)
        
        sum_attributed = vasp_total + mixer_total + dormant_total
        over_attributed_usd = max(0.0, sum_attributed - total_traced)
        unaccounted = max(0.0, total_traced - sum_attributed) if over_attributed_usd == 0.0 else 0.0

        summary = {
            "case_id": self.case_id,
            "job_id": job_id,
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "attributions": self.attributions,
            "dormant_wallets": self.dormant_wallets,
            "mixer_events": self.mixer_events,
            "cross_chain_events": self.cross_chain_events,
            "peel_chains": self.peel_chains_detected,
            "incomplete_branches": self.incomplete_branches,
            "is_complete": len(self.incomplete_branches) == 0 and not self.is_truncated,
            "truncated": self.is_truncated,
            "truncation_reason": self.truncation_reason,
            "time_to_vasp_seconds": time_to_vasp_sec,  # None if no VASP found, never fallback to total elapsed
            "elapsed_seconds": elapsed,
            "adapter_call_count": self.adapter_call_count,
            "adapter_time_seconds": round(self.adapter_time_seconds, 2),
            "funds_status": {
                "total_traced_usd": round(total_traced, 2),
                "vasp_amount_usd": round(vasp_total, 2),
                "mixer_amount_usd": round(mixer_total, 2),
                "dormant_amount_usd": round(dormant_total, 2),
                "unaccounted_usd": round(unaccounted, 2),
                "over_attributed_usd": round(over_attributed_usd, 2),
                "has_accounting_error": over_attributed_usd > 0.0
            }
        }

        await ws_manager.broadcast_event(
            f"trace:{self.case_id}",
            "trace_complete",
            summary
        )

        return summary
