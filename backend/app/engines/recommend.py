from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.core.config import settings

class RecommendationEngine:
    @staticmethod
    def generate_recommendations(
        attributions: List[Dict[str, Any]],
        dormant_wallets: List[Dict[str, Any]],
        mixer_events: List[Dict[str, Any]],
        cross_chain_events: List[Dict[str, Any]],
        complaint_matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        recommendations = []

        # 1. Freeze Request on identified VASPs
        for attr in attributions:
            vasp = attr.get("vasp_name", "Identified VASP")
            deposit_addr = attr.get("deposit_address", "")
            amt = attr.get("amount", 0.0)
            inr_val = amt * settings.USD_INR
            conf = attr.get("confidence_score", 90.0)

            recommendations.append({
                "priority": "CRITICAL",
                "action_type": "FREEZE_REQUEST",
                "title": f"Dispatch Emergency Freeze Request to {vasp}",
                "description": f"Target deposit address {deposit_addr} received ${amt:,.2f} (~₹{inr_val:,.0f}). Immediate account restraint required before fiat off-ramp.",
                "rationale": f"Attribution confidence {conf:.1f}% backed by verified VASP deposit heuristic.",
                "target_address": deposit_addr,
                "target_vasp": vasp,
                "urgency_badge": "Immediate (< 4 Hours)"
            })

            recommendations.append({
                "priority": "HIGH",
                "action_type": "PRESERVE_LOGS",
                "title": f"Submit Log & KYC Preservation Notice to {vasp}",
                "description": f"Request mandatory 90-day preservation of KYC records, login IP audit trails, device fingerprints, and linked fiat bank accounts for deposit address {deposit_addr}.",
                "rationale": "Crucial for identifying beneficiary account holder identity under CrPC Section 91 / IT Act.",
                "target_address": deposit_addr,
                "target_vasp": vasp,
                "urgency_badge": "High Priority"
            })

        # 2. Dormant Holdings
        for dorm in dormant_wallets:
            d_addr = dorm.get("address", "")
            bal = dorm.get("balance_usd", 0.0)
            inr_bal = bal * settings.USD_INR
            recommendations.append({
                "priority": "HIGH",
                "action_type": "WATCHLIST_ADD",
                "title": f"Monitor Dormant Holding Wallet ({d_addr[:8]}...)",
                "description": f"Wallet holds ${bal:,.2f} (~₹{inr_bal:,.0f}) with no recent outbound transfers. Set automated alerts for sudden movement.",
                "rationale": "Static balance represents directly recoverable crime proceeds if swift action is taken upon outflow.",
                "target_address": d_addr,
                "target_vasp": None,
                "urgency_badge": "Active Watch"
            })

        # 3. Mixer notices
        for mix in mixer_events:
            recommendations.append({
                "priority": "MEDIUM",
                "action_type": "PROBABILISTIC_CAVEAT",
                "title": "Mixer Tumbler Entry Caveat",
                "description": f"Funds routed into privacy pool at {mix.get('timestamp')}. Downstream attributions carry probabilistic uncertainty. Corroborate with off-chain lead.",
                "rationale": "Tumbler mixing pools obfuscate deterministic transaction graphs.",
                "target_address": mix.get("target_address"),
                "target_vasp": None,
                "urgency_badge": "Forensic Note"
            })

        # 4. Cross-complaint link
        for match in complaint_matches:
            c_num = match.get("complaint_number")
            recommendations.append({
                "priority": "HIGH",
                "action_type": "CROSS_LINK_CASE",
                "title": f"Syndicate Alert: Cross-Reference Complaint {c_num}",
                "description": f"Target wallet appeared in earlier cybercrime complaint {c_num}. Recommend merging into multi-jurisdiction syndicate dossier.",
                "rationale": "Common beneficiary infrastructure links separate cybercrime occurrences into single organised syndicate.",
                "target_address": match.get("address"),
                "target_vasp": None,
                "urgency_badge": "Syndicate Lead"
            })

        return recommendations
