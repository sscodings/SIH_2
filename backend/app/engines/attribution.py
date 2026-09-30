from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.db.models import Label, LabelSource, Entity, EntityAddress, Cluster, ClusterMember, Transfer

class AttributionEngine:
    @staticmethod
    def calculate_confidence(
        label_source_weight: float,
        evidence_strength: float,
        cluster_support: float,
        hops_from_label: int = 0
    ) -> Dict[str, Any]:
        """
        Calculates attribution confidence % using ChainNetra's formal formula:
        confidence = 100 * clamp( 0.45 * label_source_weight + 0.30 * evidence_strength + 0.15 * cluster_support - 0.02 * hops_from_label , 0, 1 )
        """
        raw = (
            0.45 * label_source_weight +
            0.30 * evidence_strength +
            0.15 * cluster_support -
            0.02 * hops_from_label
        )
        clamped = max(0.0, min(1.0, raw))
        score = round(clamped * 100.0, 1)

        return {
            "confidence_score": score,
            "label_source_weight": round(label_source_weight, 2),
            "evidence_strength": round(evidence_strength, 2),
            "cluster_support": round(cluster_support, 2),
            "hops_decay": round(0.02 * hops_from_label, 2),
            "hops_from_label": hops_from_label,
            "formula": "100 * clamp(0.45*Src + 0.30*Evid + 0.15*Clust - 0.02*Hops, 0, 1)"
        }

    @staticmethod
    def resolve_label(db: Session, address: str, chain: str) -> Optional[Dict[str, Any]]:
        # 1. Direct label lookup in labels table
        label_entry = db.query(Label).filter(
            Label.address.ilike(address),
            Label.chain == chain
        ).first()

        if label_entry:
            source_rec = db.query(LabelSource).filter(LabelSource.name == label_entry.source).first()
            source_weight = source_rec.reliability_weight if source_rec else 0.95
            evidence_str = 1.0 if ("hot" in label_entry.category.lower() or "deposit" in label_entry.category.lower()) else 0.85
            cluster_sup = 0.95
            conf = AttributionEngine.calculate_confidence(
                label_source_weight=source_weight,
                evidence_strength=evidence_str,
                cluster_support=cluster_sup,
                hops_from_label=0
            )
            return {
                "entity": label_entry.entity,
                "category": label_entry.category,
                "source": label_entry.source,
                "confidence": conf["confidence_score"],
                "confidence_details": conf,
                "evidence_type": "Direct Verified VASP Registry Match"
            }

        # 2. Check Entity Addresses (hot wallet or deposit)
        ea = db.query(EntityAddress).filter(
            EntityAddress.address.ilike(address),
            EntityAddress.chain == chain
        ).first()
        if ea:
            ent = db.query(Entity).filter(Entity.id == ea.entity_id).first()
            ent_name = ent.name if ent else "Verified VASP"
            evidence_str = 1.0 if ea.address_type in ["hot_wallet", "deposit"] else 0.85
            conf = AttributionEngine.calculate_confidence(
                label_source_weight=0.98,
                evidence_strength=evidence_str,
                cluster_support=0.95,
                hops_from_label=0
            )
            return {
                "entity": ent_name,
                "category": ent.category if ent else "VASP",
                "source": "VASP Verified Infrastructure Registry",
                "confidence": conf["confidence_score"],
                "confidence_details": conf,
                "evidence_type": f"Direct Entity Address ({ea.address_type})"
            }

        # 3. Check Cluster Inference
        member = db.query(ClusterMember).filter(
            ClusterMember.address.ilike(address),
            ClusterMember.chain == chain
        ).first()
        if member:
            cluster = db.query(Cluster).filter(Cluster.id == member.cluster_id).first()
            if cluster:
                conf = AttributionEngine.calculate_confidence(
                    label_source_weight=0.85,
                    evidence_strength=0.70,
                    cluster_support=0.95,
                    hops_from_label=1
                )
                return {
                    "entity": cluster.primary_entity,
                    "category": "Cluster Node",
                    "source": f"Cluster Heuristic ({member.rule_formed})",
                    "confidence": conf["confidence_score"],
                    "confidence_details": conf,
                    "evidence_type": f"Cluster Membership: {cluster.name} via {member.rule_formed}"
                }

        # 4. Exchange Deposit Address Heuristic (Fan-in -> rapid sweep to known VASP hot wallet)
        sweeps = db.query(Transfer).filter(
            Transfer.from_address.ilike(address),
            Transfer.chain == chain
        ).all()

        for sw in sweeps:
            target_ea = db.query(EntityAddress).filter(
                EntityAddress.address.ilike(sw.to_address),
                EntityAddress.chain == chain,
                EntityAddress.address_type == "hot_wallet"
            ).first()
            if target_ea:
                ent = db.query(Entity).filter(Entity.id == target_ea.entity_id).first()
                ent_name = ent.name if ent else "Verified Exchange"
                conf = AttributionEngine.calculate_confidence(
                    label_source_weight=0.92,
                    evidence_strength=0.88,  # sweep-pattern match
                    cluster_support=0.85,
                    hops_from_label=1
                )
                return {
                    "entity": ent_name,
                    "category": "VASP Deposit Address",
                    "source": "Sweep Pattern Heuristic",
                    "confidence": conf["confidence_score"],
                    "confidence_details": conf,
                    "evidence_type": f"Heuristic: Direct sweep of {sw.amount:.2f} {sw.token} to known {ent_name} Hot Wallet"
                }

        return None
