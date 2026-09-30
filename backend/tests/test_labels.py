import os
import csv
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Label, Entity
from app.labels.base import LabelRecord
from app.labels.ofac import OfacLabelSource
from app.labels.fiu import FiuVaspService
from app.labels.exchange_csv import ExchangeCsvLabelSource
from app.labels.service import LabelService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

# 1. OFAC SDN Golden Test
def test_ofac_sdn_golden_test_234_rows():
    source = OfacLabelSource()
    records = source.fetch()
    assert len(records) == 234, f"Expected exactly 234 OFAC rows, got {len(records)}"

    # Check for no duplicates
    unique_keys = set((r.chain, r.address) for r in records)
    assert len(unique_keys) == 234

    # All records must have category 'sanctioned'
    for r in records:
        assert r.category == "sanctioned"
        assert r.weight_tier == "verified_authority"

    # Specific check for Central Bank of Iran wallet TNiq9AXBp9EjUqhDhrwrfvAA8U3GUQZH81
    cbi_records = [r for r in records if r.address == "TNiq9AXBp9EjUqhDhrwrfvAA8U3GUQZH81"]
    assert len(cbi_records) == 1
    assert "CENTRAL BANK" in cbi_records[0].entity.upper()
    assert cbi_records[0].chain == "tron"

# 2. FIU-IND VASP Loader & Routing Test
def test_fiu_vasp_loader_and_routing(db_session):
    count = FiuVaspService.load_fiu_vasp_list(db_session)
    assert count == 47, f"Expected 47 FIU entities loaded, got {count}"

    # Staleness check (> 180 days since 2024-12-02)
    assert FiuVaspService.is_snapshot_stale() is True
    staleness_msg = FiuVaspService.get_staleness_warning()
    assert staleness_msg is not None
    assert "180 days" in staleness_msg

    # Test alias match: Binance -> Binance International Limited
    match_binance = FiuVaspService.match_vasp(db_session, "Binance")
    assert match_binance["matched"] is True
    assert match_binance["entity"]["name"] == "Binance International Limited"
    assert match_binance["registered_in_india"] is True

    # Test alias match: Unocoin -> Unocoin Technologies Pvt Ltd
    match_unocoin = FiuVaspService.match_vasp(db_session, "Unocoin")
    assert match_unocoin["matched"] is True
    assert match_unocoin["entity"]["name"] == "Unocoin Technologies Pvt Ltd"

    # Bybit is NOT in Dec 2024 snapshot -> status must be 'not in FIU snapshot', NEVER 'unregistered'
    match_bybit = FiuVaspService.match_vasp(db_session, "Bybit")
    assert match_bybit["matched"] is False
    assert match_bybit["status"] == "not in FIU snapshot"

    # CoinDCX is in the snapshot under legal name 'Neblio Technologies Private Limited'
    match_coindcx = FiuVaspService.match_vasp(db_session, "CoinDCX")
    assert match_coindcx["matched"] is True
    assert match_coindcx["entity"]["name"] == "Neblio Technologies Private Limited"

    # Missing nodal contact blocks auto-dispatch
    assert match_binance["notice_routing"] == "contact not on file - analyst must add"
    assert match_binance["auto_dispatch_allowed"] is False

