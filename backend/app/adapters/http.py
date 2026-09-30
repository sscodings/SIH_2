import time
import asyncio
import random
import logging
from typing import Dict, Any, Optional, Tuple
import httpx
from app.core.config import settings
from app.adapters.base import AdapterError, RateLimited, ChainUnsupported, QuotaExhausted

logger = logging.getLogger("chainnetra.adapters.http")

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 15.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_state_change = time.time()

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()
            logger.warning(f"Circuit breaker tripped to OPEN (failures: {self.failure_count})")

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.last_state_change = now
                logger.info("Circuit breaker entering HALF_OPEN probe state")
                return True
            return False
        if self.state == "HALF_OPEN":
            # Allow single probe request
            return True
        return False

class InMemoryTokenBucket:
    def __init__(self, rate: float, capacity: Optional[float] = None):
        self.rate = rate  # tokens per second
        self.capacity = capacity if capacity is not None else max(rate, 1.0)
        self.tokens = self.capacity
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> float:
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            
            # Need to wait
            needed = tokens - self.tokens
            wait_time = needed / self.rate
            await asyncio.sleep(wait_time)
            self.last_update = time.time()
            self.tokens = 0.0
            return wait_time

class HttpClientManager:
    """
    Centralized HTTP Client manager for blockchain & pricing providers.
    Provides rate limiting, exponential backoff, circuit breaking, response caching, and metrics.
    """
    _instance = None

    def __init__(self):
        self.limiters: Dict[str, InMemoryTokenBucket] = {
            "etherscan": InMemoryTokenBucket(rate=getattr(settings, "ETHERSCAN_RPS", 3.0)),
            "trongrid": InMemoryTokenBucket(rate=getattr(settings, "TRONGRID_QPS", 10.0)),
            "coingecko": InMemoryTokenBucket(rate=getattr(settings, "COINGECKO_RPM", 60.0) / 60.0),
        }
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            "etherscan": CircuitBreaker(),
            "trongrid": CircuitBreaker(),
            "coingecko": CircuitBreaker(),
            "blockscout": CircuitBreaker(),
        }
        self.metrics: Dict[str, Dict[str, Any]] = {
            "etherscan": {"calls": 0, "errors": 0, "total_latency_ms": 0.0, "throttle_wait_ms": 0.0, "status": "ok"},
            "trongrid": {"calls": 0, "errors": 0, "total_latency_ms": 0.0, "throttle_wait_ms": 0.0, "status": "ok"},
            "coingecko": {"calls": 0, "errors": 0, "total_latency_ms": 0.0, "throttle_wait_ms": 0.0, "status": "ok"},
            "blockscout": {"calls": 0, "errors": 0, "total_latency_ms": 0.0, "throttle_wait_ms": 0.0, "status": "ok"},
        }
        # In-memory cache fallback: key -> (timestamp, data, ttl)
        self.cache: Dict[str, Tuple[float, Any, float]] = {}
        self.cache_stats = {"hits": 0, "misses": 0}

        # Provider Map: chain -> provider
        # Decisions.md & Section 6: BSC defaults to "none" until verified Blockscout adapter exists
        self.provider_map = {
            "ethereum": "etherscan_v2",
            "polygon": "etherscan_v2",
            "arbitrum": "etherscan_v2",
            "bsc": "none",
            "tron": "trongrid",
            "bitcoin": "blockstream",
        }

        # Etherscan V2 chain ID map
        self.etherscan_chain_ids = {
            "ethereum": 1,
            "polygon": 137,
            "arbitrum": 42161,
        }

    @classmethod
    def get_instance(cls) -> "HttpClientManager":
        if cls._instance is None:
            cls._instance = HttpClientManager()
        return cls._instance

    def get_provider_for_chain(self, chain: str) -> str:
        c = (chain or "").lower().strip()
        provider = self.provider_map.get(c, "none")
        if provider == "none":
            raise ChainUnsupported(f"Chain '{chain}' is unsupported by available providers")
        return provider

    def _cache_get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            ts, data, ttl = self.cache[key]
            if time.time() - ts < ttl:
                self.cache_stats["hits"] += 1
                return data
            else:
                del self.cache[key]
        self.cache_stats["misses"] += 1
        return None

    def _cache_set(self, key: str, data: Any, ttl: float = 60.0):
        self.cache[key] = (time.time(), data, ttl)

    def clear_cache(self):
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0}

    async def request(
        self,
        provider: str,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        client: Optional[httpx.AsyncClient] = None,
        use_cache: bool = True,
        cache_ttl: float = 60.0,
        max_retries: int = 3
    ) -> httpx.Response:
        prov = provider.lower()
        cb = self.circuit_breakers.get(prov)
        if cb and not cb.can_execute():
            raise AdapterError(f"Circuit breaker for provider '{provider}' is OPEN. Fast failing request.")

        # Check Cache for GET requests
        cache_key = ""
        if use_cache and method.upper() == "GET":
            param_str = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
            cache_key = f"{prov}:{url}:{param_str}"
            cached_resp = self._cache_get(cache_key)
            if cached_resp is not None:
                # Return synthetic httpx response for cached JSON/content
                return httpx.Response(200, json=cached_resp)

        # Rate Limiting
        limiter = self.limiters.get(prov)
        if limiter:
            waited = await limiter.acquire()
            if prov in self.metrics:
                self.metrics[prov]["throttle_wait_ms"] += waited * 1000.0

        retries = 0
        backoff = 0.5

        while True:
            t0 = time.time()
            try:
                if client is not None:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        headers=headers,
                        json=json_data,
                        timeout=settings.ADAPTER_TIMEOUT
                    )
                else:
                    async with httpx.AsyncClient(timeout=settings.ADAPTER_TIMEOUT) as default_client:
                        response = await default_client.request(
                            method=method,
                            url=url,
                            params=params,
                            headers=headers,
                            json=json_data
                        )
                
                latency_ms = (time.time() - t0) * 1000.0
                if prov in self.metrics:
                    self.metrics[prov]["calls"] += 1
                    self.metrics[prov]["total_latency_ms"] += latency_ms

                # Check for rate limit status (429)
                if response.status_code == 429:
                    retry_after_hdr = response.headers.get("Retry-After")
                    delay = float(retry_after_hdr) if retry_after_hdr and retry_after_hdr.isdigit() else backoff
                    retries += 1
                    if retries > max_retries:
                        if cb: cb.record_failure()
                        if prov in self.metrics: self.metrics[prov]["errors"] += 1
                        raise RateLimited(f"Provider '{provider}' rate limit exceeded after retries (429)")
                    
                    logger.warning(f"Rate limited by {provider} (429). Retrying in {delay}s...")
                    await asyncio.sleep(delay + random.uniform(0.05, 0.2))
                    backoff *= 2
                    continue

                # Check for 5xx server errors
                if 500 <= response.status_code < 600:
                    retries += 1
                    if retries > max_retries:
                        if cb: cb.record_failure()
                        if prov in self.metrics: self.metrics[prov]["errors"] += 1
                        raise AdapterError(f"Provider '{provider}' returned server error {response.status_code}")
                    
                    await asyncio.sleep(backoff + random.uniform(0.05, 0.2))
                    backoff *= 2
                    continue

                # Inspect payload for common Etherscan / provider error messages
                text = response.text
                if "Max rate limit reached" in text:
                    if cb: cb.record_failure()
                    if prov in self.metrics: self.metrics[prov]["errors"] += 1
                    raise RateLimited(f"Provider '{provider}' reported: Max rate limit reached")
                
                if "Free API access is not supported for this chain" in text:
                    if prov in self.metrics: self.metrics[prov]["errors"] += 1
                    raise ChainUnsupported(f"Provider '{provider}' reported: Free API access is not supported for this chain")

                if "Community Free API limit reached" in text:
                    if prov in self.metrics: self.metrics[prov]["errors"] += 1
                    raise QuotaExhausted(f"Provider '{provider}' reported: Community Free API limit reached")

                # Successful call
                if cb:
                    cb.record_success()

                # Cache successful GET response body if requested
                if use_cache and cache_key and response.is_success:
                    try:
                        self._cache_set(cache_key, response.json(), ttl=cache_ttl)
                    except Exception:
                        pass

                return response

            except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                retries += 1
                if retries > max_retries:
                    if cb: cb.record_failure()
                    if prov in self.metrics: self.metrics[prov]["errors"] += 1
                    raise AdapterError(f"Network error contacting provider '{provider}': {net_err}") from net_err
                await asyncio.sleep(backoff + random.uniform(0.05, 0.2))
                backoff *= 2

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "providers": self.metrics,
            "cache": self.cache_stats,
            "circuit_breakers": {
                name: cb.state for name, cb in self.circuit_breakers.items()
            }
        }
