import pytest
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from app.core.addresses import normalize, display_address, node_key, to_checksum_address
from app.core.service_registry import ServiceRegistry, ServiceEntry
from app.engines.taint import TaintModel, WalletTaintLedger
from app.engines.attribution import AttributionEngine
from app.engines.clustering import ClusteringEngine
from app.engines.crosschain import CrossChainEngine
from app.engines.mixer import MixerEngine
from app.engines.tracer import TracingEngine
from app.adapters.base import ChainAdapter, AddressSummary, Transfer as AdapterTransfer, Transaction, TokenBalance
from app.adapters.factory import register_adapter, clear_custom_adapters
from app.db.models import (
    Transfer as DBTransfer, Wallet as DBWallet, Label, LabelSource,
    Entity, EntityAddress, Cluster, ClusterMember, Case, Complaint, CaseComplaint
)
from app.services.freeze import FreezeService

def test_address_normalization_and_node_keys():
    # EVM lowercase normalization and EIP-55 display
    evm_raw = "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
    evm_norm = normalize("ethereum", evm_raw)
    assert evm_norm == "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
    assert display_address("ethereum", evm_raw) == "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    
    # EVM address on different chains yields distinct node keys
    eth_key = node_key("ethereum", evm_raw)
    polygon_key = node_key("polygon", evm_raw)
    bsc_key = node_key("bsc", evm_raw)
    assert eth_key == "ethereum:0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
    assert polygon_key == "polygon:0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
    assert eth_key != polygon_key
    assert eth_key != bsc_key

    # Tron case-sensitivity preserved: two Tron addresses differing only by case must NOT be merged
    tron_upper = "TYd5q8V6qN8mKxQ5qL4V1wX8Z9yB2cN1Aa"
    tron_lower = "TYd5q8V6qN8mKxQ5qL4V1wX8Z9yB2cN1aa"
    assert normalize("tron", tron_upper) == tron_upper
    assert normalize("tron", tron_lower) == tron_lower
    assert node_key("tron", tron_upper) != node_key("tron", tron_lower)

    # Bitcoin case-sensitivity preserved
    btc_addr1 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    btc_addr2 = "1A1zP1eP5QGefi2DMPTfTL5SLmv7Divfna"
    assert normalize("bitcoin", btc_addr1) == btc_addr1
    assert normalize("bitcoin", btc_addr2) == btc_addr2
    assert node_key("bitcoin", btc_addr1) != node_key("bitcoin", btc_addr2)

