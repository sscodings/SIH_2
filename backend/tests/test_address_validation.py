import csv
import os
import pytest
from app.core.addresses import validate_address, validate_tx_hash, to_checksum_address, normalize

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def test_bare_evm_candidate_chains():
    addr = "0xaba250b6f3334fa1e5e6b37aefbbe56507f84797"
    res = validate_address(addr)
    assert res["valid"] is True
    assert res["family"] == "evm"
    assert res["candidate_chains"] == ["ethereum", "polygon", "arbitrum"]
    assert res["normalized"] == addr.lower()

def test_eip55_checksum_validation():
    # Valid EIP-55
    valid_mixed = "0xABa250B6f3334Fa1E5E6B37aEFbBE56507F84797"
    res1 = validate_address(valid_mixed, chain_hint="ethereum")
    assert res1["valid"] is True
    assert res1["family"] == "evm"

    # All-lowercase is valid
    res_lower = validate_address(valid_mixed.lower(), chain_hint="ethereum")
    assert res_lower["valid"] is True

    # Bad mixed-case casing (flip case of one character)
    # The first hex char 'A' -> 'a'
    bad_mixed = "0xaba250B6f3334Fa1E5E6B37aEFbBE56507F84797"
    res_bad = validate_address(bad_mixed, chain_hint="ethereum")
    assert res_bad["valid"] is False
    assert "EIP-55" in res_bad["error"]

def test_tron_checksum_validation():
    # Valid Tron address
    valid_tron = "TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY2"
    res1 = validate_address(valid_tron, chain_hint="tron")
    assert res1["valid"] is True
    assert res1["family"] == "tron"

    # SYN-0011 has bad checksum (last char changed from 2 to 3)
    syn_0011 = "TVssLZco7KSwkQ3NwsuwQPRxUVjXfVwYY3"
    res2 = validate_address(syn_0011, chain_hint="tron")
    assert res2["valid"] is False
    assert "checksum" in res2["error"].lower()

def test_bitcoin_address_validation():
    # Legacy P2PKH (1...)
    res1 = validate_address("1AycQxUK1k39gro3gDyRQ3vaHeDgjyD9o3", chain_hint="bitcoin")
    assert res1["valid"] is True
    assert res1["family"] == "bitcoin"

    # Segwit Bech32 (bc1...)
    res2 = validate_address("bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h", chain_hint="bitcoin")
    assert res2["valid"] is True
    assert res2["family"] == "bitcoin"

    # Bad Bitcoin checksum
    res_bad = validate_address("1AycQxUK1k39gro3gDyRQ3vaHeDgjyD9o4", chain_hint="bitcoin")
    assert res_bad["valid"] is False

def test_tx_hash_validation():
    # Tron / BTC: 64 hex characters, NO 0x
    tron_tx = "c011d7fa1316cb0a05456d60552038873eb5ca79797b1fce9d828ee537b0adca"
    assert validate_tx_hash(tron_tx, chain="tron") is True
    assert validate_tx_hash("0x" + tron_tx, chain="tron") is False
    assert validate_tx_hash(tron_tx[:63], chain="tron") is False

    btc_tx = "2d9f15b5c4d1818c9802d67991a89149c82409c79f13fd3cfc01757cc1e2393e"
    assert validate_tx_hash(btc_tx, chain="bitcoin") is True
    assert validate_tx_hash("0x" + btc_tx, chain="bitcoin") is False

    # EVM: 0x + 64 hex characters (66 chars total)
    evm_tx = "0xb8f67880da6c033674c25d1469ab9434a209a39224ceb600766decdb8ae76329"
    assert validate_tx_hash(evm_tx, chain="ethereum") is True
    assert validate_tx_hash(evm_tx[2:], chain="ethereum") is False
    assert validate_tx_hash(evm_tx[:65], chain="ethereum") is False

def test_ofac_sample_all_addresses_valid():
    csv_path = os.path.join(FIXTURES_DIR, "ofac_sample.csv")
    assert os.path.exists(csv_path)

    tron_count = 0
    usdt_count = 0
    btc_count = 0
    evm_count = 0
    other_count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            addr = row["address"].strip()
            ccy = row["currency"].strip()

            if ccy == "USDT":
                usdt_count += 1

            res = validate_address(addr)
            if res["family"] == "tron":
                tron_count += 1
                assert res["valid"] is True
            elif res["family"] == "bitcoin":
                btc_count += 1
                assert res["valid"] is True
            elif res["family"] == "evm":
                evm_count += 1
                assert res["valid"] is True
            else:
                other_count += 1

    # In ofac_sample.csv:
    # 198 Tron addresses (incl. 59 USDT-tagged which are Tron format)
    # 7 legacy BTC + 2 segwit BTC = 9 total BTC
    # 22 EVM addresses (21 EIP-55 + 1 lowercase)
    assert tron_count == 198
    assert usdt_count == 59
    assert btc_count == 9
    assert evm_count == 22

def test_exchange_addresses_all_valid():
    csv_path = os.path.join(FIXTURES_DIR, "exchange_addresses.csv")
    assert os.path.exists(csv_path)

    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            count += 1
            addr = row["address"].strip()
            chain = row["chain"].strip()
            res = validate_address(addr, chain_hint=chain)
            assert res["valid"] is True, f"Exchange address failed validation: {addr} on {chain}"
    assert count == 30
