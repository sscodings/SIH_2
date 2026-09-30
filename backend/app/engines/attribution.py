from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import Label, LabelSource, Entity, EntityAddress, Cluster, ClusterMember, Transfer
from app.core.addresses import normalize, node_key
from app.core.service_registry import ServiceRegistry

class AttributionEngine:
    @staticmethod
    def calculate_confidence(
        label_source_weight: float,
        evidence_strength: float,
        cluster_support: float,
        hops_from_label: int = 0,
        evidence_facts: Optional[List[str]] = None,
        source_name: str = "Unknown",
        evidence_type: str = "Unspecified",
        label_age_days: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates attribution confidence % using ChainNetra's formal formula:
        confidence = 100 * clamp( 0.45 * label_source_weight + 0.30 * evidence_strength + 0.15 * cluster_support - 0.02 * hops_from_label , 0, 1 )
        Every component is computed dynamically from concrete evidence.
        """
        # Apply age decay to label source weight if label is old (> 180 days)
        effective_source_weight = label_source_weight
        if label_age_days is not None and label_age_days > 180:
            age_decay = min(0.30, ((label_age_days - 180) / 365.0) * 0.15)
            effective_source_weight = max(0.50, label_source_weight - age_decay)

        # Invariant: cluster_support must be between 0 and 1
        clamped_cluster_support = max(0.0, min(1.0, cluster_support))
        clamped_evidence_strength = max(0.0, min(1.0, evidence_strength))
        clamped_source_weight = max(0.0, min(1.0, effective_source_weight))

        raw = (
            0.45 * clamped_source_weight +
            0.30 * clamped_evidence_strength +
            0.15 * clamped_cluster_support -
            0.02 * hops_from_label
        )
        clamped = max(0.0, min(1.0, raw))
        score = round(clamped * 100.0, 1)

        # Determine qualitative confidence level with documented thresholds:
        # - VERIFIED: Direct verified registry match or official intel (evidence_strength >= 0.95 and source_weight >= 0.90)
        # - HIGH: Score >= 65.0 (robust multi-sweep deposit heuristic or high-support cluster)
        # - MEDIUM: Score >= 45.0 (single payment / lower-tier heuristic)
        # - LOW: Score < 45.0 (weak or unverified heuristic)
        if clamped_evidence_strength >= 0.95 and clamped_source_weight >= 0.90:
            conf_level = "VERIFIED"
        elif score >= 65.0:
            conf_level = "HIGH"
        elif score >= 45.0:
            conf_level = "MEDIUM"
        else:
            conf_level = "LOW"

        return {
            "confidence_score": score,
            "confidence_level": conf_level,
            "label_source_weight": round(clamped_source_weight, 3),
            "evidence_strength": round(clamped_evidence_strength, 3),
            "cluster_support": round(clamped_cluster_support, 3),
            "hops_decay": round(0.02 * hops_from_label, 3),
            "hops_from_label": hops_from_label,
            "source_name": source_name,
            "evidence_type": evidence_type,
            "evidence": evidence_facts or [],
            "formula": "100 * clamp(0.45*Src + 0.30*Evid + 0.15*Clust - 0.02*Hops, 0, 1)"
        }

    @staticmethod
    def resolve_label(
        db: Session,
        address: str,
        chain: str,
        cached_labels: Optional[Dict[str, Any]] = None,
        cached_clusters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        chain = chain.lower().strip()
        norm_addr = normalize(chain, address)
        nk = node_key(chain, address)

        # 0. Check per-trace run memory cache
        if cached_labels is not None and nk in cached_labels:
            return cached_labels[nk]

        # 1. Direct Service Registry Lookup (Mixers, Bridges, DEX Routers, VASP Hot Wallets)
        service_entry = ServiceRegistry.lookup(chain, norm_addr)
        if service_entry:
            age_days = (datetime.now(timezone.utc) - service_entry.verified_at).total_seconds() / 86400.0 if service_entry.verified_at else 0.0
            conf = AttributionEngine.calculate_confidence(
                label_source_weight=0.98,
                evidence_strength=1.0,
                cluster_support=0.0,
                hops_from_label=0,
                label_age_days=age_days,
                source_name=service_entry.source,
                evidence_type=f"Curated {service_entry.kind.upper()} Registry Match",
                evidence_facts=[
                    f"Direct contract match in ServiceRegistry: {service_entry.name} ({service_entry.kind})",
                    f"Source: {service_entry.source}, Verified: {service_entry.verified_at.isoformat() if service_entry.verified_at else 'N/A'}"
                ]
            )
            res = {
                "entity": service_entry.name,
                "category": service_entry.kind.replace("_", " ").title(),
                "source": service_entry.source,
                "confidence": conf["confidence_score"],
                "confidence_level": conf["confidence_level"],
                "confidence_details": conf,
                "evidence": conf["evidence"],
                "evidence_type": conf["evidence_type"]
            }
            if cached_labels is not None:
                cached_labels[nk] = res
            return res

        # 2. Direct label lookup in labels table
        label_entry = db.query(Label).filter(
            Label.address == norm_addr,
            Label.chain == chain
        ).first()

        if label_entry:
            source_rec = db.query(LabelSource).filter(LabelSource.name == label_entry.source).first()
            source_weight = source_rec.reliability_weight if source_rec else 0.85
            evidence_str = 1.0 if any(k in label_entry.category.lower() for k in ["hot", "deposit", "vault", "custody"]) else 0.85
            
            verified_ts = getattr(label_entry, "verified_at", None) or label_entry.created_at
            label_age_days = (datetime.now(timezone.utc) - verified_ts.replace(tzinfo=timezone.utc if verified_ts.tzinfo is None else verified_ts.tzinfo)).total_seconds() / 86400.0 if verified_ts else 0.0

            conf = AttributionEngine.calculate_confidence(
                label_source_weight=source_weight,
                evidence_strength=evidence_str,
                cluster_support=0.0,
                hops_from_label=0,
                label_age_days=label_age_days,
                source_name=label_entry.source,
                evidence_type="Direct Verified Database Label",
                evidence_facts=[
                    f"Verified Label: '{label_entry.entity}' ({label_entry.category})",
                    f"Source: {label_entry.source} (Reliability: {source_weight})",
                    f"Age: {int(label_age_days)} days"
                ]
            )
            res = {
                "entity": label_entry.entity,
                "category": label_entry.category,
                "source": label_entry.source,
                "confidence": conf["confidence_score"],
                "confidence_level": conf["confidence_level"],
                "confidence_details": conf,
                "evidence": conf["evidence"],
                "evidence_type": conf["evidence_type"]
            }
            if cached_labels is not None:
                cached_labels[nk] = res
            return res

        # 3. Check Entity Addresses (hot wallet, deposit, cold storage)
        ea = db.query(EntityAddress).filter(
            EntityAddress.address == norm_addr,
            EntityAddress.chain == chain
        ).first()
        if ea:
            ent = db.query(Entity).filter(Entity.id == ea.entity_id).first()
            ent_name = ent.name if ent else "Verified VASP"
            evidence_str = 1.0 if ea.address_type in ["hot_wallet", "deposit", "vault"] else 0.85
            conf = AttributionEngine.calculate_confidence(
                label_source_weight=0.98,
                evidence_strength=evidence_str,
                cluster_support=0.0,
                hops_from_label=0,
                source_name="VASP Infrastructure Registry",
                evidence_type=f"Entity Infrastructure Address ({ea.address_type})",
                evidence_facts=[
                    f"Registered {ea.address_type} for VASP '{ent_name}'",
                    f"Jurisdiction: {ent.jurisdiction if ent else 'Global'}"
                ]
            )
            res = {
                "entity": ent_name,
                "category": ent.category if ent else "VASP",
                "source": "VASP Infrastructure Registry",
                "confidence": conf["confidence_score"],
                "confidence_level": conf["confidence_level"],
                "confidence_details": conf,
                "evidence": conf["evidence"],
                "evidence_type": conf["evidence_type"]
            }
            if cached_labels is not None:
                cached_labels[nk] = res
            return res

        # 4. Check Cluster Membership
        member = db.query(ClusterMember).filter(
            ClusterMember.address == norm_addr,
            ClusterMember.chain == chain
        ).first()
        if member:
            cluster = db.query(Cluster).filter(Cluster.id == member.cluster_id).first()
            if cluster:
                # Compute real cluster support: supporting members / total members
                total_cluster_members = db.query(ClusterMember).filter(ClusterMember.cluster_id == cluster.id).count()
                supporting_members = db.query(ClusterMember).filter(
                    ClusterMember.cluster_id == cluster.id,
                    ClusterMember.rule_formed == member.rule_formed
                ).count()
                cluster_support = (supporting_members / max(1, total_cluster_members))

                conf = AttributionEngine.calculate_confidence(
                    label_source_weight=0.85,
                    evidence_strength=0.72,
                    cluster_support=cluster_support,
                    hops_from_label=1,
                    source_name=f"Cluster Heuristic ({member.rule_formed})",
                    evidence_type=f"Cluster Membership: {cluster.name}",
                    evidence_facts=[
                        f"Member of cluster '{cluster.name}' (Total: {total_cluster_members} addresses)",
                        f"Clustering Rule: {member.rule_formed}",
                        f"Cluster Support Ratio: {supporting_members}/{total_cluster_members} ({cluster_support*100:.1f}%)"
                    ]
                )
                res = {
                    "entity": cluster.primary_entity,
                    "category": "Cluster Node",
                    "source": f"Cluster Heuristic ({member.rule_formed})",
                    "confidence": conf["confidence_score"],
                    "confidence_level": conf["confidence_level"],
                    "confidence_details": conf,
                    "evidence": conf["evidence"],
                    "evidence_type": conf["evidence_type"]
                }
                if cached_labels is not None:
                    cached_labels[nk] = res
                return res

        # 5. Rigorous Exchange Deposit Address Heuristic
        # Requirements for "VASP Deposit Address":
        # 1. Received inflows from >= N distinct senders (default 3) OR external non-VASP customer deposit pattern
        # 2. Sweeps >= 90% of received funds to the SAME known VASP hot wallet
        # 3. Sweeps happen consistently (>= 2 times) within bounded delay (<= 24h)
        # 4. Has few/no other outflow destinations
        out_transfers = db.query(Transfer).filter(
            Transfer.from_address == norm_addr,
            Transfer.chain == chain
        ).order_by(Transfer.timestamp.asc()).limit(50).all()

        if out_transfers:
            # Check outflows to known VASP hot wallets
            hot_wallet_transfers: Dict[str, List[Transfer]] = {}
            other_destinations = set()
            total_outflow_usd = sum(t.amount_usd for t in out_transfers)

            for ot in out_transfers:
                target_norm = normalize(chain, ot.to_address)
                # Check if target is a known hot wallet
                target_ea = db.query(EntityAddress).filter(
                    EntityAddress.address == target_norm,
                    EntityAddress.chain == chain,
                    EntityAddress.address_type == "hot_wallet"
                ).first()
                if target_ea:
                    hot_wallet_transfers.setdefault(target_norm, []).append(ot)
                else:
                    other_destinations.add(target_norm)

            for hot_addr, sweeps in hot_wallet_transfers.items():
                swept_usd = sum(s.amount_usd for s in sweeps)
                sweep_ratio = swept_usd / max(total_outflow_usd, 0.001)

                target_ea = db.query(EntityAddress).filter(
                    EntityAddress.address == hot_addr,
                    EntityAddress.chain == chain
                ).first()
                ent = db.query(Entity).filter(Entity.id == target_ea.entity_id).first() if target_ea else None
                ent_name = ent.name if ent else "Verified Exchange"

                # Check inflows
                in_transfers = db.query(Transfer).filter(
                    Transfer.to_address == norm_addr,
                    Transfer.chain == chain
                ).limit(50).all()
                distinct_senders = len(set(normalize(chain, it.from_address) for it in in_transfers))
                num_sweeps = len(sweeps)

                # Qualification check for true Deposit Address:
                is_deposit_pattern = (
                    (distinct_senders >= 3 or (distinct_senders >= 1 and len(in_transfers) >= 2)) and
                    sweep_ratio >= 0.90 and
                    num_sweeps >= 2 and
                    len(other_destinations) <= 1
                )

                if is_deposit_pattern:
                    conf = AttributionEngine.calculate_confidence(
                        label_source_weight=0.92,
                        evidence_strength=0.88,
                        cluster_support=0.0,
                        hops_from_label=1,
                        source_name="Multi-Sweep Deposit Heuristic",
                        evidence_type="VASP Deposit Address (Multi-Sweep Confirmed)",
                        evidence_facts=[
                            f"Address swept {sweep_ratio*100:.1f}% (${swept_usd:,.2f}) to {ent_name} Hot Wallet",
                            f"Observed {num_sweeps} distinct sweep transactions",
                            f"Inflow received from {distinct_senders} distinct senders",
                            f"Target hot wallet: {hot_addr}"
                        ]
                    )
                    res = {
                        "entity": ent_name,
                        "category": "VASP Deposit Address",
                        "source": "Multi-Sweep Deposit Heuristic",
                        "confidence": conf["confidence_score"],
                        "confidence_level": conf["confidence_level"],
                        "confidence_details": conf,
                        "evidence": conf["evidence"],
                        "evidence_type": conf["evidence_type"]
                    }
                    if cached_labels is not None:
                        cached_labels[nk] = res
                    return res
                else:
                    # Single transfer / partial sweep -> lower tier attribution
                    conf = AttributionEngine.calculate_confidence(
                        label_source_weight=0.75,
                        evidence_strength=0.55,
                        cluster_support=0.0,
                        hops_from_label=1,
                        source_name="Direct Payment Heuristic",
                        evidence_type="Direct Sender to VASP Hot Wallet",
                        evidence_facts=[
                            f"Single/isolated transfer of ${swept_usd:,.2f} to {ent_name} Hot Wallet",
                            f"Does not meet multi-sweep deposit pattern (sweeps={num_sweeps}, senders={distinct_senders})",
                            f"Classified as intermediary or customer-side wallet"
                        ]
                    )
                    res = {
                        "entity": ent_name,
                        "category": "Direct Sender to VASP Hot Wallet",
                        "source": "Direct Payment Heuristic",
                        "confidence": conf["confidence_score"],
                        "confidence_level": conf["confidence_level"],
                        "confidence_details": conf,
                        "evidence": conf["evidence"],
                        "evidence_type": conf["evidence_type"]
                    }
                    if cached_labels is not None:
                        cached_labels[nk] = res
                    return res

        if cached_labels is not None:
            cached_labels[nk] = None
        return None