def test_taint_models_hand_computed():
    t0 = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=10)
    t2 = t0 + timedelta(minutes=20)
    t3 = t0 + timedelta(minutes=30)
    t4 = t0 + timedelta(minutes=40)

    # 1. Haircut model with mixed clean and tainted inflows
    ledger_haircut = TaintModel.create_ledger("0xwallet1", "ethereum", "haircut")
    ledger_haircut.add_inflow(amount=100.0, tainted_amount=100.0, timestamp=t0, tx_hash="tx_in_1")
    ledger_haircut.add_inflow(amount=100.0, tainted_amount=0.0, timestamp=t1, tx_hash="tx_in_2")

    res1 = ledger_haircut.compute_outflow_taint(50.0, t2, "tx_out_1")
    assert res1.tainted_amount == 25.0
    assert not res1.overestimates
    assert res1.model_name == "haircut"

    res2 = ledger_haircut.compute_outflow_taint(100.0, t3, "tx_out_2")
    assert res2.tainted_amount == 50.0

    res3 = ledger_haircut.compute_outflow_taint(100.0, t4, "tx_out_3")
    assert res3.tainted_amount == 25.0
    assert ledger_haircut.total_tainted_outflow == 100.0
    assert ledger_haircut.total_tainted_outflow <= ledger_haircut.total_tainted_inflow

    # 2. FIFO model with lot consumption
    ledger_fifo = TaintModel.create_ledger("0xwallet2", "ethereum", "fifo")
    ledger_fifo.add_inflow(amount=100.0, tainted_amount=100.0, timestamp=t0, tx_hash="tx_in_1")
    ledger_fifo.add_inflow(amount=100.0, tainted_amount=0.0, timestamp=t1, tx_hash="tx_in_2")

    fifo_out1 = ledger_fifo.compute_outflow_taint(60.0, t2, "tx_out_1")
    assert fifo_out1.tainted_amount == 60.0

    fifo_out2 = ledger_fifo.compute_outflow_taint(80.0, t3, "tx_out_2")
    assert fifo_out2.tainted_amount == 40.0

    fifo_out3 = ledger_fifo.compute_outflow_taint(50.0, t4, "tx_out_3")
    assert fifo_out3.tainted_amount == 0.0
    assert ledger_fifo.total_tainted_outflow == 100.0
    assert ledger_fifo.total_tainted_outflow <= ledger_fifo.total_tainted_inflow

    # 3. Poison model
    ledger_poison = TaintModel.create_ledger("0xwallet3", "ethereum", "poison")
    ledger_poison.add_inflow(amount=100.0, tainted_amount=100.0, timestamp=t0, tx_hash="tx_in_1")

    p_out1 = ledger_poison.compute_outflow_taint(60.0, t2, "tx_p_1")
    assert p_out1.tainted_amount == 60.0
    assert p_out1.overestimates is True

    p_out2 = ledger_poison.compute_outflow_taint(80.0, t3, "tx_p_2")
    assert p_out2.tainted_amount == 80.0
    assert ledger_poison.total_tainted_outflow == 140.0

    # 4. Zero-inflow edge case
    ledger_zero = TaintModel.create_ledger("0xwallet4", "ethereum", "haircut")
    z_out = ledger_zero.compute_outflow_taint(50.0, t0)
    assert z_out.tainted_amount == 0.0

class FakeChainAdapter(ChainAdapter):
    def __init__(self, chain_id: str, transfers_map: Dict[str, List[AdapterTransfer]]):
        self.chain_id = chain_id
        self.transfers_map = transfers_map

    async def get_address_summary(self, address: str) -> AddressSummary:
        return AddressSummary(address=address, chain=self.chain_id, total_received=0.0, total_received_usd=0.0, total_sent=0.0, total_sent_usd=0.0, balance_usd=0.0, tx_count=0)

    async def get_transfers(self, address: str, direction: str = "both", since: Optional[datetime] = None, until: Optional[datetime] = None, limit: int = 100) -> List[AdapterTransfer]:
        txs = self.transfers_map.get(normalize(self.chain_id, address), [])
        filtered = []
        for t in txs:
            if since and t.timestamp < since:
                continue
            if until and t.timestamp > until:
                continue
            filtered.append(t)
        return filtered

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        return None

    async def get_balance(self, address: str) -> List[TokenBalance]:
        return [TokenBalance(token="USDT", symbol="USDT", balance=0.0, balance_usd=0.0)]

    def normalize(self, raw: dict) -> AdapterTransfer:
        return AdapterTransfer(**raw)

@pytest.mark.asyncio
async def test_temporal_soundness_and_time_window(db_session):
    t_arrival = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    t_before = t_arrival - timedelta(hours=2)
    t_inside = t_arrival + timedelta(hours=4)
    t_after = t_arrival + timedelta(hours=80)  # beyond default 72h window

    root = "TCollectorTemporalTest9999"
    target_early = "TMuleTooEarly00000000000"
    target_valid = "TMuleValidWindow00000000"
    target_late = "TMuleTooLate000000000000"

    fake_txs = {
        normalize("tron", root): [
            AdapterTransfer(chain="tron", tx_hash="tx_before", timestamp=t_before, from_address=root, to_address=target_early, amount=1000.0, amount_usd=1000.0),
            AdapterTransfer(chain="tron", tx_hash="tx_valid", timestamp=t_inside, from_address=root, to_address=target_valid, amount=1000.0, amount_usd=1000.0),
            AdapterTransfer(chain="tron", tx_hash="tx_late", timestamp=t_after, from_address=root, to_address=target_late, amount=1000.0, amount_usd=1000.0),
        ]
    }
    fake_ad = FakeChainAdapter("tron", fake_txs)
    register_adapter("tron", fake_ad)

    try:
        tracer = TracingEngine(
            db=db_session,
            case_id=999,
            start_address=root,
            chain="tron",
            initial_amount_usd=1000.0,
            start_time=t_arrival,
            time_window_hours=72
        )
        res = await tracer.execute_trace(job_id="test-temporal-job")

        node_keys = [n["id"] for n in res["nodes"]]
        # target_valid MUST be included
        assert node_key("tron", target_valid) in node_keys
        # target_early (before arrival) and target_late (after 72h window) MUST NOT be included
        assert node_key("tron", target_early) not in node_keys
        assert node_key("tron", target_late) not in node_keys
    finally:
        clear_custom_adapters()

