import time
import logging
import httpx
from typing import Dict, Tuple, Optional
from app.core.config import settings
from app.adapters.base import AdapterError

logger = logging.getLogger(__name__)

STABLECOINS = {"USDT", "USDC", "DAI", "BUSD", "FDUSD", "TUSD", "USDD"}

COINGECKO_ID_MAP = {
    "BTC": "bitcoin",
    "BITCOIN": "bitcoin",
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
    CACHE_TTL_SECONDS = 60.0

    @classmethod
    def get_cached_price(cls, symbol: str) -> Optional[float]:
        symbol_upper = symbol.upper()
        if symbol_upper in cls._cache:
            price, expiry = cls._cache[symbol_upper]
            if time.time() < expiry:
                return price
        return None

    @classmethod
    def set_cached_price(cls, symbol: str, price: float):
        symbol_upper = symbol.upper()
        cls._cache[symbol_upper] = (price, time.time() + cls.CACHE_TTL_SECONDS)

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()

    @classmethod
    async def get_price_usd(cls, symbol: str, client: Optional[httpx.AsyncClient] = None) -> float:
        symbol_upper = symbol.upper()
        
        # 1. Stablecoin constant peg
        if symbol_upper in STABLECOINS:
            return 1.0

        # 2. Check in-memory cache
        cached = cls.get_cached_price(symbol_upper)
        if cached is not None:
            return cached

        # 3. Resolve CoinGecko coin id
        coin_id = COINGECKO_ID_MAP.get(symbol_upper)
        if not coin_id:
            raise AdapterError(f"Unsupported asset for pricing lookup: {symbol}")

        url = f"{settings.COINGECKO_BASE_URL.rstrip('/')}/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}

        try:
            if client:
                res = await client.get(url, params=params, timeout=settings.ADAPTER_TIMEOUT)
                res.raise_for_status()
                data = res.json()
            else:
                async with httpx.AsyncClient(timeout=settings.ADAPTER_TIMEOUT) as local_client:
                    res = await local_client.get(url, params=params)
                    res.raise_for_status()
                    data = res.json()

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
