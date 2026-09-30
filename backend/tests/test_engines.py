import pytest
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from app.adapters.base import ChainAdapter, Transfer, AddressSummary, Transaction, TokenBalance, AdapterError
from app.adapters.factory import register_adapter
from app.engines.taint import TaintModel
from app.engines.attribution import AttributionEngine
from app.engines.tracer import TracingEngine
from app.engines.crosschain import CrossChainEngine
from app.engines.mixer import MixerEngine
from app.services.ingest import IngestionService
from app.services.freeze import FreezeService
from app.core.audit import log_audit_action, verify_audit_chain
from app.db.models import Case, Label, Entity, EntityAddress, Transfer as DBTransfer, FreezeRequest

class MockGraphAdapter(ChainAdapter):
    def __init__(self, chain_id: str, graph: dict, should_fail_on: Optional[str] = None):
        self.chain_id = chain_id
        self.graph = graph  # from_addr -> list of Transfer
        self.should_fail_on = should_fail_on

    async def get_address_summary(self, address: str) -> AddressSummary:
        return AddressSummary(
            address=address,
            chain=self.chain_id,
            total_received=1000.0,
            total_received_usd=1000.0,
            total_sent=1000.0,
            total_sent_usd=1000.0,
            balance_usd=0.0,
            tx_count=len(self.graph.get(address.lower(), []))
        )

    async def get_transfers(
        self,
        address: str,
        direction: str = "both",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Transfer]:
        if self.should_fail_on and address.lower() == self.should_fail_on.lower():
            raise AdapterError(f"Simulated network drop for {address}")
        txs = self.graph.get(address.lower(), [])
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

    def normalize(self, raw: dict) -> Transfer:
        return Transfer(**raw)


# 1. Taint Model Edge Cases
def test_taint_models_edge_cases():
    # Haircut model
    assert TaintModel.calculate_taint("haircut", 500.0, 1000.0, 200.0) == 100.0
    # Zero inflow edge case
    assert TaintModel.calculate_taint("haircut", 0.0, 0.0, 200.0) == 0.0
    # Zero outflow
    assert TaintModel.calculate_taint("haircut", 500.0, 1000.0, 0.0) == 0.0

    # FIFO model
    assert TaintModel.calculate_taint("fifo", 500.0, 1000.0, 200.0, remaining_taint_balance=150.0) == 150.0
    assert TaintModel.calculate_taint("fifo", 500.0, 1000.0, 300.0, remaining_taint_balance=500.0) == 300.0

    # Poison model (capped by total tainted inflow)
    assert TaintModel.calculate_taint("poison", 50.0, 1000.0, 300.0) == 50.0
    assert TaintModel.calculate_taint("poison", 500.0, 1000.0, 300.0) == 300.0
    assert TaintModel.calculate_taint("poison", 0.0, 1000.0, 300.0) == 0.0


# 2. Ingest Address Validation (Real Tron, EVM, BTC)
def test_address_validation_real_formats():
    # Real Tron base58 addresses
    assert IngestionService.detect_chain_and_validate("TYDzsYUE2UtZZTqXz31eS7x7ZnyQ7vX5rA")["valid"] is True
    assert IngestionService.detect_chain_and_validate("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")["chain"] == "tron"

    # Real EVM EIP-55 addresses
    assert IngestionService.detect_chain_and_validate("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")["valid"] is True
    assert IngestionService.detect_chain_and_validate("0x00000000219ab540356cbb839cbe05303d7705fa")["chain"] == "ethereum"

    # Real Bitcoin (Bech32 and legacy)
    assert IngestionService.detect_chain_and_validate("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq")["valid"] is True
    assert IngestionService.detect_chain_and_validate("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")["valid"] is True
    assert IngestionService.detect_chain_and_validate("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy")["valid"] is True

    # Invalid addresses
    assert IngestionService.detect_chain_and_validate("invalid_crypto_addr")["valid"] is False
    assert IngestionService.detect_chain_and_validate("0xinvalid_evm_length")["valid"] is False


from app.core.addresses import node_key
from app.core.service_registry import ServiceRegistry, ServiceEntry