@pytest.mark.asyncio
async def test_peel_chain_generalized_and_minimum_hops(db_session):
    t0 = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
    # Construct 4-hop chain: Root -> Hop1 -> Hop2 -> Hop3 -> Hop4
    # Each hop: 1 large continuing output (85% > 80%) + multiple small peels
    h0 = "TPeelHop0Root000000000000000"
    h1 = "TPeelHop1Dominant00000000000"
    h2 = "TPeelHop2Dominant00000000000"
    h3 = "TPeelHop3Dominant00000000000"
    h4 = "TPeelHop4Dominant00000000000"

    fake_txs = {
        normalize("tron", h0): [
            AdapterTransfer(chain="tron", tx_hash="tx_p1", timestamp=t0 + timedelta(minutes=10), from_address=h0, to_address=h1, amount=850.0, amount_usd=850.0),
            AdapterTransfer(chain="tron", tx_hash="tx_p1_peel1", timestamp=t0 + timedelta(minutes=10), from_address=h0, to_address="TPeelSmall1A00000000000000", amount=100.0, amount_usd=100.0),
            AdapterTransfer(chain="tron", tx_hash="tx_p1_peel2", timestamp=t0 + timedelta(minutes=10), from_address=h0, to_address="TPeelSmall1B00000000000000", amount=50.0, amount_usd=50.0),
        ],
        normalize("tron", h1): [
            AdapterTransfer(chain="tron", tx_hash="tx_p2", timestamp=t0 + timedelta(minutes=20), from_address=h1, to_address=h2, amount=720.0, amount_usd=720.0),
            AdapterTransfer(chain="tron", tx_hash="tx_p2_peel", timestamp=t0 + timedelta(minutes=20), from_address=h1, to_address="TPeelSmall2000000000000000", amount=130.0, amount_usd=130.0),
        ],
        normalize("tron", h2): [
            AdapterTransfer(chain="tron", tx_hash="tx_p3", timestamp=t0 + timedelta(minutes=30), from_address=h2, to_address=h3, amount=600.0, amount_usd=600.0),
            AdapterTransfer(chain="tron", tx_hash="tx_p3_peel", timestamp=t0 + timedelta(minutes=30), from_address=h2, to_address="TPeelSmall3000000000000000", amount=120.0, amount_usd=120.0),
        ],
        normalize("tron", h3): [
            AdapterTransfer(chain="tron", tx_hash="tx_p4", timestamp=t0 + timedelta(minutes=40), from_address=h3, to_address=h4, amount=500.0, amount_usd=500.0),
            AdapterTransfer(chain="tron", tx_hash="tx_p4_peel", timestamp=t0 + timedelta(minutes=40), from_address=h3, to_address="TPeelSmall4000000000000000", amount=100.0, amount_usd=100.0),
        ]
    }
    fake_ad = FakeChainAdapter("tron", fake_txs)
    register_adapter("tron", fake_ad)

    try:
        tracer = TracingEngine(
            db=db_session,
            case_id=998,
            start_address=h0,
            chain="tron",
            initial_amount_usd=1000.0,
            start_time=t0,
            peel_chain_ratio=0.80
        )
        res = await tracer.execute_trace(job_id="test-peel-job")

        assert len(res["peel_chains"]) >= 1
        peel_chain = res["peel_chains"][0]
        assert peel_chain["hops"] >= 3
        assert len(peel_chain["wallets"]) >= 4
    finally:
        clear_custom_adapters()

