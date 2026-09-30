import heapq
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session
from backend.app.adapters.factory import get_chain_adapter
from backend.app.engines.taint import TaintModel
from backend.app.engines.attribution import AttributionEngine
from backend.app.engines.crosschain import CrossChainEngine
from backend.app.engines.mixer import MixerEngine
from backend.app.core.ws import ws_manager

logger = logging.getLogger(__name__)

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
        stop_at_first_vasp: bool = True
    ):
        self.db = db
        self.case_id = case_id
        self.start_address = start_address.strip()
        self.chain = chain.lower()
        self.initial_amount_usd = max(initial_amount_usd, 1.0)
        self.start_time = start_time or datetime.utcnow() - timedelta(days=2)
        self.max_depth = max_depth
        self.min_value_usd = min_value_usd
        self.max_nodes = max_nodes
        self.time_window_hours = time_window_hours
        self.taint_model = taint_model.lower()
        self.stop_at_first_vasp = stop_at_first_vasp

        # State tracking
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.visited_addresses: Set[str] = set()
        self.attributions: List[Dict[str, Any]] = []
        self.dormant_wallets: List[Dict[str, Any]] = []
        self.mixer_events: List[Dict[str, Any]] = []
        self.cross_chain_events: List[Dict[str, Any]] = []
        self.peel_chains_detected: List[Dict[str, Any]] = []
        self.first_vasp_found_time: Optional[datetime] = None

    async def execute_trace(self, job_id: str, cancel_token: Optional[dict] = None) -> Dict[str, Any]:
        """
        Executes priority-queue First-VASP-Hit search with live event streaming.
        Priority queue orders exploration by highest tainted value.
        """
        # Initialize start node (Victim / Suspect collector)
        root_label = AttributionEngine.resolve_label(self.db, self.start_address, self.chain)
        root_entity_type = "Suspect/Collector"
        if root_label:
            root_entity_type = root_label["category"]

        self.nodes[self.start_address.lower()] = {
            "id": self.start_address.lower(),
            "address": self.start_address,
            "chain": self.chain,
            "entity_type": root_entity_type,
            "label": root_label["entity"] if root_label else "Suspect Collector Wallet",
            "risk_level": "High",
            "value_usd": self.initial_amount_usd,
            "depth": 0,
            "taint": self.initial_amount_usd
        }

        # WebSocket emit: start event
        await ws_manager.broadcast_event(
            f"trace:{self.case_id}",
            "trace_started",
            {
                "case_id": self.case_id,
                "job_id": job_id,
                "start_address": self.start_address,
                "chain": self.chain,
                "initial_amount_usd": self.initial_amount_usd
            }
        )

        # Priority Queue entries: (-tainted_amount, depth, address, chain, current_time)
        pq = []
        heapq.heappush(pq, (-self.initial_amount_usd, 0, self.start_address, self.chain, self.start_time))

        time_to_vasp_sec = None
        trace_start_tick = datetime.utcnow()

        while pq and len(self.nodes) < self.max_nodes:
            if cancel_token and cancel_token.get("cancelled"):
                break

            neg_taint, depth, current_addr, current_chain, arrival_time = heapq.heappop(pq)
            current_taint = -neg_taint
            current_addr_lower = current_addr.lower()

            if current_addr_lower in self.visited_addresses and depth > 0:
                continue
            self.visited_addresses.add(current_addr_lower)

            if depth >= self.max_depth:
                continue

            # Fetch outgoing transfers from this address
            adapter = get_chain_adapter(current_chain)
            outflows = await adapter.get_transfers(
                address=current_addr,
                direction="out",
                since=arrival_time,
                limit=100
            )

            # Check if this address is a Dormant Holding (has incoming funds, zero outflows or balance >= min_value)
            if not outflows:
                bal_list = await adapter.get_balance(current_addr)
                bal = bal_list[0].balance_usd if bal_list else current_taint
                if bal >= self.min_value_usd:
                    self.dormant_wallets.append({
                        "address": current_addr,
                        "chain": current_chain,
                        "balance_usd": bal,
                        "depth": depth
                    })
                    if current_addr_lower in self.nodes:
                        self.nodes[current_addr_lower]["entity_type"] = "Dormant holding (freeze candidate)"
                    await ws_manager.broadcast_event(
                        f"trace:{self.case_id}",
                        "dormant_found",
                        {"address": current_addr, "chain": current_chain, "balance_usd": bal}
                    )
                continue

            # Check for Peel-Chain Pattern (1 large continuing output + 1 small peel)
            if len(outflows) == 2:
                sorted_transfers = sorted(outflows, key=lambda x: x.amount_usd, reverse=True)
                if sorted_transfers[0].amount_usd > sorted_transfers[1].amount_usd * 3.0:
                    self.peel_chains_detected.append({
                        "parent": current_addr,
                        "large_target": sorted_transfers[0].to_address,
                        "peel_target": sorted_transfers[1].to_address,
                        "chain": current_chain
                    })
                    if current_addr_lower in self.nodes:
                        self.nodes[current_addr_lower]["entity_type"] = "Peel-chain wallet"

            # Process outgoing transfers
            total_wallet_inflow = sum(t.amount_usd for t in outflows)
            for tx in outflows:
                target_addr = tx.to_address
                target_lower = target_addr.lower()

                # Calculate propagated taint value using chosen model
                propagated_taint = TaintModel.calculate_taint(
                    model_name=self.taint_model,
                    inflow_tainted_amount=current_taint,
                    total_wallet_inflow=max(total_wallet_inflow, current_taint),
                    outflow_amount=tx.amount_usd
                )

                if propagated_taint < self.min_value_usd:
                    continue

                # Add Edge
                edge_id = f"{current_addr_lower}->{target_lower}:{tx.tx_hash}"
                edge_data = {
                    "id": edge_id,
                    "source": current_addr_lower,
                    "target": target_lower,
                    "tx_hash": tx.tx_hash,
                    "amount": tx.amount,
                    "amount_usd": tx.amount_usd,
                    "tainted_usd": round(propagated_taint, 2),
                    "token": tx.token,
                    "chain": current_chain,
                    "timestamp": tx.timestamp.isoformat(),
                    "is_cross_chain": False
                }
                self.edges.append(edge_data)

                # Check Attribution & Entity Type
                attribution = AttributionEngine.resolve_label(self.db, target_addr, current_chain)
                node_type = "Intermediary (layering)"
                node_label = f"Mule {target_addr[:6]}...{target_addr[-4:]}"
                risk_lvl = "High"

                is_terminal_vasp = False
                if attribution:
                    node_label = attribution["entity"]
                    cat = attribution["category"].lower()
                    if "vasp" in cat or "exchange" in cat or "otc" in cat or "deposit" in cat:
                        node_type = "VASP deposit address" if "deposit" in cat else "VASP hot wallet"
                        risk_lvl = "Low"
                        is_terminal_vasp = True

                        attr_entry = {
                            "vasp_name": attribution["entity"],
                            "vasp_category": attribution["category"],
                            "deposit_address": target_addr,
                            "tx_hash": tx.tx_hash,
                            "amount": tx.amount_usd,
                            "timestamp": tx.timestamp.isoformat(),
                            "hops_from_suspect": depth + 1,
                            "confidence_score": attribution["confidence"],
                            "evidence_breakdown": attribution["confidence_details"]
                        }
                        self.attributions.append(attr_entry)

                        if not self.first_vasp_found_time:
                            self.first_vasp_found_time = datetime.utcnow()
                            time_to_vasp_sec = round((self.first_vasp_found_time - trace_start_tick).total_seconds(), 2)

                        await ws_manager.broadcast_event(
                            f"trace:{self.case_id}",
                            "vasp_found",
                            attr_entry
                        )

                    elif "mixer" in cat or "tumbler" in cat:
                        node_type = "Mixer"
                        risk_lvl = "Critical"
                        mix_candidates = MixerEngine.match_mixer_pool_withdrawals(
                            self.db, current_chain, target_addr, tx.amount_usd, tx.timestamp
                        )
                        self.mixer_events.append({
                            "mixer_address": target_addr,
                            "deposit_amount": tx.amount_usd,
                            "timestamp": tx.timestamp.isoformat(),
                            "candidates": mix_candidates
                        })
                        await ws_manager.broadcast_event(
                            f"trace:{self.case_id}",
                            "mixer_entered",
                            {"mixer_address": target_addr, "candidates": mix_candidates}
                        )

                    elif "bridge" in cat:
                        node_type = "Bridge contract"
                        risk_lvl = "Medium"

                # Check for Cross-Chain Bridge release on another chain
                if "bridge" in node_type.lower() or "bridge" in target_lower or tx.is_contract_call:
                    matched_bridge = CrossChainEngine.match_bridge_transfer(
                        self.db,
                        source_chain=current_chain,
                        source_tx_hash=tx.tx_hash,
                        bridge_deposit_address=target_addr,
                        deposit_amount=tx.amount,
                        deposit_time=tx.timestamp
                    )
                    if matched_bridge:
                        self.cross_chain_events.append(matched_bridge)
                        dest_chain = matched_bridge["destination_chain"]
                        dest_wallet = matched_bridge["destination_wallet"]
                        dest_lower = dest_wallet.lower()

                        # Add destination node and cross-chain edge
                        self.nodes[dest_lower] = {
                            "id": dest_lower,
                            "address": dest_wallet,
                            "chain": dest_chain,
                            "entity_type": "Intermediary (layering)",
                            "label": f"Bridge Out ({dest_chain.upper()})",
                            "risk_level": "High",
                            "value_usd": matched_bridge["released_amount"],
                            "depth": depth + 2,
                            "taint": matched_bridge["released_amount"]
                        }

                        bridge_edge = {
                            "id": f"bridge:{target_lower}->{dest_lower}",
                            "source": target_lower,
                            "target": dest_lower,
                            "tx_hash": matched_bridge["destination_tx_hash"],
                            "amount": matched_bridge["released_amount"],
                            "amount_usd": matched_bridge["released_amount"],
                            "tainted_usd": matched_bridge["released_amount"],
                            "token": matched_bridge["token"],
                            "chain": dest_chain,
                            "timestamp": tx.timestamp.isoformat(),
                            "is_cross_chain": True,
                            "confidence": matched_bridge["confidence"]
                        }
                        self.edges.append(bridge_edge)

                        await ws_manager.broadcast_event(
                            f"trace:{self.case_id}",
                            "bridge_detected",
                            matched_bridge
                        )

                        # Enqueue destination address for further exploration on dest_chain
                        heapq.heappush(
                            pq,
                            (-matched_bridge["released_amount"], depth + 2, dest_wallet, dest_chain, tx.timestamp)
                        )

                # Add target node if not present
                if target_lower not in self.nodes:
                    self.nodes[target_lower] = {
                        "id": target_lower,
                        "address": target_addr,
                        "chain": current_chain,
                        "entity_type": node_type,
                        "label": node_label,
                        "risk_level": risk_lvl,
                        "value_usd": tx.amount_usd,
                        "depth": depth + 1,
                        "taint": round(propagated_taint, 2)
                    }

                    # Emit hop_discovered event
                    await ws_manager.broadcast_event(
                        f"trace:{self.case_id}",
                        "hop_discovered",
                        {
                            "node": self.nodes[target_lower],
                            "edge": edge_data,
                            "depth": depth + 1,
                            "narration": f"Funds traced to {target_addr[:8]}... (${tx.amount_usd:,.2f} {tx.token}) [{node_type}]"
                        }
                    )
                    await asyncio.sleep(0.04) # brief yield for real-time streaming effect

                # Stop exploration on this branch if terminal VASP reached and stop_at_first_vasp is active
                if is_terminal_vasp and self.stop_at_first_vasp:
                    continue

                # Push to Priority Queue to continue tracing
                heapq.heappush(
                    pq,
                    (-propagated_taint, depth + 1, target_addr, current_chain, tx.timestamp)
                )

        # Trace Complete
        elapsed = round((datetime.utcnow() - trace_start_tick).total_seconds(), 2)

        # Compute funds status
        total_traced = self.initial_amount_usd
        vasp_total = sum(a["amount"] for a in self.attributions)
        mixer_total = sum(m["deposit_amount"] for m in self.mixer_events)
        dormant_total = sum(d["balance_usd"] for d in self.dormant_wallets)
        unaccounted = max(0.0, total_traced - (vasp_total + mixer_total + dormant_total))

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
            "time_to_vasp_seconds": time_to_vasp_sec or elapsed,
            "elapsed_seconds": elapsed,
            "funds_status": {
                "total_traced_usd": round(total_traced, 2),
                "vasp_amount_usd": round(vasp_total, 2),
                "mixer_amount_usd": round(mixer_total, 2),
                "dormant_amount_usd": round(dormant_total, 2),
                "unaccounted_usd": round(unaccounted, 2)
            }
        }

        await ws_manager.broadcast_event(
            f"trace:{self.case_id}",
            "trace_complete",
            summary
        )

        return summary