# 3. Hand-Built Graph Tracing & Stop at First VASP
@pytest.mark.asyncio
async def test_tracer_hand_built_graph(db_session):
    # Setup hand-built graph: Suspect -> Mule1 -> Mule2 -> Binance Hot Wallet
    suspect_addr = "0xsuspect000000000000000000000000000000001"
    mule1_addr = "0xmule000000000000000000000000000000000002"
    mule2_addr = "0xmule000000000000000000000000000000000003"
    exchange_addr = "0xbinancehotwallet000000000000000000000004"
    extra_addr = "0xextraunreachable000000000000000000000005"

    now = datetime.now(timezone.utc)

    # Insert Label for Binance Hot Wallet
    db_session.add(Label(
        address=exchange_addr,
        chain="ethereum",
        entity="Binance",
        category="VASP deposit address",
        source="Exchange Registry",
        confidence=0.95
    ))

    # Insert Case
    case = Case(
        case_number="CASE-TEST-0001",
        title="Synthetic Graph Test Case",
        primary_chain="ethereum",
        primary_address=suspect_addr,
        status="Active",
        priority="High",
        created_by="tester@demo"
    )
    db_session.add(case)
    db_session.commit()

    graph = {
        suspect_addr.lower(): [
            Transfer(chain="ethereum", tx_hash="tx1", timestamp=now, from_address=suspect_addr, to_address=mule1_addr, token="USDT", amount=10000.0, amount_usd=10000.0)
        ],
        mule1_addr.lower(): [
            Transfer(chain="ethereum", tx_hash="tx2", timestamp=now, from_address=mule1_addr, to_address=mule2_addr, token="USDT", amount=9900.0, amount_usd=9900.0)
        ],
        mule2_addr.lower(): [
            Transfer(chain="ethereum", tx_hash="tx3", timestamp=now, from_address=mule2_addr, to_address=exchange_addr, token="USDT", amount=9800.0, amount_usd=9800.0),
            Transfer(chain="ethereum", tx_hash="tx4", timestamp=now, from_address=mule2_addr, to_address=extra_addr, token="USDT", amount=100.0, amount_usd=100.0)
        ],
        exchange_addr.lower(): [
            Transfer(chain="ethereum", tx_hash="tx5", timestamp=now, from_address=exchange_addr, to_address=extra_addr, token="USDT", amount=5000.0, amount_usd=5000.0)
        ]
    }

    mock_adapter = MockGraphAdapter("ethereum", graph)
    register_adapter("ethereum", mock_adapter)

    # A) Trace with stop_at_first_vasp=True
    tracer = TracingEngine(
        db=db_session,
        case_id=case.id,
        start_address=suspect_addr,
        chain="ethereum",
        initial_amount_usd=10000.0,
        max_depth=5,
        min_value_usd=50.0,
        stop_at_first_vasp=True
    )
    res = await tracer.execute_trace("job_test_1")
    assert len(res["attributions"]) >= 1
    assert res["attributions"][0]["vasp_name"] == "Binance"
    assert res["attributions"][0]["hops_from_suspect"] == 3
    assert res["is_complete"] is True

    # Confirm exchange_addr did not continue tracing further
    assert not any(e["source"] == node_key("ethereum", exchange_addr) for e in res["edges"])


# 4. Tracer Incomplete Branch Handling on AdapterError
@pytest.mark.asyncio
async def test_tracer_incomplete_branch_on_error(db_session):
    suspect_addr = "0xsuspect_fail_00000000000000000000000001"
    mule_failing = "0xmule_failing_00000000000000000000000002"
    mule_working = "0xmule_working_00000000000000000000000003"
    exchange_addr = "0xexchangeworking00000000000000000000004"

    now = datetime.now(timezone.utc)

    db_session.add(Label(
        address=exchange_addr,
        chain="ethereum",
        entity="Kraken",
        category="VASP deposit address",
        source="Registry",
        confidence=0.90
    ))

    case = Case(
        case_number="CASE-TEST-0002",
        title="Failing Branch Case",
        primary_chain="ethereum",
        primary_address=suspect_addr,
        status="Active",
        priority="High"
    )
    db_session.add(case)
    db_session.commit()

    graph = {
        suspect_addr.lower(): [
            Transfer(chain="ethereum", tx_hash="tx_fail", timestamp=now, from_address=suspect_addr, to_address=mule_failing, token="USDT", amount=5000.0, amount_usd=5000.0),
            Transfer(chain="ethereum", tx_hash="tx_work", timestamp=now, from_address=suspect_addr, to_address=mule_working, token="USDT", amount=5000.0, amount_usd=5000.0)
        ],
        mule_working.lower(): [
            Transfer(chain="ethereum", tx_hash="tx_to_ex", timestamp=now, from_address=mule_working, to_address=exchange_addr, token="USDT", amount=4900.0, amount_usd=4900.0)
        ]
    }

    mock_adapter = MockGraphAdapter("ethereum", graph, should_fail_on=mule_failing)
    register_adapter("ethereum", mock_adapter)

    tracer = TracingEngine(
        db=db_session,
        case_id=case.id,
        start_address=suspect_addr,
        chain="ethereum",
        initial_amount_usd=10000.0,
        max_depth=4,
        min_value_usd=50.0
    )
    res = await tracer.execute_trace("job_test_fail")
    
    # Assert failing branch was caught and recorded as incomplete branch
    assert len(res["incomplete_branches"]) >= 1
    assert any(b["address"] == mule_failing for b in res["incomplete_branches"])
    assert res["is_complete"] is False
    
    # Assert working branch continued and found Kraken attribution
    assert len(res["attributions"]) >= 1
    assert res["attributions"][0]["vasp_name"] == "Kraken"