def test_confidence_scoring_from_real_evidence():
    # 1. Fresh label vs 2-year old stale label
    fresh_conf = AttributionEngine.calculate_confidence(
        label_source_weight=0.98,
        evidence_strength=1.0,
        cluster_support=0.0,
        hops_from_label=0,
        label_age_days=10
    )
    stale_conf = AttributionEngine.calculate_confidence(
        label_source_weight=0.98,
        evidence_strength=1.0,
        cluster_support=0.0,
        hops_from_label=0,
        label_age_days=750
    )
    assert fresh_conf["confidence_score"] > stale_conf["confidence_score"]
    assert fresh_conf["confidence_level"] == "VERIFIED"

    # 2. Cluster support ratio variation
    high_support_conf = AttributionEngine.calculate_confidence(
        label_source_weight=0.85,
        evidence_strength=0.75,
        cluster_support=0.90,  # 9/10 members support
        hops_from_label=1
    )
    low_support_conf = AttributionEngine.calculate_confidence(
        label_source_weight=0.85,
        evidence_strength=0.75,
        cluster_support=0.10,  # 1/10 members support
        hops_from_label=1
    )
    assert high_support_conf["confidence_score"] > low_support_conf["confidence_score"]
    assert high_support_conf["confidence_score"] != 95.0
    assert low_support_conf["cluster_support"] == 0.10

def test_deposit_address_sweep_heuristic(db_session):
    # Setup VASP Hot Wallet
    hot_addr = normalize("tron", "THotWalletKnownVasp1111111111111")
    ent = Entity(name="TestExchange", category="Exchange")
    db_session.add(ent)
    db_session.commit()
    db_session.add(EntityAddress(entity_id=ent.id, address=hot_addr, chain="tron", address_type="hot_wallet"))
    db_session.commit()

    # Case A: True Deposit Pattern (3 senders, >=90% swept to hot wallet across 2 sweeps)
    dep_wallet = normalize("tron", "TTrueDepositAddress222222222222")
    t0 = datetime(2026, 9, 30, 8, 0, 0)
    db_session.add_all([
        DBTransfer(chain="tron", tx_hash="in1", timestamp=t0, from_address="TSender1", to_address=dep_wallet, amount=100.0, amount_usd=100.0),
        DBTransfer(chain="tron", tx_hash="in2", timestamp=t0+timedelta(minutes=5), from_address="TSender2", to_address=dep_wallet, amount=200.0, amount_usd=200.0),
        DBTransfer(chain="tron", tx_hash="in3", timestamp=t0+timedelta(minutes=10), from_address="TSender3", to_address=dep_wallet, amount=300.0, amount_usd=300.0),
        DBTransfer(chain="tron", tx_hash="sw1", timestamp=t0+timedelta(minutes=30), from_address=dep_wallet, to_address=hot_addr, amount=290.0, amount_usd=290.0),
        DBTransfer(chain="tron", tx_hash="sw2", timestamp=t0+timedelta(minutes=40), from_address=dep_wallet, to_address=hot_addr, amount=300.0, amount_usd=300.0),
    ])
    db_session.commit()

    dep_attr = AttributionEngine.resolve_label(db_session, dep_wallet, "tron")
    assert dep_attr is not None
    assert dep_attr["category"] == "VASP Deposit Address"
    assert dep_attr["confidence"] >= 65.0
    assert dep_attr["confidence_level"] == "HIGH"

    # Case B: Mule single transfer (1 sender, 1 payment to exchange hot wallet)
    mule_wallet = normalize("tron", "TMuleSinglePayment333333333333")
    db_session.add_all([
        DBTransfer(chain="tron", tx_hash="m_in", timestamp=t0, from_address="TVictimA", to_address=mule_wallet, amount=500.0, amount_usd=500.0),
        DBTransfer(chain="tron", tx_hash="m_out", timestamp=t0+timedelta(minutes=20), from_address=mule_wallet, to_address=hot_addr, amount=500.0, amount_usd=500.0),
    ])
    db_session.commit()

    mule_attr = AttributionEngine.resolve_label(db_session, mule_wallet, "tron")
    assert mule_attr is not None
    assert mule_attr["category"] == "Direct Sender to VASP Hot Wallet"
    assert mule_attr["category"] != "VASP Deposit Address"

