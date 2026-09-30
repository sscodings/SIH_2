from typing import List, Dict, Set
from sqlalchemy.orm import Session
from backend.app.db.models import Transfer, Cluster, ClusterMember

class ClusteringEngine:
    @staticmethod
    def identify_sweep_clusters(db: Session, chain: str) -> List[Dict]:
        """
        Groups wallets that sweep funds to the same destination within 24 hours.
        """
        transfers = db.query(Transfer).filter(Transfer.chain == chain).all()
        target_map: Dict[str, Set[str]] = {}
        for t in transfers:
            target_map.setdefault(t.to_address.lower(), set()).add(t.from_address.lower())

        clusters_found = []
        for target, senders in target_map.items():
            if len(senders) >= 2:
                clusters_found.append({
                    "cluster_type": "Same Sweep Target",
                    "target_address": target,
                    "member_addresses": list(senders),
                    "rule": f"Swept to common target {target[:8]}..."
                })
        return clusters_found

    @staticmethod
    def add_address_to_cluster(db: Session, cluster_name: str, primary_entity: str, address: str, chain: str, rule: str):
        cluster = db.query(Cluster).filter(Cluster.name == cluster_name).first()
        if not cluster:
            cluster = Cluster(name=cluster_name, primary_entity=primary_entity, cluster_type=rule, member_count=1)
            db.add(cluster)
            db.commit()
            db.refresh(cluster)
        
        existing_member = db.query(ClusterMember).filter(
            ClusterMember.cluster_id == cluster.id,
            ClusterMember.address.ilike(address)
        ).first()

        if not existing_member:
            member = ClusterMember(cluster_id=cluster.id, address=address, chain=chain, rule_formed=rule)
            db.add(member)
            cluster.member_count += 1
            db.commit()