# 3. Exchange CSV Golden Test
def test_exchange_csv_golden_test(db_session):
    source = ExchangeCsvLabelSource()
    records = source.fetch()
    assert len(records) == 30, f"Expected 30 exchange address labels (incl. superseded), got {len(records)}"

    entities = set(r.entity for r in records)
    assert entities == {"Binance", "Bybit", "Unocoin"}

    # Save records into database
    res = LabelService.save_records(db_session, records)
    assert res["added"] == 30

    # 1. Bybit 0x1Db92e... is inactive and must NEVER attribute
    bybit_inactive = LabelService.lookup_attribute(
        db_session,
        chain="ethereum",
        address="0x1Db92e2EeBC8E0c075a02BeA49a2935BcD2dFCF4"
    )
    assert bybit_inactive is None, "Inactive Bybit address must never attribute"

    # 2. Only 1 hot wallet exists (Binance TRX TV6Mu...)
    hot_records = [r for r in records if r.wallet_type == "hot"]
    assert len(hot_records) == 1
    assert hot_records[0].address == "TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi"
    guidance = ExchangeCsvLabelSource.get_recommendation_guidance("hot")
    assert "immediately" in guidance.lower() or "freeze now" in guidance.lower()

    # Cold wallet guidance
    cold_guidance = ExchangeCsvLabelSource.get_recommendation_guidance("cold")
    assert "deposit layer" in cold_guidance

    # Unknown wallet guidance
    unknown_guidance = ExchangeCsvLabelSource.get_recommendation_guidance("unknown")
    assert "confirm wallet type" in unknown_guidance

    # 3. Unocoin BTC validity window:
    # Old address: 1PSh1go1ZBvULhGV4BsekEaVAAESa2fNWp was valid until 2023-06-23
    old_btc = "1PSh1go1ZBvULhGV4BsekEaVAAESa2fNWp"
    # Transfer before 2023-06-23 attributes
    attr_before = LabelService.lookup_attribute(
        db_session,
        chain="bitcoin",
        address=old_btc,
        transfer_time=datetime(2023, 1, 15, tzinfo=timezone.utc)
    )
    assert attr_before is not None
    assert attr_before["entity"] == "Unocoin"

    # Transfer after 2023-06-23 does NOT attribute
    attr_after = LabelService.lookup_attribute(
        db_session,
        chain="bitcoin",
        address=old_btc,
        transfer_time=datetime(2023, 8, 1, tzinfo=timezone.utc)
    )
    assert attr_after is None, "Superseded label outside valid window must not attribute"

    # 4. Unocoin ETH address labeled ONLY on ethereum
    unocoin_eth = "0x6CC38B3F8cbF2b78996801D1B8D5FA441c33270d"
    eth_attr = LabelService.lookup_attribute(db_session, chain="ethereum", address=unocoin_eth)
    assert eth_attr is not None
    assert eth_attr["entity"] == "Unocoin"

    # Must NOT attribute on Polygon or BSC
    polygon_attr = LabelService.lookup_attribute(db_session, chain="polygon", address=unocoin_eth)
    assert polygon_attr is None

# 4. Label Conflict Resolution Test
def test_label_conflict_resolution(db_session):
    # Two conflicting records for the same address:
    # 1. Unverified official source (weight 0.85) claiming Entity A
    # 2. Verified authority source (weight 1.0) claiming Entity B
    addr = "TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2"
    rec1 = LabelRecord(
        chain="tron",
        address=addr,
        entity="Community Exchange",
        category="VASP",
        source="Community Feed",
        weight_tier="community",
        record_status="active"
    )
    rec2 = LabelRecord(
        chain="tron",
        address=addr,
        entity="High Reliability Exchange",
        category="sanctioned",
        source="Law Enforcement",
        weight_tier="verified_authority",
        record_status="active"
    )

    LabelService.save_records(db_session, [rec1, rec2])

    res = LabelService.lookup_attribute(db_session, chain="tron", address=addr)
    assert res is not None
    # Higher reliability tier chosen
    assert res["entity"] == "High Reliability Exchange"
    assert res["category"] == "sanctioned"
    # Conflicting label recorded in evidence
    assert len(res["conflicts"]) == 1
    assert res["conflicts"][0]["entity"] == "Community Exchange"

# 5. Revoked Label Stops Attributing Test
def test_revoked_label_stops_attributing(db_session):
    addr = "TQrY8tryqsYVCYS3MFbtffiPp2ccyn4STm"
    rec = LabelRecord(
        chain="tron",
        address=addr,
        entity="Revoked Entity",
        category="Scam",
        source="Analyst",
        record_status="revoked"
    )
    LabelService.save_records(db_session, [rec])

    res = LabelService.lookup_attribute(db_session, chain="tron", address=addr)
    assert res is None, "Revoked label must never attribute"
