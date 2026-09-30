import os
import joblib
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.db.models import Transfer, Wallet

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "models")

class RiskEngine:
    @staticmethod
    def extract_features(db: Session, address: str, chain: str) -> Dict[str, float]:
        """
        Extracts 12 forensic behavioral features for a wallet.
        """
        in_transfers = db.query(Transfer).filter(
            Transfer.to_address.ilike(address),
            Transfer.chain == chain
        ).all()

        out_transfers = db.query(Transfer).filter(
            Transfer.from_address.ilike(address),
            Transfer.chain == chain
        ).all()

        fan_in = len(set(t.from_address.lower() for t in in_transfers))
        fan_out = len(set(t.to_address.lower() for t in out_transfers))

        total_in = sum(t.amount_usd for t in in_transfers)
        total_out = sum(t.amount_usd for t in out_transfers)

        pass_through_ratio = min(5.0, (total_out / max(total_in, 0.01))) if total_in > 0 else 0.0

        all_txs = in_transfers + out_transfers
        if all_txs:
            timestamps = sorted([t.timestamp for t in all_txs])
            age_days = (timestamps[-1] - timestamps[0]).total_seconds() / 86400.0
            round_amts = sum(1 for t in all_txs if t.amount > 0 and (t.amount % 10 == 0 or t.amount % 50 == 0))
            round_amount_ratio = round_amts / len(all_txs)
            burstiness = len(all_txs) / max(1.0, age_days)
        else:
            age_days = 0.0
            round_amount_ratio = 0.0
            burstiness = 0.0

        wallet_record = db.query(Wallet).filter(
            Wallet.address.ilike(address),
            Wallet.chain == chain
        ).first()

        balance_usd = wallet_record.balance_usd if wallet_record else max(0.0, total_in - total_out)
        is_dormant = 1.0 if (len(out_transfers) == 0 and balance_usd > 100.0) else 0.0
        
        # Exposure to mixers/bridges
        mixer_exposure = 1.0 if any("mix" in t.to_address.lower() or "mix" in t.from_address.lower() for t in all_txs) else 0.0
        bridge_exposure = 1.0 if any(t.is_contract_call or "bridge" in t.to_address.lower() for t in all_txs) else 0.0

        return {
            "fan_in": float(fan_in),
            "fan_out": float(fan_out),
            "total_in_usd": float(total_in),
            "total_out_usd": float(total_out),
            "pass_through_ratio": float(round(pass_through_ratio, 3)),
            "round_amount_ratio": float(round(round_amount_ratio, 3)),
            "age_days": float(round(age_days, 2)),
            "burstiness": float(round(burstiness, 2)),
            "distinct_counterparties": float(fan_in + fan_out),
            "mixer_exposure": mixer_exposure,
            "bridge_exposure": bridge_exposure,
            "dormant_flag": is_dormant,
            "balance_usd": float(balance_usd)
        }

    @staticmethod
    def calculate_wallet_risk(db: Session, address: str, chain: str) -> Dict[str, Any]:
        features = RiskEngine.extract_features(db, address, chain)
        
        # Rule-based risk score blend
        score = 15.0 # baseline
        factors = []

        if features["mixer_exposure"] > 0:
            score += 35.0
            factors.append({
                "feature": "Mixer Interaction",
                "value": "Detected",
                "impact": "+35",
                "why": "Direct deposit or withdrawal from privacy tumbler / mixer contract"
            })

        if features["pass_through_ratio"] > 0.85 and features["fan_out"] >= 3:
            score += 25.0
            factors.append({
                "feature": "Layering / Rapid Pass-Through",
                "value": f"{features['pass_through_ratio']*100:.1f}% swept",
                "impact": "+25",
                "why": "High-velocity pass-through characteristic of mule/intermediary layering wallets"
            })

        if features["fan_in"] >= 8:
            score += 20.0
            factors.append({
                "feature": "High Fan-In Inflow",
                "value": f"{int(features['fan_in'])} distinct senders",
                "impact": "+20",
                "why": "Multiple distinct victim deposits consolidating into single collector address"
            })

        if features["burstiness"] > 5.0:
            score += 15.0
            factors.append({
                "feature": "Transaction Burstiness",
                "value": f"{features['burstiness']:.1f} tx/day",
                "impact": "+15",
                "why": "Unusual burst of high-velocity operations over a brief time window"
            })

        if features["dormant_flag"] > 0:
            score += 10.0
            factors.append({
                "feature": "Dormant Holding",
                "value": f"${features['balance_usd']:,.2f} static",
                "impact": "+10",
                "why": "Retained funds with zero recent outflows; prime candidate for freezing"
            })

        if features["bridge_exposure"] > 0:
            score += 10.0
            factors.append({
                "feature": "Cross-Chain Bridge Usage",
                "value": "Detected",
                "impact": "+10",
                "why": "Attempt to obscure forensic trail across blockchain boundaries"
            })

        final_score = min(99.0, max(5.0, score))
        if final_score >= 80:
            level = "Critical"
        elif final_score >= 60:
            level = "High"
        elif final_score >= 35:
            level = "Medium"
        else:
            level = "Low"

        # Ensure top 5 factors
        if len(factors) < 5:
            factors.append({
                "feature": "Wallet Counterparties",
                "value": f"{int(features['distinct_counterparties'])} addresses",
                "impact": "+5",
                "why": "Counterparty graph interaction footprint"
            })

        return {
            "address": address,
            "chain": chain,
            "risk_score": round(final_score, 1),
            "risk_level": level,
            "features": features,
            "top_factors": factors[:5]
        }
