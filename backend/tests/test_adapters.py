import pytest
import httpx
from datetime import datetime, timezone, timedelta
from app.adapters.base import AdapterError, Transfer
from app.adapters.tron import TronAdapter
from app.adapters.evm import EvmAdapter
from app.adapters.bitcoin import BitcoinAdapter
from app.adapters.factory import get_chain_adapter, register_adapter, clear_custom_adapters
from app.services.pricing import PricingService
from app.core.config import settings

@pytest.mark.asyncio
async def test_pricing_service_stablecoins():
    PricingService.clear_cache()
    usdt = await PricingService.get_price_usd("USDT")
    usdc = await PricingService.get_price_usd("USDC")
    dai = await PricingService.get_price_usd("DAI")
    assert usdt == 1.0
    assert usdc == 1.0
    assert dai == 1.0

@pytest.mark.asyncio
async def test_pricing_service_coingecko_and_cache(monkeypatch):
    PricingService.clear_cache()
    
    call_count = 0
    def mock_handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        if "simple/price" in str(request.url):
            return httpx.Response(200, json={"ethereum": {"usd": 3250.75}})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        # First call fetches from API
        price1 = await PricingService.get_price_usd("ETH", client=client)
        assert price1 == 3250.75
        assert call_count == 1

        # Second call hits cache (no new API call)
        price2 = await PricingService.get_price_usd("ETH", client=client)
        assert price2 == 3250.75
        assert call_count == 1

@pytest.mark.asyncio
async def test_pricing_service_failure_raises_adapter_error():
    PricingService.clear_cache()
    def mock_fail(request: httpx.Request):
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(mock_fail)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(AdapterError):
            await PricingService.get_price_usd("BTC", client=client)

@pytest.mark.asyncio
async def test_tron_adapter_retry_and_adapter_error(monkeypatch):
    monkeypatch.setattr(settings, "CHAINNETRA_MODE", "LIVE")
    
    def mock_failing(request: httpx.Request):
        return httpx.Response(503, text="Service Unavailable")

    adapter = TronAdapter()
    
    # In live mode, a failing API must raise AdapterError and NOT return demo fallback
    transport = httpx.MockTransport(mock_failing)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(AdapterError):
            await adapter._fetch_with_retry(client, "https://api.trongrid.io/v1/accounts/TDemo123")

@pytest.mark.asyncio
async def test_evm_adapter_direction_and_since_filtering(monkeypatch):
    monkeypatch.setattr(settings, "CHAINNETRA_MODE", "LIVE")
    PricingService.clear_cache()
    PricingService.set_cached_price("ETH", 3000.0)

    target_addr = "0x71C84949C6ff62E90D88F2c1598f6A7B8E9f6A40"
    now_ts = int(datetime.now(timezone.utc).timestamp())

    sample_tokentx = [
        # Outflow 1 (Matches direction 'out' and timestamp)
        {
            "hash": "0xaaa1",
            "blockNumber": "1000",
            "timeStamp": str(now_ts - 100),
            "from": target_addr,
            "to": "0x9999999999999999999999999999999999999999",
            "value": "100000000",  # 100 USDT (6 decimals)
            "tokenSymbol": "USDT",
            "tokenDecimal": "6",
            "logIndex": "0"
        },
        # Inflow 1 (Should be excluded when direction='out')
        {
            "hash": "0xaaa2",
            "blockNumber": "1001",
            "timeStamp": str(now_ts - 50),
            "from": "0x1111111111111111111111111111111111111111",
            "to": target_addr,
            "value": "500000000",
            "tokenSymbol": "USDT",
            "tokenDecimal": "6",
            "logIndex": "0"
        },
        # Outflow 2 (Old timestamp, should be excluded by since filter)
        {
            "hash": "0xaaa3",
            "blockNumber": "500",
            "timeStamp": str(now_ts - 50000),
            "from": target_addr,
            "to": "0x8888888888888888888888888888888888888888",
            "value": "200000000",
            "tokenSymbol": "USDT",
            "tokenDecimal": "6",
            "logIndex": "0"
        }
    ]

    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if "action=tokentx" in url:
            return httpx.Response(200, json={"status": "1", "message": "OK", "result": sample_tokentx})
        return httpx.Response(200, json={"status": "1", "message": "OK", "result": []})

    adapter = EvmAdapter("ethereum")
    
    # Test with direction='out' and since filter
    since_time = datetime.now(timezone.utc) - timedelta(hours=2)
    
    orig_client = httpx.AsyncClient
    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: orig_client(transport=transport))

    transfers = await adapter.get_transfers(target_addr, direction="out", since=since_time)
    
    assert len(transfers) == 1
    assert transfers[0].tx_hash == "0xaaa1"
    assert transfers[0].amount == 100.0
    assert transfers[0].amount_usd == 100.0
    assert transfers[0].token == "USDT"

@pytest.mark.asyncio
async def test_bitcoin_adapter_parsing_and_multi_input(monkeypatch):
    monkeypatch.setattr(settings, "CHAINNETRA_MODE", "LIVE")
    PricingService.clear_cache()
    PricingService.set_cached_price("BTC", 60000.0)

    target_addr = "bc1qsuspectbitcoinwallet0000000000"
    
    sample_esplora_txs = [
        {
            "txid": "btc_tx_123",
            "status": {"confirmed": True, "block_height": 800000, "block_time": int(datetime.now(timezone.utc).timestamp())},
            "vin": [
                {"prevout": {"scriptpubkey_address": target_addr, "value": 50000000}},
                {"prevout": {"scriptpubkey_address": "bc1qcoinputmule00000000000", "value": 30000000}}
            ],
            "vout": [
                {"scriptpubkey_address": "bc1qexchangedeposit00000000", "value": 75000000}
            ]
        }
    ]

    def mock_handler(request: httpx.Request):
        return httpx.Response(200, json=sample_esplora_txs)

    adapter = BitcoinAdapter()
    orig_client = httpx.AsyncClient
    transport = httpx.MockTransport(mock_handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: orig_client(transport=transport))

    transfers = await adapter.get_transfers(target_addr, direction="out")
    assert len(transfers) == 1
    t = transfers[0]
    assert t.tx_hash == "btc_tx_123"
    assert t.token == "BTC"
    assert t.amount == 0.75
    assert t.amount_usd == 0.75 * 60000.0
    assert t.multi_input is True
