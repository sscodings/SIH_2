import pytest
import httpx
import asyncio
from app.adapters.http import HttpClientManager, CircuitBreaker, InMemoryTokenBucket
from app.adapters.base import RateLimited, ChainUnsupported, QuotaExhausted, AdapterError
from app.adapters.evm import EvmAdapter
from app.services.pricing import PricingService

@pytest.mark.asyncio
async def test_http_retry_after_and_backoff():
    http_mgr = HttpClientManager.get_instance()
    call_count = 0

    def mock_handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429, headers={"Retry-After": "0.05"}, text="Too Many Requests")
        return httpx.Response(200, json={"status": "1", "message": "OK", "result": []})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        resp = await http_mgr.request(
            provider="etherscan",
            method="GET",
            url="https://api.etherscan.io/v2/api",
            params={"module": "test"},
            client=client,
            use_cache=False
        )
        assert resp.status_code == 200
        assert call_count == 2

@pytest.mark.asyncio
async def test_circuit_breaker_trip_and_recover():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True

    cb.record_failure()
    cb.record_failure()
    assert cb.state == "CLOSED"

    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False

    # Wait for recovery timeout
    await asyncio.sleep(0.12)
    assert cb.can_execute() is True
    assert cb.state == "HALF_OPEN"

    # Successful probe resets breaker
    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.failure_count == 0

@pytest.mark.asyncio
async def test_cache_avoids_second_call():
    http_mgr = HttpClientManager.get_instance()
    http_mgr.clear_cache()
    call_count = 0

    def mock_handler(request: httpx.Request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json={"status": "1", "message": "OK", "result": [{"id": 123}]})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        url = "https://api.etherscan.io/v2/api/test_cache"
        resp1 = await http_mgr.request(
            provider="etherscan",
            method="GET",
            url=url,
            params={"a": "1"},
            client=client,
            use_cache=True,
            cache_ttl=60.0
        )
        assert resp1.json()["result"][0]["id"] == 123
        assert call_count == 1

        # Second request hits cache
        resp2 = await http_mgr.request(
            provider="etherscan",
            method="GET",
            url=url,
            params={"a": "1"},
            client=client,
            use_cache=True,
            cache_ttl=60.0
        )
        assert resp2.json()["result"][0]["id"] == 123
        assert call_count == 1  # No second HTTP call

@pytest.mark.asyncio
async def test_chain_unsupported_for_unmapped_chain():
    # BSC is unmapped ("none") until Blockscout adapter is verified
    adapter = EvmAdapter(chain_id="bsc")
    with pytest.raises(ChainUnsupported):
        await adapter.get_transfers("0xd746108C820a9432f370DfFeEaF1B82CA7DD131D")

@pytest.mark.asyncio
async def test_etherscan_error_string_mappings():
    http_mgr = HttpClientManager.get_instance()

    # 1. "Max rate limit reached" -> RateLimited
    def mock_rate_limit(req):
        return httpx.Response(200, json={"status": "0", "message": "NOTOK", "result": "Max rate limit reached"})
    transport1 = httpx.MockTransport(mock_rate_limit)
    async with httpx.AsyncClient(transport=transport1) as c1:
        with pytest.raises(RateLimited):
            await http_mgr.request("etherscan", "GET", "https://api.etherscan.io/v2/api", client=c1, use_cache=False)

    # 2. "Free API access is not supported for this chain" -> ChainUnsupported
    def mock_chain_unsupported(req):
        return httpx.Response(200, json={"status": "0", "message": "Free API access is not supported for this chain", "result": ""})
    transport2 = httpx.MockTransport(mock_chain_unsupported)
    async with httpx.AsyncClient(transport=transport2) as c2:
        with pytest.raises(ChainUnsupported):
            await http_mgr.request("etherscan", "GET", "https://api.etherscan.io/v2/api", client=c2, use_cache=False)

    # 3. "Community Free API limit reached" -> QuotaExhausted
    def mock_quota_exhausted(req):
        return httpx.Response(200, json={"status": "0", "message": "NOTOK", "result": "Community Free API limit reached"})
    transport3 = httpx.MockTransport(mock_quota_exhausted)
    async with httpx.AsyncClient(transport=transport3) as c3:
        with pytest.raises(QuotaExhausted):
            await http_mgr.request("etherscan", "GET", "https://api.etherscan.io/v2/api", client=c3, use_cache=False)

@pytest.mark.asyncio
async def test_coingecko_monthly_budget_exhaustion(monkeypatch):
    PricingService.clear_cache()
    PricingService.reset_monthly_usage()
    # Mock budget to 2 requests
    monkeypatch.setattr("app.core.config.settings.COINGECKO_MONTHLY_BUDGET", 2)

    def mock_handler(req):
        return httpx.Response(200, json={"ethereum": {"usd": 3000.0}})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        # Call 1: succeeds
        p1 = await PricingService.get_price_usd("ETH", client=client)
        assert p1 == 3000.0

        # Clear cache to force second API request
        PricingService.clear_cache()
        p2 = await PricingService.get_price_usd("ETH", client=client)
        assert p2 == 3000.0

        # Clear cache: call 3 exceeds monthly budget of 2
        PricingService.clear_cache()
        with pytest.raises(QuotaExhausted):
            await PricingService.get_price_usd("ETH", client=client)

    PricingService.reset_monthly_usage()

@pytest.mark.asyncio
async def test_pagination_and_truncation_cap():
    adapter = EvmAdapter(chain_id="ethereum")

    def mock_paginated(req):
        url_str = str(req.url)
        # Return 100 items per page
        items = [
            {
                "hash": f"0x{i:064x}",
                "from": "0x1111111111111111111111111111111111111111",
                "to": "0x2222222222222222222222222222222222222222",
                "value": "1000000000000000000",
                "timeStamp": "1700000000",
                "tokenSymbol": "USDT",
                "tokenDecimal": "6"
            }
            for i in range(100)
        ]
        return httpx.Response(200, json={"status": "1", "message": "OK", "result": items})

    transport = httpx.MockTransport(mock_paginated)
    async with httpx.AsyncClient(transport=transport) as client:
        # With default settings (max 5 pages = 500 items max), loop collects items and marks truncated if capped
        transfers = await adapter.get_transfers("0x2222222222222222222222222222222222222222", limit=100, client=client)
        assert len(transfers) >= 100
        assert transfers[0].truncated is True
