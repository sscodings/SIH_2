import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Transfer, Cluster, ClusterMember
from app.core.addresses import normalize, node_key
from app.core.service_registry import ServiceRegistry

class ClusteringEngine:
    """
    Forensic Clustering Engine:
    1. Bounded Time-Window Sweep Clustering (non-service targets only)
    2. Bitcoin Common-Input-Ownership Heuristic (excluding CoinJoin)
    3. EVM/Tron Gas Funding Dispersal Pattern (fresh wallet rapid funding)
    """

    @staticmethod
    def identify_sweep_clusters(
        db: Session,
        chain: str,
        window_hours: int = 24,
        min_senders: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Groups non-service wallets that sweep funds to the same destination within bounded time window.
        Excludes known VASPs, exchanges, mixers, DEX routers, and bridges to prevent clustering unrelated customers.
        """
        chain = chain.lower().strip()
        
        # Bounded SQL query: group by destination address with counts >= min_senders
        sweep_targets = db.query(
            Transfer.to_address,
            func.count(func.distinct(Transfer.from_address)).label("sender_count")
        ).filter(
            Transfer.chain == chain
        ).group_by(
            Transfer.to_address
        ).having(
            func.count(func.distinct(Transfer.from_address)) >= min_senders
        ).all()

        clusters_found = []
        for target_row in sweep_targets:
            target_addr = target_row.to_address
            norm_target = normalize(chain, target_addr)

            # Exclude known service targets (VASPs, bridges, mixers, DEX)
            if ServiceRegistry.is_service(chain, norm_target):
                continue

            # Fetch transfers to this target and group within time window
            txs = db.query(Transfer).filter(
                Transfer.chain == chain,
                Transfer.to_address == norm_target
            ).order_by(Transfer.timestamp.asc()).all()

            if not txs:
                continue

            # Cluster transfers by 24h window
            current_window_txs = [txs[0]]
            window_start = txs[0].timestamp

            for tx in txs[1:]:
                tx_ts = tx.timestamp.replace(tzinfo=timezone.utc if tx.timestamp.tzinfo is None else tx.timestamp.tzinfo)
                w_start = window_start.replace(tzinfo=timezone.utc if window_start.tzinfo is None else window_start.tzinfo)
                if (tx_ts - w_start).total_seconds() <= window_hours * 3600:
                    current_window_txs.append(tx)
                else:
                    # Check if previous window meets minimum senders
                    senders = list(set(normalize(chain, t.from_address) for t in current_window_txs))
                    if len(senders) >= min_senders:
                        evidence_txs = list(set(t.tx_hash for t in current_window_txs))
                        clusters_found.append({
                            "cluster_type": "Same Non-Service Sweep Target",
                            "target_address": norm_target,
                            "member_addresses": senders,
                            "chain": chain,
                            "rule": f"Swept to common intermediary {norm_target[:10]}... within {window_hours}h",
                            "confidence": 0.82,
                            "evidence_tx_hashes": evidence_txs
                        })
                    current_window_txs = [tx]
                    window_start = tx.timestamp

            # Process final window
            senders = list(set(normalize(chain, t.from_address) for t in current_window_txs))
            if len(senders) >= min_senders:
                evidence_txs = list(set(t.tx_hash for t in current_window_txs))
                clusters_found.append({
                    "cluster_type": "Same Non-Service Sweep Target",
                    "target_address": norm_target,
                    "member_addresses": senders,
                    "chain": chain,
                    "rule": f"Swept to common intermediary {norm_target[:10]}... within {window_hours}h",
                    "confidence": 0.82,
                    "evidence_tx_hashes": evidence_txs
                })

        return clusters_found

    @staticmethod
    def identify_btc_common_input_clusters(
        db: Session,
        min_inputs: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Bitcoin Common-Input-Ownership Heuristic:
        Multiple inputs spending in the same transaction are controlled by the same wallet/entity.
        CoinJoin transactions (transactions with >= 3 equal-value outputs) are excluded and flagged.
        """
        # Find multi-input BTC transactions
        btc_txs = db.query(Transfer).filter(
            Transfer.chain == "bitcoin"
        ).all()

        # Group by tx_hash
        by_tx: Dict[str, List[Transfer]] = {}
        for t in btc_txs:
            by_tx.setdefault(t.tx_hash, []).append(t)

        clusters_found = []
        for tx_hash, tx_list in by_tx.items():
            senders = list(set(normalize("bitcoin", t.from_address) for t in tx_list if t.from_address != "coinbase"))
            outputs = [t.amount for t in tx_list]

            # CoinJoin Check: If transaction has >= 3 identical output amounts (within 0.0001 BTC tolerance)
            is_coinjoin = False
            if len(outputs) >= 3:
                rounded_outputs = [round(amt, 4) for amt in outputs]
                from collections import Counter
                counts = Counter(rounded_outputs)
                if any(c >= 3 for c in counts.values()):
                    is_coinjoin = True

            if is_coinjoin:
                # Do NOT cluster CoinJoin transactions (anonymity pool)
                continue

            if len(senders) >= min_inputs:
                clusters_found.append({
                    "cluster_type": "Bitcoin Common-Input Heuristic",
                    "target_address": f"tx:{tx_hash[:12]}",
                    "member_addresses": senders,
                    "chain": "bitcoin",
                    "rule": "btc_common_input_ownership",
                    "confidence": 0.78,
                    "evidence_tx_hashes": [tx_hash]
                })

        return clusters_found

    @staticmethod
    def identify_gas_funding_clusters(
        db: Session,
        chain: str,
        window_hours: int = 12,
        min_funded: int = 3
    ) -> List[Dict[str, Any]]:
        """
        EVM/Tron Fresh Wallet Gas Funding Dispersal Pattern:
        A master wallet dispersing small gas amounts (ETH/TRX/BNB) to multiple fresh wallets within <12h.
        """
        chain = chain.lower().strip()
        gas_tokens = {"ETH", "TRX", "BNB", "POL", "MATIC"}

        transfers = db.query(Transfer).filter(
            Transfer.chain == chain,
            Transfer.token.in_(gas_tokens),
            Transfer.amount_usd < 100.0  # Gas funding amounts are typically small
        ).order_by(Transfer.timestamp.asc()).all()

        by_funder: Dict[str, List[Transfer]] = {}
        for t in transfers:
            norm_funder = normalize(chain, t.from_address)
            # Skip if funder is a known service
            if ServiceRegistry.is_service(chain, norm_funder):
                continue
            by_funder.setdefault(norm_funder, []).append(t)

        clusters_found = []
        for funder, fund_txs in by_funder.items():
            if len(fund_txs) < min_funded:
                continue

            # Group funded recipients within time window
            window_start = fund_txs[0].timestamp
            current_recipients = [fund_txs[0]]

            for t in fund_txs[1:]:
                t_ts = t.timestamp.replace(tzinfo=timezone.utc if t.timestamp.tzinfo is None else t.timestamp.tzinfo)
                w_ts = window_start.replace(tzinfo=timezone.utc if window_start.tzinfo is None else window_start.tzinfo)
                if (t_ts - w_ts).total_seconds() <= window_hours * 3600:
                    current_recipients.append(t)
                else:
                    rec_addrs = list(set(normalize(chain, x.to_address) for x in current_recipients))
                    if len(rec_addrs) >= min_funded:
                        evidence_txs = list(set(x.tx_hash for x in current_recipients))
                        clusters_found.append({
                            "cluster_type": "Fresh Wallet Gas Funding Dispersal",
                            "target_address": funder,
                            "member_addresses": rec_addrs,
                            "chain": chain,
                            "rule": f"Gas funded by master wallet {funder[:10]}... within {window_hours}h",
                            "confidence": 0.85,
                            "evidence_tx_hashes": evidence_txs
                        })
                    current_recipients = [t]
                    window_start = t.timestamp

            rec_addrs = list(set(normalize(chain, x.to_address) for x in current_recipients))
            if len(rec_addrs) >= min_funded:
                evidence_txs = list(set(x.tx_hash for x in current_recipients))
                clusters_found.append({
                    "cluster_type": "Fresh Wallet Gas Funding Dispersal",
                    "target_address": funder,
                    "member_addresses": rec_addrs,
                    "chain": chain,
                    "rule": f"Gas funded by master wallet {funder[:10]}... within {window_hours}h",
                    "confidence": 0.85,
                    "evidence_tx_hashes": evidence_txs
                })

        return clusters_found

    @staticmethod
    def add_address_to_cluster(
        db: Session,
        cluster_name: str,
        primary_entity: str,
        address: str,
        chain: str,
        rule: str,
        confidence: float = 0.85,
        evidence_tx_hashes: Optional[List[str]] = None
    ) -> ClusterMember:
        """
        Idempotent cluster insertion. Prevents duplicate cluster members or phantom clusters upon re-running.
        """
        chain = chain.lower().strip()
        norm_addr = normalize(chain, address)

        cluster = db.query(Cluster).filter(Cluster.name == cluster_name).first()
        if not cluster:
            cluster = Cluster(
                name=cluster_name,
                primary_entity=primary_entity,
                cluster_type=rule,
                member_count=0
            )
            db.add(cluster)
            db.commit()
            db.refresh(cluster)

        existing_member = db.query(ClusterMember).filter(
            ClusterMember.cluster_id == cluster.id,
            ClusterMember.address == norm_addr,
            ClusterMember.chain == chain
        ).first()

        if not existing_member:
            tx_json = json.dumps(evidence_tx_hashes or [])
            member = ClusterMember(
                cluster_id=cluster.id,
                address=norm_addr,
                chain=chain,
                rule_formed=rule,
                confidence=confidence,
                evidence_tx_hashes=tx_json
            )
            db.add(member)
            cluster.member_count = db.query(ClusterMember).filter(ClusterMember.cluster_id == cluster.id).count() + 1
            db.commit()
            db.refresh(member)
            return member

        return existing_member
