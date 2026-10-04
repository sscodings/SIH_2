import os
import json
import logging
import joblib
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import Transfer, Wallet

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "models")

# Default fallback feature list if model_card is missing
DEFAULT_FEATURE_ORDER = [
    "fan_in", "fan_out", "total_in_usd", "total_out_usd", "pass_through_ratio",
    "round_amount_ratio", "age_days", "burstiness", "mixer_exposure", "bridge_exposure", "dormant_flag"
]

class MLModelManager:
    _instance: Optional["MLModelManager"] = None

    def __init__(self):
        self.rf_model = None
        self.iso_model = None
        self.feature_order = DEFAULT_FEATURE_ORDER
        self.loaded = False
        self._load_models()

    def _load_models(self):
        try:
            card_path = os.path.join(MODEL_DIR, "model_card.json")
            if os.path.exists(card_path):
                with open(card_path, "r") as f:
                    card_data = json.load(f)
                    self.feature_order = card_data.get("feature_order", DEFAULT_FEATURE_ORDER)

            rf_path = os.path.join(MODEL_DIR, "wallet_role_rf.joblib")
            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)

            iso_path = os.path.join(MODEL_DIR, "anomaly_iso.joblib")
            if os.path.exists(iso_path):
                self.iso_model = joblib.load(iso_path)

            if self.rf_model is not None and self.iso_model is not None:
                self.loaded = True
        except Exception as e:
            logger.warning(f"Failed to load ML models gracefully: {e}")
            self.loaded = False

    @classmethod
    def get_instance(cls) -> "MLModelManager":
        if cls._instance is None:
            cls._instance = MLModelManager()
        return cls._instance

class RiskEngine:
    @staticmethod
    def extract_features(db: Session, address: str, chain: str) -> Dict[str, float]:
        """
        Extracts forensic behavioral features for a wallet.
        """
        from app.core.addresses import normalize
        from app.core.service_registry import ServiceRegistry

        norm_addr = normalize(chain, address)
        in_transfers = db.query(Transfer).filter(
            Transfer.to_address == norm_addr,
            Transfer.chain == chain
        ).all()

        out_transfers = db.query(Transfer).filter(
            Transfer.from_address == norm_addr,
            Transfer.chain == chain
        ).all()

        fan_in = len(set(normalize(chain, t.from_address) for t in in_transfers))
        fan_out = len(set(normalize(chain, t.to_address) for t in out_transfers))

        total_in = sum(t.amount_usd for t in in_transfers)
        total_out = sum(t.amount_usd for t in out_transfers)

        pass_through_ratio = min(5.0, (total_out / max(total_in, 0.01))) if total_in > 0 else 0.0

        all_txs = in_transfers + out_transfers
        if all_txs:
            timestamps = sorted([t.timestamp for t in all_txs])
            age_days = max(0.01, (timestamps[-1] - timestamps[0]).total_seconds() / 86400.0)
            round_amts = sum(1 for t in all_txs if t.amount > 0 and (t.amount % 10 == 0 or t.amount % 50 == 0))
            round_amount_ratio = round_amts / len(all_txs)
            burstiness = len(all_txs) / max(1.0, age_days)
        else:
            age_days = 0.0
            round_amount_ratio = 0.0
            burstiness = 0.0

        wallet_record = db.query(Wallet).filter(
            Wallet.address == norm_addr,
            Wallet.chain == chain
        ).first()

        balance_usd = wallet_record.balance_usd if wallet_record else max(0.0, total_in - total_out)
        is_dormant = 1.0 if (len(out_transfers) == 0 and balance_usd > 100.0) else 0.0

        # Verified exposure to mixers and bridges strictly via curated ServiceRegistry
        mixer_exposure = 1.0 if any(
            ServiceRegistry.is_mixer(t.chain, t.to_address) or ServiceRegistry.is_mixer(t.chain, t.from_address)
            for t in all_txs
        ) else 0.0
        bridge_exposure = 1.0 if any(
            ServiceRegistry.is_bridge(t.chain, t.to_address) or ServiceRegistry.is_bridge(t.chain, t.from_address)
            for t in all_txs
        ) else 0.0

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
    def predict_ml_role_and_anomaly(features: Dict[str, float]) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        import pandas as pd
        mgr = MLModelManager.get_instance()
        if not mgr.loaded or mgr.rf_model is None or mgr.iso_model is None:
            return None, None, None

        try:
            # Build feature DataFrame in the exact persisted feature_order
            row_dict = {col: [features.get(col, 0.0)] for col in mgr.feature_order}
            feat_df = pd.DataFrame(row_dict)
            
            # Predict role & probability
            role = str(mgr.rf_model.predict(feat_df)[0])
            probas = mgr.rf_model.predict_proba(feat_df)[0]
            confidence = round(float(np.max(probas)), 3)

            # Predict anomaly score
            anomaly_score = round(float(mgr.iso_model.decision_function(feat_df)[0]), 3)

            return role, confidence, anomaly_score
        except Exception as e:
            logger.warning(f"Error executing ML model prediction: {e}")
            return None, None, None

    @staticmethod
    def calculate_wallet_risk(db: Session, address: str, chain: str) -> Dict[str, Any]:
        features = RiskEngine.extract_features(db, address, chain)
        
        # Rule-based risk score blend
        score = 15.0  # baseline
        factors: List[Dict[str, str]] = []

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

        # ML Model Inference & Blending
        ml_role, ml_confidence, anomaly_score = RiskEngine.predict_ml_role_and_anomaly(features)
        
        if ml_role:
            if ml_role in ["collector", "mixer", "intermediary", "peel"]:
                impact_val = 15.0 if (ml_confidence or 0) >= 0.7 else 10.0
                score += impact_val
                factors.append({
                    "feature": "ML Role Classification",
                    "value": f"{ml_role.upper()} ({((ml_confidence or 0)*100):.1f}%)",
                    "impact": f"+{int(impact_val)}",
                    "why": f"Random Forest pattern classifier identified role as {ml_role}"
                })
            elif ml_role == "normal" and (ml_confidence or 0) >= 0.85:
                score = max(5.0, score - 10.0)
                factors.append({
                    "feature": "ML Normal Profile",
                    "value": f"NORMAL ({((ml_confidence or 0)*100):.1f}%)",
                    "impact": "-10",
                    "why": "Transactional pattern consistent with typical non-syndicate retail activity"
                })

        if anomaly_score is not None and anomaly_score < 0:
            score += 10.0
            factors.append({
                "feature": "Isolation Forest Anomaly",
                "value": f"Score {anomaly_score:.3f}",
                "impact": "+10",
                "why": "Statistical anomaly detected compared to baseline transactional profiles"
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

        return {
            "score": round(final_score, 1),
            "level": level,
            "ml_role": ml_role,
            "ml_confidence": ml_confidence,
            "anomaly_score": anomaly_score,
            "features": features,
            "factors": factors
        }
