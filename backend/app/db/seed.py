import os
import json
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.app.db.database import engine, SessionLocal, Base
from backend.app.db.models import (
    User, Complaint, Case, CaseComplaint, Wallet, Transfer,
    Label, LabelSource, Entity, EntityAddress, Cluster, ClusterMember,
    Watchlist, Alert, FreezeRequest, Report, CaseNote, Webhook, ApiKey, AuditLog, AppSetting
)
from backend.app.core.security import get_password_hash
from backend.app.core.audit import log_audit_action

# Set fixed seed for deterministic reproducible data
random.seed(42)

def seed_database():
    print("Dropping and recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        print("Seeding demo users...")
        users = [
            User(
                email="investigator@demo",
                hashed_password=get_password_hash("demo123"),
                full_name="Vikram Rathore (IO Cyber Crime)",
                role="Investigator",
                is_active=True
            ),
            User(
                email="supervisor@demo",
                hashed_password=get_password_hash("demo123"),
                full_name="Meera Sharma (SP Cyber Operations)",
                role="Supervisor",
                is_active=True
            ),
            User(
                email="admin@demo",
                hashed_password=get_password_hash("demo123"),
                full_name="System Administrator (Tech Wing)",
                role="Admin",
                is_active=True
            )
        ]
        db.add_all(users)
        db.commit()

        print("Seeding VASP entities and label sources...")
        sources = [
            LabelSource(name="Verified LEA Intel", reliability_weight=0.98, description="Cryptographic seizure or law-enforcement subpoena confirmation"),
            LabelSource(name="VASP Verified Registry", reliability_weight=0.95, description="Officially verified VASP compliance deposit registry"),
            LabelSource(name="ChainNetra Heuristic Engine", reliability_weight=0.85, description="High-confidence deposit sweep pattern detection"),
            LabelSource(name="Community Public Feed", reliability_weight=0.65, description="Open-source fraud reports and victim submissions")
        ]
        db.add_all(sources)
        db.commit()

        vasps = [
            Entity(name="DemoX Exchange", category="Exchange", jurisdiction="Seychelles", compliance_contact="compliance@demox-exchange.example", response_sla="< 2 hours", description="High-volume international trading platform with instant freeze API"),
            Entity(name="NovaTrade", category="Exchange", jurisdiction="Malta", compliance_contact="law-enforcement@novatrade.example", response_sla="< 4 hours", description="Regulated European digital asset brokerage"),
            Entity(name="Zenith OTC", category="OTC Broker", jurisdiction="Dubai (VARA)", compliance_contact="legal@zenith-otc.example", response_sla="< 6 hours", description="Institutional high-value liquidity desk"),
            Entity(name="BharatCoin Express", category="Exchange", jurisdiction="India (FIU-IND)", compliance_contact="nodal@bharatcoin.example", response_sla="< 1 hour", description="FIU-IND registered domestic reporting entity"),
            Entity(name="Apex Custody", category="Custodial Wallet", jurisdiction="Switzerland", compliance_contact="compliance@apexcustody.example", response_sla="< 12 hours", description="Regulated institutional escrow service"),
            Entity(name="VeilMix", category="Mixer", jurisdiction="Decentralized / Anonymous", compliance_contact="none@unregulated.example", response_sla="N/A", description="Zero-knowledge privacy pool and tumbling router"),
            Entity(name="SwiftBridge", category="Bridge", jurisdiction="Decentralized", compliance_contact="ops@swiftbridge.example", response_sla="N/A", description="Cross-chain liquidity bridge router"),
            Entity(name="SwapLab Router", category="DEX", jurisdiction="Decentralized", compliance_contact="support@swaplab.example", response_sla="N/A", description="Automated market maker liquidity router")
        ]
        db.add_all(vasps)
        db.commit()

        # Entity Addresses (Hot wallets, routers, mixers)
        # Tron
        demox = db.query(Entity).filter(Entity.name == "DemoX Exchange").first()
        novatrade = db.query(Entity).filter(Entity.name == "NovaTrade").first()
        zenith = db.query(Entity).filter(Entity.name == "Zenith OTC").first()
        veilmix = db.query(Entity).filter(Entity.name == "VeilMix").first()
        swiftbridge = db.query(Entity).filter(Entity.name == "SwiftBridge").first()
        swaplab = db.query(Entity).filter(Entity.name == "SwapLab Router").first()

        entity_addrs = [
            EntityAddress(entity_id=demox.id, address="TXDemoxHotWalletPrimary88888888888", chain="tron", address_type="hot_wallet"),
            EntityAddress(entity_id=demox.id, address="TXDemoxDepositVault9999999999999", chain="tron", address_type="deposit"),
            EntityAddress(entity_id=novatrade.id, address="0xNovaTradeBscHotWallet7777777777", chain="bsc", address_type="hot_wallet"),
            EntityAddress(entity_id=zenith.id, address="0xZenithArbitrumColdVault666666666", chain="arbitrum", address_type="hot_wallet"),
            EntityAddress(entity_id=veilmix.id, address="bc1qveilmixprivacytumbler00000000", chain="bitcoin", address_type="contract"),
            EntityAddress(entity_id=swiftbridge.id, address="TXSwiftBridgeTronPortal5555555555", chain="tron", address_type="contract"),
            EntityAddress(entity_id=swaplab.id, address="0xSwapLabEthRouterV344444444444444", chain="ethereum", address_type="router")
        ]
        db.add_all(entity_addrs)

        # Labels
        labels = [
            Label(address="TXDemoxHotWalletPrimary88888888888", chain="tron", entity="DemoX Exchange", category="VASP Hot Wallet", source="VASP Verified Registry", confidence=0.99),
            Label(address="TXDemoxDepositVault9999999999999", chain="tron", entity="DemoX Exchange", category="VASP Deposit Address", source="VASP Verified Registry", confidence=0.96),
            Label(address="0xNovaTradeBscHotWallet7777777777", chain="bsc", entity="NovaTrade", category="VASP Hot Wallet", source="VASP Verified Registry", confidence=0.98),
            Label(address="0xZenithArbitrumColdVault666666666", chain="arbitrum", entity="Zenith OTC", category="VASP Deposit Address", source="Verified LEA Intel", confidence=0.95),
            Label(address="bc1qveilmixprivacytumbler00000000", chain="bitcoin", entity="VeilMix", category="Mixer", source="Verified LEA Intel", confidence=0.96),
            Label(address="TXSwiftBridgeTronPortal5555555555", chain="tron", entity="SwiftBridge", category="Bridge", source="VASP Verified Registry", confidence=0.95),
            Label(address="0xSwapLabEthRouterV344444444444444", chain="ethereum", entity="SwapLab Router", category="DEX Router", source="VASP Verified Registry", confidence=0.95)
        ]
        db.add_all(labels)
        db.commit()

        print("Seeding Case Zero: Investment Scam (Guided Demo Scenario)...")
        # Case Zero: 9 victims -> 2 collector wallets on Tron (USDT) -> 3-hop layering -> DemoX Exchange deposit (Nearest VASP in 4 hops, 90%+)
        c0_start_time = datetime.now(timezone.utc) - timedelta(hours=14)
        c0_case = Case(
            case_number="CASE-2026-0001",
            title="Case Zero: High-Yield Telegram Investment Scam",
            description="Syndicate targeting working professionals with fictitious algorithmic trading profits. 9 victims reported cumulative losses of ₹1.12 Crore ($134,500). Funds funneled into 2 Tron collectors and layered toward an offshore exchange.",
            primary_chain="tron",
            primary_address="TXYZCollectorAlpha777111111111111",
            status="Active",
            priority="Critical",
            time_to_vasp_seconds=2.85,
            created_by="investigator@demo",
            created_at=c0_start_time
        )
        db.add(c0_case)
        db.commit()

        # Seed 9 Complaints for Case Zero
        c0_victims = [
            ("Aarav Mehta", "Maharashtra", 1850000, 22155.0),
            ("Pooja Nair", "Karnataka", 1420000, 17006.0),
            ("Rohit Verma", "Delhi", 980000, 11736.0),
            ("Sneha Patel", "Gujarat", 1250000, 14970.0),
            ("Karan Singh", "Punjab", 870000, 10419.0),
            ("Ananya Roy", "West Bengal", 1150000, 13772.0),
            ("Deepak Joshi", "Telangana", 1650000, 19760.0),
            ("Meenal Shah", "Maharashtra", 950000, 11377.0),
            ("Suresh Gupta", "Uttar Pradesh", 1100000, 13173.0)
        ]

        c0_complaint_ids = []
        for idx, (v_name, v_state, inr_amt, usd_amt) in enumerate(c0_victims, start=101):
            c_num = f"NCRP-2026-{idx:06d}"
            target_collector = "TXYZCollectorAlpha777111111111111" if idx % 2 == 1 else "TXYZCollectorBeta888222222222222"
            cmp = Complaint(
                complaint_number=c_num,
                source="NCRP",
                victim_name=v_name,
                victim_state=v_state,
                fraud_type="Investment Scam",
                reported_wallets=json.dumps([target_collector]),
                chain="tron",
                amount_lost_inr=inr_amt,
                amount_lost_usd=usd_amt,
                reported_at=c0_start_time - timedelta(minutes=random.randint(10, 120)),
                status="Assigned",
                priority="Critical"
            )
            db.add(cmp)
            db.commit()
            c0_complaint_ids.append(cmp.id)
            db.add(CaseComplaint(case_id=c0_case.id, complaint_id=cmp.id))

        # Case Zero Transfers
        # Hop 0 -> Hop 1: Victims to Collectors
        t0 = c0_start_time
        transfers_c0 = []
        for i, (v_name, _, _, usd_amt) in enumerate(c0_victims):
            v_addr = f"TVictimWallet{i+1:02d}00000000000000000000"
            dest = "TXYZCollectorAlpha777111111111111" if i % 2 == 0 else "TXYZCollectorBeta888222222222222"
            transfers_c0.append(Transfer(
                chain="tron",
                tx_hash=f"c0_tx_inflow_{i+1:02d}_{random.randint(100000,999999)}",
                block_number=5892010 + i,
                timestamp=t0 + timedelta(minutes=i*10),
                from_address=v_addr,
                to_address=dest,
                token="USDT",
                amount=usd_amt,
                amount_usd=usd_amt
            ))

        # Hop 1 -> Hop 2: Collectors consolidate to Layer 1 Mules
        layer1_a = "TL1MuleAlpha333333333333333333333"
        layer1_b = "TL1MuleBeta444444444444444444444"
        transfers_c0.append(Transfer(
            chain="tron",
            tx_hash=f"c0_tx_layer1_a_{random.randint(100000,999999)}",
            block_number=5892050,
            timestamp=t0 + timedelta(minutes=140),
            from_address="TXYZCollectorAlpha777111111111111",
            to_address=layer1_a,
            token="USDT",
            amount=75000.0,
            amount_usd=75000.0
        ))
        transfers_c0.append(Transfer(
            chain="tron",
            tx_hash=f"c0_tx_layer1_b_{random.randint(100000,999999)}",
            block_number=5892055,
            timestamp=t0 + timedelta(minutes=150),
            from_address="TXYZCollectorBeta888222222222222",
            to_address=layer1_b,
            token="USDT",
            amount=59500.0,
            amount_usd=59500.0
        ))

        # Hop 2 -> Hop 3: Layer 1 splits into Layer 2 transit mules
        layer2_hub = "TL2TransitHub5555555555555555555"
        transfers_c0.append(Transfer(
            chain="tron",
            tx_hash=f"c0_tx_layer2_a_{random.randint(100000,999999)}",
            block_number=5892090,
            timestamp=t0 + timedelta(minutes=210),
            from_address=layer1_a,
            to_address=layer2_hub,
            token="USDT",
            amount=74800.0,
            amount_usd=74800.0
        ))
        transfers_c0.append(Transfer(
            chain="tron",
            tx_hash=f"c0_tx_layer2_b_{random.randint(100000,999999)}",
            block_number=5892095,
            timestamp=t0 + timedelta(minutes=220),
            from_address=layer1_b,
            to_address=layer2_hub,
            token="USDT",
            amount=59300.0,
            amount_usd=59300.0
        ))

        # Hop 3 -> Hop 4: Layer 2 transit hub deposits directly into DemoX Exchange Deposit Vault
        demox_deposit = "TXDemoxDepositVault9999999999999"
        transfers_c0.append(Transfer(
            chain="tron",
            tx_hash="c0_tx_final_deposit_demox_982347102934",
            block_number=5892150,
            timestamp=t0 + timedelta(minutes=300),
            from_address=layer2_hub,
            to_address=demox_deposit,
            token="USDT",
            amount=133500.0,
            amount_usd=133500.0
        ))

        # Hop 4 -> Hot Wallet: DemoX Exchange sweeps from deposit vault to Primary Hot Wallet
        transfers_c0.append(Transfer(
            chain="tron",
            tx_hash="c0_tx_internal_sweep_demox_hotwallet",
            block_number=5892180,
            timestamp=t0 + timedelta(minutes=340),
            from_address=demox_deposit,
            to_address="TXDemoxHotWalletPrimary88888888888",
            token="USDT",
            amount=133500.0,
            amount_usd=133500.0
        ))

        db.add_all(transfers_c0)
        db.commit()

        # Seed Wallets for Case Zero
        c0_wallets = [
            Wallet(address="TXYZCollectorAlpha777111111111111", chain="tron", first_seen=t0, last_seen=t0+timedelta(hours=3), tx_count=10, total_in_usd=75000.0, total_out_usd=75000.0, balance_usd=0.0, risk_score=85.0, risk_level="High", entity_type="Suspect/Collector", label="Suspect Collector Alpha"),
            Wallet(address="TXYZCollectorBeta888222222222222", chain="tron", first_seen=t0, last_seen=t0+timedelta(hours=3), tx_count=8, total_in_usd=59500.0, total_out_usd=59500.0, balance_usd=0.0, risk_score=82.0, risk_level="High", entity_type="Suspect/Collector", label="Suspect Collector Beta"),
            Wallet(address=layer1_a, chain="tron", first_seen=t0+timedelta(minutes=140), last_seen=t0+timedelta(hours=4), tx_count=3, total_in_usd=75000.0, total_out_usd=74800.0, balance_usd=200.0, risk_score=75.0, risk_level="High", entity_type="Intermediary (layering)", label="Mule Layer 1A"),
            Wallet(address=layer1_b, chain="tron", first_seen=t0+timedelta(minutes=150), last_seen=t0+timedelta(hours=4), tx_count=3, total_in_usd=59500.0, total_out_usd=59300.0, balance_usd=200.0, risk_score=75.0, risk_level="High", entity_type="Intermediary (layering)", label="Mule Layer 1B"),
            Wallet(address=layer2_hub, chain="tron", first_seen=t0+timedelta(minutes=210), last_seen=t0+timedelta(hours=5), tx_count=4, total_in_usd=134100.0, total_out_usd=133500.0, balance_usd=600.0, risk_score=80.0, risk_level="High", entity_type="Intermediary (layering)", label="Consolidation Hub Layer 2"),
            Wallet(address=demox_deposit, chain="tron", first_seen=t0+timedelta(minutes=300), last_seen=t0+timedelta(hours=6), tx_count=5, total_in_usd=133500.0, total_out_usd=133500.0, balance_usd=0.0, risk_score=15.0, risk_level="Low", entity_type="VASP deposit address", label="DemoX Exchange Deposit Vault"),
            Wallet(address="TXDemoxHotWalletPrimary88888888888", chain="tron", first_seen=t0, last_seen=t0+timedelta(days=10), tx_count=12000, total_in_usd=95000000.0, total_out_usd=94000000.0, balance_usd=1000000.0, risk_score=5.0, risk_level="Low", entity_type="VASP hot wallet", label="DemoX Primary Hot Wallet")
        ]
        db.add_all(c0_wallets)
        db.commit()

        print("Seeding Scenario 2: Task-Based Fraud (Cross-Chain & Dormant Freeze Candidate)...")
        # Task fraud: Tron -> Burner Fan-out -> Peel Chain -> Tron->BSC Bridge -> NovaTrade deposit + Dormant wallet
        c2_start = datetime.now(timezone.utc) - timedelta(days=2)
        c2_case = Case(
            case_number="CASE-2026-0002",
            title="Task-Based Part-Time Job Fraud (Tron to BSC)",
            description="Online rating task scam. Funds split across 20 burner wallets, peeled via SwiftBridge to BSC, depositing into NovaTrade with ₹34.5 Lakh still dormant in freeze candidate wallet.",
            primary_chain="tron",
            primary_address="TTaskMasterCollector999999999999",
            status="Active",
            priority="High",
            time_to_vasp_seconds=3.4,
            created_by="investigator@demo",
            created_at=c2_start
        )
        db.add(c2_case)
        db.commit()

        # Seed Task Case Transfers
        t2_inflow = 85000.0
        c2_transfers = [
            Transfer(
                chain="tron",
                tx_hash="c2_inflow_victim_consolidate",
                block_number=5889100,
                timestamp=c2_start,
                from_address="TVictimTaskPool01010101010101010",
                to_address="TTaskMasterCollector999999999999",
                token="USDT",
                amount=t2_inflow,
                amount_usd=t2_inflow
            ),
            # Peel chain: Large output (70k) to Bridge, Small peel (15k) to Dormant wallet
            Transfer(
                chain="tron",
                tx_hash="c2_peel_large_to_bridge",
                block_number=5889120,
                timestamp=c2_start + timedelta(minutes=45),
                from_address="TTaskMasterCollector999999999999",
                to_address="TXSwiftBridgeTronPortal5555555555",
                token="USDT",
                amount=45000.0,
                amount_usd=45000.0,
                is_contract_call=True
            ),
            Transfer(
                chain="tron",
                tx_hash="c2_peel_dormant_candidate",
                block_number=5889122,
                timestamp=c2_start + timedelta(minutes=46),
                from_address="TTaskMasterCollector999999999999",
                to_address="TDormantFreezeCandidate40000USD00",
                token="USDT",
                amount=40000.0,
                amount_usd=40000.0
            ),
            # BSC Bridge Release -> Intermediary BSC -> NovaTrade Deposit
            Transfer(
                chain="bsc",
                tx_hash="c2_bsc_bridge_release_tx99",
                block_number=38910200,
                timestamp=c2_start + timedelta(minutes=50),
                from_address="0xSwiftBridgeBscReleaseContract333",
                to_address="0xBscMuleIntermediary8888888888888",
                token="USDT",
                amount=44950.0,
                amount_usd=44950.0
            ),
            Transfer(
                chain="bsc",
                tx_hash="c2_bsc_novatrade_deposit_tx",
                block_number=38910240,
                timestamp=c2_start + timedelta(minutes=80),
                from_address="0xBscMuleIntermediary8888888888888",
                to_address="0xNovaTradeBscHotWallet7777777777",
                token="USDT",
                amount=44900.0,
                amount_usd=44900.0
            )
        ]
        db.add_all(c2_transfers)

        # Dormant holding wallet record with $40,000 (~₹33.4 Lakh) balance
        db.add(Wallet(
            address="TDormantFreezeCandidate40000USD00",
            chain="tron",
            first_seen=c2_start + timedelta(minutes=46),
            last_seen=c2_start + timedelta(minutes=46),
            tx_count=1,
            total_in_usd=40000.0,
            total_out_usd=0.0,
            balance_usd=40000.0,
            risk_score=68.0,
            risk_level="High",
            entity_type="Dormant holding (freeze candidate)",
            label="Dormant Crime Proceeds (Freeze Candidate)"
        ))
        db.commit()

        print("Seeding Scenario 3: Sextortion (Bitcoin & VeilMix Mixer)...")
        c3_start = datetime.now(timezone.utc) - timedelta(days=3)
        c3_case = Case(
            case_number="CASE-2026-0003",
            title="Sextortion Extortion Campaign (Bitcoin & VeilMix)",
            description="Blackmail scam demanding BTC ransoms. Consolidates into VeilMix privacy tumbler with probabilistic continuation.",
            primary_chain="bitcoin",
            primary_address="1BTCCollectorBlackmail1111111111",
            status="Active",
            priority="Medium",
            created_by="investigator@demo",
            created_at=c3_start
        )
        db.add(c3_case)
        db.commit()

        c3_transfers = [
            Transfer(
                chain="bitcoin",
                tx_hash="c3_btc_inflow_victim1",
                block_number=884210,
                timestamp=c3_start,
                from_address="1VictimExtorted01010101010101010",
                to_address="1BTCCollectorBlackmail1111111111",
                token="BTC",
                amount=0.85,
                amount_usd=55250.0
            ),
            Transfer(
                chain="bitcoin",
                tx_hash="c3_btc_deposit_veilmix",
                block_number=884218,
                timestamp=c3_start + timedelta(hours=2),
                from_address="1BTCCollectorBlackmail1111111111",
                to_address="bc1qveilmixprivacytumbler00000000",
                token="BTC",
                amount=0.849,
                amount_usd=55185.0
            ),
            # Mixer candidate withdrawal
            Transfer(
                chain="bitcoin",
                tx_hash="c3_btc_veilmix_candidate_withdrawal",
                block_number=884240,
                timestamp=c3_start + timedelta(hours=6),
                from_address="bc1qveilmixprivacytumbler00000000",
                to_address="bc1qcandidatecashoutaftermix99999",
                token="BTC",
                amount=0.84,
                amount_usd=54600.0
            )
        ]
        db.add_all(c3_transfers)
        db.commit()

        print("Seeding Scenario 4: Ransomware (Ethereum Swap & Arbitrum Bridge to Zenith OTC)...")
        c4_start = datetime.now(timezone.utc) - timedelta(days=4)
        c4_case = Case(
            case_number="CASE-2026-0004",
            title="Healthcare Hospital Ransomware Attack (ETH to Arbitrum)",
            description="Corporate ransomware demand paid in USDT, swapped to ETH via SwapLab Router, bridged to Arbitrum, and deposited to Zenith OTC desk.",
            primary_chain="ethereum",
            primary_address="0xRansomwareSuspectWallet555555555",
            status="Active",
            priority="Critical",
            created_by="investigator@demo",
            created_at=c4_start
        )
        db.add(c4_case)
        db.commit()

        c4_transfers = [
            Transfer(
                chain="ethereum",
                tx_hash="c4_eth_ransom_inflow",
                block_number=19800100,
                timestamp=c4_start,
                from_address="0xVictimHospitalTreasury000000000",
                to_address="0xRansomwareSuspectWallet555555555",
                token="USDT",
                amount=120000.0,
                amount_usd=120000.0
            ),
            Transfer(
                chain="ethereum",
                tx_hash="c4_eth_swaplab_router_deposit",
                block_number=19800115,
                timestamp=c4_start + timedelta(hours=1),
                from_address="0xRansomwareSuspectWallet555555555",
                to_address="0xSwapLabEthRouterV344444444444444",
                token="USDT",
                amount=120000.0,
                amount_usd=120000.0,
                is_contract_call=True
            ),
            Transfer(
                chain="arbitrum",
                tx_hash="c4_arbitrum_bridge_release_tx",
                block_number=21040010,
                timestamp=c4_start + timedelta(hours=3),
                from_address="0xArbitrumBridgeGatewayPortal777",
                to_address="0xZenithArbitrumColdVault666666666",
                token="ETH",
                amount=35.0,
                amount_usd=119000.0
            )
        ]
        db.add_all(c4_transfers)
        db.commit()

        print("Seeding Scenario 5: Multi-Victim Syndicate Cluster (Feeds Case Linking Evidence Board)...")
        # 5 distinct complaints whose funds converge on the common collector cluster
        cluster = Cluster(
            name="Syndicate Cluster #09 (Eurasian Cyber-Financial Network)",
            primary_entity="Common Collector Nexus",
            cluster_type="Same Sweep Target Convergence",
            member_count=5
        )
        db.add(cluster)
        db.commit()

        syndicate_collector = "TSyndicateCoreCollectorNexus77777"
        syndicate_complaints = [
            ("Vikram Singhania", "Gujarat", "Stock Market Investment Scheme", 3200000, 38323.0),
            ("Divya Menon", "Kerala", "Work-from-Home Commission Fraud", 1850000, 22155.0),
            ("Manish Tiwari", "Madhya Pradesh", "Fake Crypto Staking Protocol", 2700000, 32335.0),
            ("Sunita Sen", "Assam", "Telegram Trading Signal Scam", 1400000, 16766.0),
            ("Rakesh Bansal", "Rajasthan", "Pre-IPO Digital Share Fraud", 4500000, 53892.0)
        ]

        syndicate_case = Case(
            case_number="CASE-2026-0005",
            title="Operation Chakra: Multi-State Syndicate Network",
            description="Unified syndicate case merging 5 interstate victim complaints linked to identical collector infrastructure.",
            primary_chain="tron",
            primary_address=syndicate_collector,
            status="Active",
            priority="Critical",
            created_by="supervisor@demo",
            created_at=datetime.now(timezone.utc) - timedelta(days=5)
        )
        db.add(syndicate_case)
        db.commit()

        for idx, (v_name, v_state, f_type, inr_amt, usd_amt) in enumerate(syndicate_complaints, start=301):
            c_num = f"NCRP-2026-{idx:06d}"
            v_wallet = f"TSyndicateVictimWallet{idx:04d}0000000000"
            cmp = Complaint(
                complaint_number=c_num,
                source="SAHYOG" if idx % 2 == 0 else "NCRP",
                victim_name=v_name,
                victim_state=v_state,
                fraud_type=f_type,
                reported_wallets=json.dumps([syndicate_collector]),
                chain="tron",
                amount_lost_inr=inr_amt,
                amount_lost_usd=usd_amt,
                reported_at=datetime.now(timezone.utc) - timedelta(days=random.randint(2, 6)),
                status="Assigned",
                priority="Critical"
            )
            db.add(cmp)
            db.commit()
            db.add(CaseComplaint(case_id=syndicate_case.id, complaint_id=cmp.id))

            # Inflow transfer to common collector
            db.add(Transfer(
                chain="tron",
                tx_hash=f"syndicate_tx_in_{idx}_{random.randint(1000,9999)}",
                block_number=5879000 + idx,
                timestamp=datetime.now(timezone.utc) - timedelta(days=3, hours=idx % 12),
                from_address=v_wallet,
                to_address=syndicate_collector,
                token="USDT",
                amount=usd_amt,
                amount_usd=usd_amt
            ))
            # Add to cluster members
            db.add(ClusterMember(
                cluster_id=cluster.id,
                address=v_wallet,
                chain="tron",
                rule_formed="common_sweep_target"
            ))

        db.add(ClusterMember(
            cluster_id=cluster.id,
            address=syndicate_collector,
            chain="tron",
            rule_formed="syndicate_collector_hub"
        ))
        db.commit()

        print("Seeding 60+ historical cases for analytics...")
        # Historic closed cases with varied response times and VASPs
        chains = ["tron", "ethereum", "bsc", "bitcoin", "polygon", "arbitrum"]
        typology_list = [
            "Investment Scam", "Task-Based Fraud", "Sextortion", "Ransomware",
            "Phishing Drainer", "Darknet Marketplace", "Layering Syndicate"
        ]
        vasp_names = ["DemoX Exchange", "NovaTrade", "Zenith OTC", "BharatCoin Express", "Apex Custody"]

        for i in range(1, 65):
            c_chain = random.choice(chains)
            typ = random.choice(typology_list)
            elapsed_sec = random.uniform(2.1, 14.8) # ChainNetra automated time: seconds!
            c_vasp = random.choice(vasp_names)
            c_date = datetime.now(timezone.utc) - timedelta(days=random.randint(5, 120))
            amt_inr = random.randint(300000, 8500000)
            amt_usd = amt_inr / 83.5

            hist_case = Case(
                case_number=f"CASE-2025-{i:04d}",
                title=f"{typ} Investigation #{i}",
                description=f"Closed investigation resolving fraud proceeds routed through {c_chain.upper()}.",
                primary_chain=c_chain,
                primary_address=f"T0xHistSuspect{i:04d}000000000000000000",
                status="Frozen" if i % 3 == 0 else "Closed",
                priority="High" if amt_usd > 20000 else "Medium",
                time_to_vasp_seconds=round(elapsed_sec, 2),
                created_by="investigator@demo",
                created_at=c_date
            )
            db.add(hist_case)

        db.commit()

        print("Seeding 30 inbox complaints...")
        indian_states = ["Maharashtra", "Karnataka", "Delhi", "Gujarat", "Telangana", "Tamil Nadu", "Uttar Pradesh", "West Bengal", "Punjab", "Rajasthan"]
        for j in range(1, 31):
            s_chain = random.choice(["tron", "ethereum", "bsc", "bitcoin"])
            mock_addr = (
                f"T{random.randint(1000000000, 9999999999)}AbcDefTron" if s_chain == "tron"
                else (f"0x{random.randint(1000000000, 9999999999):x}abcdef40hexevm" if s_chain in ["ethereum", "bsc"]
                else f"bc1q{random.randint(1000000000, 9999999999)}bitcoinaddr")
            )
            c_inr = random.randint(150000, 4500000)
            db.add(Complaint(
                complaint_number=f"NCRP-2026-{900+j:06d}",
                source=random.choice(["NCRP", "SAHYOG", "Bulk", "Manual"]),
                victim_name=f"Victim Citizen {j}",
                victim_state=random.choice(indian_states),
                fraud_type=random.choice(typology_list),
                reported_wallets=json.dumps([mock_addr]),
                chain=s_chain,
                amount_lost_inr=c_inr,
                amount_lost_usd=round(c_inr / 83.5, 2),
                reported_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 720)),
                status="New" if j <= 15 else "Assigned",
                priority="Critical" if c_inr > 2000000 else ("High" if c_inr > 800000 else "Medium")
            ))
        db.commit()

        print("Seeding watchlist and alerts...")
        wl1 = Watchlist(
            address="TDormantFreezeCandidate40000USD00",
            chain="tron",
            label="Dormant Task-Scam Holdings",
            reason="High-value static balance ($40,000 USD)",
            alert_on_outflow=True,
            min_threshold_usd=50.0,
            alert_on_vasp=True,
            is_active=True
        )
        wl2 = Watchlist(
            address="bc1qveilmixprivacytumbler00000000",
            chain="bitcoin",
            label="VeilMix Core Tumbler",
            reason="Privacy tumbler monitoring",
            alert_on_outflow=True,
            min_threshold_usd=100.0,
            alert_on_vasp=True,
            is_active=True
        )
        db.add_all([wl1, wl2])

        al1 = Alert(
            alert_type="REACHED_VASP",
            severity="Critical",
            title="Proceeds Reached DemoX Exchange Deposit Vault",
            message="Case Zero: Funds ($133,500 USDT) deposited into DemoX Exchange. Immediate freeze request recommended.",
            address="TXDemoxDepositVault9999999999999",
            chain="tron",
            case_id=c0_case.id,
            is_acknowledged=False
        )
        al2 = Alert(
            alert_type="DORMANT_WAKE",
            severity="High",
            title="Dormant Wallet Balance Preserved",
            message="Task fraud holding wallet holds $40,000 USDT without outbound movement.",
            address="TDormantFreezeCandidate40000USD00",
            chain="tron",
            case_id=c2_case.id,
            is_acknowledged=False
        )
        al3 = Alert(
            alert_type="MIXER_EXPOSURE",
            severity="High",
            title="Funds Entered VeilMix Privacy Tumbler",
            message="Sextortion proceeds entered VeilMix tumbler pool. Probabilistic tracking mode activated.",
            address="bc1qveilmixprivacytumbler00000000",
            chain="bitcoin",
            case_id=c3_case.id,
            is_acknowledged=False
        )
        db.add_all([al1, al2, al3])

        print("Seeding Freeze Requests...")
        fr1 = FreezeRequest(
            request_number="FR-2026-0001",
            case_id=c0_case.id,
            vasp_id=demox.id,
            vasp_name="DemoX Exchange",
            deposit_address="TXDemoxDepositVault9999999999999",
            suspect_wallet="TXYZCollectorAlpha777111111111111",
            victim_loss_inr=11200000.0,
            victim_loss_usd=134500.0,
            tx_hashes=json.dumps(["c0_tx_final_deposit_demox_982347102934"]),
            status="Pending Approval",
            legal_order_ref="Cr.No 402/2026 U/S 66D IT Act & 420 IPC",
            created_by="investigator@demo"
        )
        db.add(fr1)

        print("Seeding Webhook & Settings...")
        wh = Webhook(
            name="State Cyber Cell SIEM Connector",
            target_url="https://cybercell.gov.example/api/v1/alerts",
            events=json.dumps(["trace_complete", "vasp_found", "freeze_alert", "inbox_complaint"]),
            is_active=True,
            secret="netra_wh_secret_forensic_cell_99"
        )
        db.add(wh)

        settings_list = [
            AppSetting(key="CHAINNETRA_MODE", value="DEMO"),
            AppSetting(key="USD_INR", value="83.50"),
            AppSetting(key="DEFAULT_MAX_DEPTH", value="6"),
            AppSetting(key="DEFAULT_MIN_VALUE_USD", value="50.0"),
            AppSetting(key="DEFAULT_TAINT_MODEL", value="haircut"),
            AppSetting(key="STOP_AT_FIRST_VASP", value="true")
        ]
        db.add_all(settings_list)
        db.commit()

        # Seed initial genesis audit log entry
        print("Logging genesis audit record...")
        log_audit_action(
            db=db,
            user_email="system@chainnetra",
            action="SYSTEM_INIT_AND_SEED",
            entity_type="SYSTEM",
            entity_id="GENESIS",
            details={"mode": "DEMO", "scenarios": 6, "cases": 65, "vasps": 8}
        )

        print("Database successfully seeded with all 6 required forensic scenarios!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
