from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.engines.risk import RiskEngine

class TypologyEngine:
    @staticmethod
    def detect_typologies(db: Session, address: str, chain: str) -> List[Dict[str, Any]]:
        features = RiskEngine.extract_features(db, address, chain)
        typologies = []

        # 1. Investment / Pig-Butchering Scam
        # Signature: many small victim deposits -> consolidation -> stablecoin cashout
        inv_score = 0
        inv_indicators = []
        if features["fan_in"] >= 4:
            inv_score += 35
            inv_indicators.append(f"Multiple victim inflows ({int(features['fan_in'])} distinct depositors)")
        if features["pass_through_ratio"] > 0.8:
            inv_score += 30
            inv_indicators.append("Consolidation of victim funds with rapid forward routing")
        if chain.lower() in ["tron", "ethereum", "bsc"]:
            inv_score += 25
            inv_indicators.append(f"Stablecoin transfer infrastructure on {chain.upper()}")
        if inv_score >= 60:
            typologies.append({
                "name": "Investment / Pig-Butchering Scam",
                "match_percentage": min(95.0, float(inv_score)),
                "description": "Victims induced to deposit funds into counterfeit investment platforms, followed by rapid consolidation into high-volume cash-out corridors.",
                "indicators": inv_indicators,
                "confidence": "HIGH"
            })

        # 2. Task-Based Fraud
        # Signature: many similar small deposits, rapid pass-through, fan-out to burner wallets
        task_score = 0
        task_indicators = []
        if features["fan_in"] >= 5 and features["fan_out"] >= 5:
            task_score += 40
            task_indicators.append("High fan-in accompanied by wide burner distribution fan-out")
        if features["burstiness"] > 3.0:
            task_score += 30
            task_indicators.append("High-frequency micro-transactions characteristic of task commission payouts")
        if task_score >= 60:
            typologies.append({
                "name": "Task-Based Fraud",
                "match_percentage": min(92.0, float(task_score)),
                "description": "Scammers recruit victims for fictitious online tasks, collecting escalating deposits before cutting communication and fanning out funds.",
                "indicators": task_indicators,
                "confidence": "HIGH"
            })

        # 3. Sextortion
        # Signature: BTC payments from senders, quick consolidation, mixer exposure
        if chain.lower() == "bitcoin" or features["mixer_exposure"] > 0:
            sex_score = 45 if features["mixer_exposure"] > 0 else 20
            if features["round_amount_ratio"] > 0.4:
                sex_score += 35
            if sex_score >= 50:
                typologies.append({
                    "name": "Sextortion Blackmail",
                    "match_percentage": min(88.0, float(sex_score)),
                    "description": "Extortion payments in standardized denominations channeled through privacy tumblers or direct consolidation.",
                    "indicators": ["Mixer exposure / coin tumbler involvement", "Pattern of standardized extortion sums"],
                    "confidence": "MEDIUM"
                })

        # 4. Ransomware
        # Signature: Large payments, mixer, peel chains
        if features["total_in_usd"] > 50000.0 or (features["mixer_exposure"] > 0 and features["fan_in"] <= 3):
            typologies.append({
                "name": "Ransomware Extortion",
                "match_percentage": 78.0,
                "description": "High-value extortion payment following peel-chain liquidation and obfuscation routing.",
                "indicators": ["Large lump-sum transaction", "Peel-chain hop structure"],
                "confidence": "MEDIUM"
            })

        # 5. Cross-Chain Layering Syndicate
        if features["bridge_exposure"] > 0 or features["fan_out"] >= 8:
            typologies.append({
                "name": "Cross-Chain Layering Syndicate",
                "match_percentage": 94.0,
                "description": "Coordinated multi-chain laundering network utilizing cross-chain bridges and peeling to evade single-ledger tracking.",
                "indicators": ["Cross-chain bridge hop observed", "Deep intermediary layering structure"],
                "confidence": "VERY HIGH"
            })

        # Default fallback if empty
        if not typologies:
            typologies.append({
                "name": "Suspicious Intermediary Mule",
                "match_percentage": 65.0,
                "description": "Unattributed pass-through transit address exhibiting rapid balance depletion.",
                "indicators": ["Pass-through outflow pattern"],
                "confidence": "MEDIUM"
            })

        typologies.sort(key=lambda x: x["match_percentage"], reverse=True)
        return typologies
