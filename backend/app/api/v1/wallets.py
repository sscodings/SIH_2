from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Wallet, Transfer, ClusterMember, Cluster, CaseComplaint, Complaint
from backend.app.engines.risk import RiskEngine
from backend.app.engines.typology import TypologyEngine
from backend.app.adapters.factory import get_chain_adapter

router = APIRouter(prefix="/wallets", tags=["Wallet Profiling"])

@router.get("/{chain}/{address}")
async def get_wallet_profile(chain: str, address: str, db: Session = Depends(get_db)):
    chain = chain.lower()
    adapter = get_chain_adapter(chain)
    summary = await adapter.get_address_summary(address)

    # Risk analysis
    risk = RiskEngine.calculate_wallet_risk(db, address, chain)
    typologies = TypologyEngine.detect_typologies(db, address, chain)

    # Cluster memberships
    member = db.query(ClusterMember).filter(
        ClusterMember.address.ilike(address),
        ClusterMember.chain == chain
    ).first()
    cluster_info = None
    if member:
        cl = db.query(Cluster).filter(Cluster.id == member.cluster_id).first()
        if cl:
            cluster_info = {
                "cluster_id": cl.id,
                "cluster_name": cl.name,
                "cluster_type": cl.cluster_type,
                "rule_formed": member.rule_formed,
                "member_count": cl.member_count
            }

    # Linked complaints
    linked_complaints = db.query(Complaint).filter(Complaint.reported_wallets.contains(address)).all()

    return {
        "address": address,
        "chain": chain,
        "summary": summary.dict(),
        "risk": risk,
        "typologies": typologies,
        "cluster": cluster_info,
        "linked_complaints": [
            {
                "id": c.id,
                "complaint_number": c.complaint_number,
                "victim_name": c.victim_name,
                "amount_lost_inr": c.amount_lost_inr,
                "fraud_type": c.fraud_type
            }
            for c in linked_complaints
        ]
    }

@router.get("/{chain}/{address}/risk")
def get_wallet_risk(chain: str, address: str, db: Session = Depends(get_db)):
    risk = RiskEngine.calculate_wallet_risk(db, address, chain.lower())
    typologies = TypologyEngine.detect_typologies(db, address, chain.lower())
    return {
        "address": address,
        "chain": chain,
        "risk": risk,
        "typologies": typologies
    }

@router.get("/{chain}/{address}/transfers")
async def get_wallet_transfers(chain: str, address: str, direction: str = "both", limit: int = 50, db: Session = Depends(get_db)):
    adapter = get_chain_adapter(chain.lower())
    transfers = await adapter.get_transfers(address, direction=direction, limit=limit)
    return {
        "address": address,
        "chain": chain,
        "count": len(transfers),
        "transfers": [t.dict() for t in transfers]
    }