def test_clustering_engine_forensic_rules(db_session):
    t0 = datetime(2026, 9, 30, 8, 0, 0)
    
    # 1. Non-service sweep clustering
    target_mule = normalize("tron", "TIntermediaryMuleHub4444444444")
    db_session.add_all([
        DBTransfer(chain="tron", tx_hash="s_in1", timestamp=t0, from_address="TSenderAlpha1", to_address=target_mule, amount=100.0, amount_usd=100.0),
        DBTransfer(chain="tron", tx_hash="s_in2", timestamp=t0+timedelta(hours=2), from_address="TSenderBeta2", to_address=target_mule, amount=150.0, amount_usd=150.0),
    ])
    db_session.commit()

    clusters = ClusteringEngine.identify_sweep_clusters(db_session, "tron", window_hours=24)
    assert len(clusters) >= 1
    assert any(c["target_address"] == target_mule for c in clusters)

    # 2. Service sweep exclusion: VASP hot wallet must NOT cluster depositors
    vasp_hot = normalize("tron", "TXDemoxHotWalletPrimary88888888888")
    db_session.add_all([
        DBTransfer(chain="tron", tx_hash="v_in1", timestamp=t0, from_address="TUnrelatedCustomer1", to_address=vasp_hot, amount=100.0, amount_usd=100.0),
        DBTransfer(chain="tron", tx_hash="v_in2", timestamp=t0+timedelta(hours=1), from_address="TUnrelatedCustomer2", to_address=vasp_hot, amount=200.0, amount_usd=200.0),
    ])
    db_session.commit()

    vasp_clusters = [c for c in ClusteringEngine.identify_sweep_clusters(db_session, "tron", window_hours=24) if c["target_address"] == vasp_hot]
    assert len(vasp_clusters) == 0  # Service exclusion prevents clustering unrelated customers

    # 3. Bitcoin CoinJoin exclusion vs standard common-input
    # CoinJoin: 5 equal outputs of 0.1 BTC -> MUST be skipped
    db_session.add_all([
        DBTransfer(chain="bitcoin", tx_hash="tx_coinjoin_1", timestamp=t0, from_address="1In1", to_address="1Out1", amount=0.10, amount_usd=6500.0),
        DBTransfer(chain="bitcoin", tx_hash="tx_coinjoin_1", timestamp=t0, from_address="1In2", to_address="1Out2", amount=0.10, amount_usd=6500.0),
        DBTransfer(chain="bitcoin", tx_hash="tx_coinjoin_1", timestamp=t0, from_address="1In3", to_address="1Out3", amount=0.10, amount_usd=6500.0),
    ])
    # Standard multi-input: unequal outputs -> clustered
    db_session.add_all([
        DBTransfer(chain="bitcoin", tx_hash="tx_standard_multi_in", timestamp=t0, from_address="1StdIn1", to_address="1StdOut1", amount=0.45, amount_usd=29250.0),
        DBTransfer(chain="bitcoin", tx_hash="tx_standard_multi_in", timestamp=t0, from_address="1StdIn2", to_address="1StdOut2", amount=0.12, amount_usd=7800.0),
    ])
    db_session.commit()

    btc_clusters = ClusteringEngine.identify_btc_common_input_clusters(db_session)
    # Assert CoinJoin was excluded
    assert not any("tx_coinjoin_1" in c.get("evidence_tx_hashes", []) for c in btc_clusters)
    # Assert standard was included
    assert any("tx_standard_multi_in" in c.get("evidence_tx_hashes", []) for c in btc_clusters)

    # 4. Idempotence test
    m1 = ClusteringEngine.add_address_to_cluster(db_session, "TestCluster1", "EntityA", "TAddr111", "tron", "rule1")
    m2 = ClusteringEngine.add_address_to_cluster(db_session, "TestCluster1", "EntityA", "TAddr111", "tron", "rule1")
    assert m1.id == m2.id