# 5. Cross-Chain Bridge Matching
def test_crosschain_bridge_matcher(db_session):
    now = datetime.now(timezone.utc)
    
    # Deposit transaction on Tron
    bridge_contract = "TBridgeContractOfficial7777777777"
    dest_wallet = "0xDestinationUserWallet888888888888888888"

    ServiceRegistry.register(ServiceEntry(
        chain="tron",
        address=bridge_contract,
        kind="bridge",
        name="Official Bridge",
        source="Official"
    ))

    # Insert release transfer in database
    db_session.add(DBTransfer(
        chain="ethereum",
        tx_hash="0xeth_bridge_release_tx_999",
        timestamp=now + timedelta(seconds=90),
        from_address="0xbridgevaultrouter0000000000000000000000",
        to_address=dest_wallet,
        token="USDT",
        amount=10000.0,
        amount_usd=10000.0,
        is_contract_call=True
    ))
    db_session.commit()

    # 1. Matching bridge transfer
    match = CrossChainEngine.match_bridge_transfer(
        db=db_session,
        source_chain="tron",
        source_tx_hash="tron_tx_123",
        bridge_deposit_address=bridge_contract,
        deposit_amount=10000.0,
        deposit_time=now
    )
    assert match is not None
    assert match["destination_chain"] == "ethereum"
    assert match["destination_wallet"] == dest_wallet
    assert match["confidence"] >= 60.0

    # 2. No matching transfer (different time window)
    no_match = CrossChainEngine.match_bridge_transfer(
        db=db_session,
        source_chain="tron",
        source_tx_hash="tron_tx_999",
        bridge_deposit_address=bridge_contract,
        deposit_amount=999999.0,
        deposit_time=now
    )
    assert no_match is None


# 6. Mixer Pool Matching
def test_mixer_matcher(db_session):
    now = datetime.now(timezone.utc)
    mixer_addr = "bc1qmixerprivacyvault0000000000000000"

    ServiceRegistry.register(ServiceEntry(
        chain="bitcoin",
        address=mixer_addr,
        kind="mixer",
        name="Privacy Mixer",
        source="Test",
        denominations=[0.1, 0.5, 1.0, 5.0, 10.0]
    ))

    # Insert mixer pool withdrawal
    db_session.add(DBTransfer(
        chain="bitcoin",
        tx_hash="btc_mixer_out_tx_1",
        timestamp=now + timedelta(minutes=45),
        from_address=mixer_addr,
        to_address="bc1qrecipientanonymous00000000000000000",
        token="BTC",
        amount=1.0,
        amount_usd=60000.0
    ))
    db_session.commit()

    candidates = MixerEngine.match_mixer_pool_withdrawals(
        db=db_session,
        chain="bitcoin",
        mixer_address=mixer_addr,
        deposit_amount=1.0,
        deposit_time=now
    )
    assert len(candidates) == 1
    assert candidates[0]["target_address"] == "bc1qrecipientanonymous00000000000000000"
    assert candidates[0]["time_delta_minutes"] == 45


# 7. Freeze Request Service Workflow
def test_freeze_service_workflow(db_session):
    entity = Entity(
        name="CoinDCX Exchange",
        category="VASP",
        jurisdiction="India",
        compliance_contact="compliance@coindcx.demo",
        response_sla="2 Hours"
    )
    db_session.add(entity)
    db_session.commit()

    # Create freeze request
    fr = FreezeService.create_freeze_request(
        db=db_session,
        case_id=1,
        vasp_id=entity.id,
        deposit_address="0xcoindcxdeposit0000000000000000000000001",
        suspect_wallet="0xsuspectwallet00000000000000000000000000",
        legal_order_ref="FIR 101/2026",
        notes="Freeze immediately",
        created_by="investigator@demo"
    )
    assert fr.status == "Draft"
    assert fr.request_number.startswith("FR-")

    # Update status through state machine: Draft -> Pending Approval -> Approved -> Sent
    FreezeService.update_freeze_status(
        db=db_session,
        request_id=fr.id,
        new_status="Pending Approval",
        actor_email="investigator@demo",
        actor_role="investigator"
    )
    FreezeService.update_freeze_status(
        db=db_session,
        request_id=fr.id,
        new_status="Approved",
        actor_email="supervisor@demo",
        actor_role="supervisor"
    )
    updated = FreezeService.update_freeze_status(
        db=db_session,
        request_id=fr.id,
        new_status="Sent",
        actor_email="supervisor@demo",
        actor_role="supervisor"
    )
    assert updated.status == "Sent"
    assert updated.approved_by == "supervisor@demo"


# 8. Cryptographic Audit Chain Integrity
def test_audit_chain_integrity(db_session):
    log_audit_action(
        db=db_session,
        user_email="admin@demo",
        action="SYSTEM_BOOT",
        entity_type="SYSTEM",
        entity_id="0",
        details={"status": "initial"}
    )
    log_audit_action(
        db=db_session,
        user_email="investigator@demo",
        action="VIEW_CASE",
        entity_type="CASE",
        entity_id="1",
        details={"case_number": "CASE-2026-0001"}
    )

    check = verify_audit_chain(db_session)
    assert check["valid"] is True
    assert check["count"] == 2
