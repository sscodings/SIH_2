import time
import logging
from typing import Dict, Tuple, Optional, List
import httpx
from app.core.config import settings
from app.adapters.base import AdapterError, QuotaExhausted
from app.adapters.http import HttpClientManager

logger = logging.getLogger(__name__)

STABLECOINS = {"USDT", "USDC", "DAI", "BUSD", "FDUSD", "TUSD", "USDD"}

COINGECKO_ID_MAP = {
    "BTC": "bitcoin",
    "BITCOIN": "bitcoin",
    "XBT": "bitcoin",
    "ETH": "ethereum",
    "ETHEREUM": "ethereum",
    "TRX": "tron",
    "TRON": "tron",
    "BNB": "binancecoin",
    "BSC": "binancecoin",
    "MATIC": "matic-network",
    "POL": "matic-network",
    "POLYGON": "matic-network",
    "ARB": "arbitrum",
    "ARBITRUM": "arbitrum",
    "SOL": "solana",
    "SOLANA": "solana"
}

class PricingService:
    _cache: Dict[str, Tuple[float, float]] = {}  # symbol -> (price_usd, expiry_timestamp)
    CACHE_TTL_SECONDS = 300.0  # 5 minutes cache for price stability
    monthly_usage_count = 0

    @classmethod
    def get_cached_price(cls, symbol: str) -> Optional[float]:
        symbol_upper = symbol.upper()
        if symbol_upper in cls._cache:
            price, expiry = cls._cache[symbol_upper]
            if time.time() < expiry:
                return price
        return None

    @classmethod
    def set_cached_price(cls, symbol: str, price: float, ttl: Optional[float] = None):
        symbol_upper = symbol.upper()
        cache_ttl = ttl if ttl is not None else cls.CACHE_TTL_SECONDS
        cls._cache[symbol_upper] = (price, time.time() + cache_ttl)

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()

    @classmethod
    def reset_monthly_usage(cls):
        cls.monthly_usage_count = 0

    @classmethod
    async def get_price_usd(cls, symbol: str, client: Optional[httpx.AsyncClient] = None) -> float:
        symbol_upper = symbol.upper()
        
        # 1. Stablecoin constant 1.0 peg (0 API calls)
        if symbol_upper in STABLECOINS:
            return 1.0

        # 2. Check in-memory cache
        cached = cls.get_cached_price(symbol_upper)
        if cached is not None:
            return cached

        # 3. Check monthly budget cap (binding 9000 requests)
        budget = getattr(settings, "COINGECKO_MONTHLY_BUDGET", 9000)
        if cls.monthly_usage_count >= budget:
            raise QuotaExhausted(f"CoinGecko monthly API budget exhausted ({budget} requests reached)")

        # 4. Resolve CoinGecko coin id
        coin_id = COINGECKO_ID_MAP.get(symbol_upper)
        if not coin_id:
            raise AdapterError(f"Unsupported asset for pricing lookup: {symbol}")

        url = f"{settings.COINGECKO_BASE_URL.rstrip('/')}/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}
        api_key = getattr(settings, "COINGECKO_API_KEY", "")
        if api_key:
            params["x_cg_demo_api_key"] = api_key

        http_mgr = HttpClientManager.get_instance()
        try:
            # Route via centralized http manager for rate limiting & token bucket
            resp = await http_mgr.request(
                provider="coingecko",
                method="GET",
                url=url,
                params=params,
                client=client,
                use_cache=True,
                cache_ttl=cls.CACHE_TTL_SECONDS
            )
            cls.monthly_usage_count += 1
            data = resp.json()

            price = data.get(coin_id, {}).get("usd")
            if price is None or not isinstance(price, (int, float)) or price <= 0:
                raise AdapterError(f"Invalid price response from CoinGecko for {symbol}: {data}")

            price_float = float(price)
            cls.set_cached_price(symbol_upper, price_float)
            return price_float
        except Exception as e:
            if isinstance(e, AdapterError):
                raise
            raise AdapterError(f"Pricing lookup failed for asset '{symbol}': {str(e)}") from e