def test_service_registry_mixer_bridge_dex(db_session):
    # 1. Unregistered address with 'mix' or 'bridge' in string must NOT match
    fake_mix = "0xnotarealmixwallet1234567890123456789012"
    fake_bridge = "0xnotarealbridgewallet123456789012345678"
    assert not ServiceRegistry.is_mixer("ethereum", fake_mix)
    assert not ServiceRegistry.is_bridge("ethereum", fake_bridge)

    # 2. Registered mixer
    assert ServiceRegistry.is_mixer("bitcoin", "bc1qveilmixprivacytumbler00000000")

    # 3. Ambiguous bridge candidates (score within 5 points)
    t0 = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
    bridge_portal = "TXSwiftBridgeTronPortal5555555555"
    db_session.add_all([
        DBTransfer(chain="bsc", tx_hash="tx_cand1", timestamp=t0+timedelta(minutes=15), from_address="0xswiftbridgebscreleasecontract333", to_address="0xDestWallet1", amount=100.0, amount_usd=100.0),
        DBTransfer(chain="bsc", tx_hash="tx_cand2", timestamp=t0+timedelta(minutes=16), from_address="0xswiftbridgebscreleasecontract333", to_address="0xDestWallet2", amount=100.0, amount_usd=100.0),
    ])
    db_session.commit()

    match_res = CrossChainEngine.match_bridge_transfer(
        db=db_session,
        source_chain="tron",
        source_tx_hash="src_tx_hash",
        bridge_deposit_address=bridge_portal,
        deposit_amount=100.0,
        deposit_time=t0
    )
    assert match_res is not None
    assert match_res["is_ambiguous"] is True

def test_no_hardcoded_constants_and_honest_timing(db_session):
    # 1. Create case with no linked complaints -> freeze service requires explicit amount or defaults to 0
    case = Case(title="No Complaint Case", primary_chain="tron", primary_address="TSuspectNoComplaint9999", created_by="investigator@demo")
    db_session.add(case)
    db_session.commit()

    fr = FreezeService.create_freeze_request(
        db=db_session,
        case_id=case.id,
        vasp_id=1,
        deposit_address="TDep999",
        suspect_wallet="TSuspectNoComplaint9999",
        legal_order_ref="Order #1",
        notes="Notes",
        created_by="investigator@demo"
    )
    # Must NOT return hardcoded 11200000.0 or 134500.0
    assert fr.victim_loss_inr == 0.0
    assert fr.victim_loss_usd == 0.0

@pytest.mark.asyncio
async def test_trace_budget_and_no_vasp_timing(db_session):
    # Trace where no VASP is encountered -> time_to_vasp_seconds must be None
    t0 = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
    root = "TSuspectDeadEnd88888888"
    fake_txs = {
        normalize("tron", root): [
            AdapterTransfer(chain="tron", tx_hash="tx1", timestamp=t0+timedelta(minutes=5), from_address=root, to_address="TMuleEnd1", amount=100.0, amount_usd=100.0)
        ]
    }
    fake_ad = FakeChainAdapter("tron", fake_txs)
    register_adapter("tron", fake_ad)

    try:
        tracer = TracingEngine(
            db=db_session,
            case_id=101,
            start_address=root,
            chain="tron",
            initial_amount_usd=100.0,
            start_time=t0,
            max_adapter_calls=1  # Limit budget
        )
        res = await tracer.execute_trace(job_id="test-budget-job")
        assert res["time_to_vasp_seconds"] is None
        assert res["adapter_call_count"] >= 1
    finally:
        clear_custom_adapters()
