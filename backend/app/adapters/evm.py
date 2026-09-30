import asyncio
import logging
import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.adapters.base import ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance, AdapterError
from app.core.config import settings
from app.services.pricing import PricingService

logger = logging.getLogger(__name__)

EVM_CHAIN_IDS = {
    "ethereum": 1,
    "eth": 1,
    "bsc": 56,
    "binance": 56,
    "polygon": 137,
    "matic": 137,
    "arbitrum": 42161,
    "arb": 42161
}

NATIVE_SYMBOLS = {
    "ethereum": "ETH",
    "eth": "ETH",
    "bsc": "BNB",
    "binance": "BNB",
    "polygon": "POL",
    "matic": "POL",
    "arbitrum": "ETH",
    "arb": "ETH"
}

class EvmAdapter(ChainAdapter):
    def __init__(self, chain_id: str = "ethereum"):
        self.chain_id = chain_id.lower()
        self.numeric_chain_id = EVM_CHAIN_IDS.get(self.chain_id, 1)
        self.native_symbol = NATIVE_SYMBOLS.get(self.chain_id, "ETH")
        self.api_key = settings.ETHERSCAN_API_KEY
        self.base_url = "https://api.etherscan.io/v2/api"

    async def _fetch_with_retry(
        self,
        client: httpx.AsyncClient,
        params: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        params = {**params, "chainid": self.numeric_chain_id}
        if self.api_key:
            params["apikey"] = self.api_key

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                res = await client.get(self.base_url, params=params, timeout=settings.ADAPTER_TIMEOUT)
                if res.status_code == 429:
                    await asyncio.sleep(0.3 * (2 ** attempt))
                    continue
                if res.status_code >= 400:
                    raise AdapterError(f"Etherscan V2 HTTP {res.status_code}: {res.text}")
                data = res.json()
                if not isinstance(data, dict):
                    raise AdapterError(f"Malformed response from Etherscan V2: {data}")
                
                # Etherscan error handling
                status = data.get("status")
                msg = str(data.get("message", ""))
                # "No transactions found" returns status="0" and message="No transactions found", which is not an error
                if status == "0" and "no transactions found" not in msg.lower() and "no records found" not in msg.lower():
                    if "rate limit" in str(data.get("result", "")).lower() or "max rate limit" in msg.lower():
                        await asyncio.sleep(0.3 * (2 ** attempt))
                        continue
                    raise AdapterError(f"Etherscan V2 API error: {data.get('result') or msg}")

                return data
            except Exception as e:
                last_error = e
                if isinstance(e, AdapterError) and attempt == max_retries:
                    raise
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (2 ** (attempt - 1)))
                else:
                    if isinstance(e, AdapterError):
                        raise
                    raise AdapterError(f"Etherscan V2 request failed after {max_retries} attempts: {str(e)}") from e
        raise AdapterError(f"Etherscan V2 request failed: {last_error}")

    async def get_address_summary(self, address: str) -> AddressSummary:
        async with httpx.AsyncClient() as client:
            native_price = await PricingService.get_price_usd(self.native_symbol, client)
            
            # Fetch native balance
            params = {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest"
            }
            data = await self._fetch_with_retry(client, params)
            raw_bal = float(data.get("result", 0) or 0)
            bal_native = raw_bal / 1e18
            bal_usd = bal_native * native_price

            return AddressSummary(
                address=address,
                chain=self.chain_id,
                total_received=0.0,
                total_received_usd=0.0,
                total_sent=0.0,
                total_sent_usd=0.0,
                balance_usd=round(bal_usd, 2),
                tx_count=1
            )

    async def get_transfers(
        self,
        address: str,
        direction: str = "both",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Transfer]:
        results: List[Transfer] = []
        is_truncated = False
        addr_lower = address.lower()

        async with httpx.AsyncClient() as client:
            native_price = await PricingService.get_price_usd(self.native_symbol, client)

            # Actions to query: tokentx (ERC20), txlist (native), txlistinternal (internal)
            actions = [
                ("tokentx", "ERC20"),
                ("txlist", "NATIVE"),
                ("txlistinternal", "INTERNAL")
            ]

            for action_name, action_type in actions:
                for page in range(1, settings.ADAPTER_MAX_PAGES + 1):
                    params = {
                        "module": "account",
                        "action": action_name,
                        "address": address,
                        "startblock": 0,
                        "endblock": 99999999,
                        "page": page,
                        "offset": min(limit, 100),
                        "sort": "desc"
                    }
                    data = await self._fetch_with_retry(client, params)
                    items = data.get("result", [])
                    if not isinstance(items, list) or len(items) == 0:
                        break

                    for it in items:
                        from_addr = it.get("from", "")
                        to_addr = it.get("to", "")
                        from_lower = from_addr.lower()
                        to_lower = to_addr.lower()

                        # Direction filter
                        if direction == "out" and from_lower != addr_lower:
                            continue
                        if direction == "in" and to_lower != addr_lower:
                            continue

                        # Timestamp filter
                        ts_val = int(it.get("timeStamp", 0) or 0)
                        ts = datetime.fromtimestamp(ts_val, tz=timezone.utc)
                        if since and ts < since.replace(tzinfo=timezone.utc if since.tzinfo is None else since.tzinfo):
                            continue
                        if until and ts > until.replace(tzinfo=timezone.utc if until.tzinfo is None else until.tzinfo):
                            continue

                        if action_type == "ERC20":
                            symbol = it.get("tokenSymbol", "USDT").upper()
                            decimals = int(it.get("tokenDecimal", 18) or 18)
                            raw_val = float(it.get("value", 0) or 0)
                            amt = raw_val / (10 ** decimals)
                            token_price = 1.0 if symbol in ["USDT", "USDC", "DAI"] else await PricingService.get_price_usd(symbol, client)
                            amt_usd = amt * token_price
                            is_contract = True
                        else:
                            symbol = self.native_symbol
                            raw_val = float(it.get("value", 0) or 0)
                            amt = raw_val / 1e18
                            amt_usd = amt * native_price
                            is_contract = action_type == "INTERNAL"

                        results.append(Transfer(
                            chain=self.chain_id,
                            tx_hash=it.get("hash", ""),
                            block_number=int(it.get("blockNumber", 0) or 0),
                            timestamp=ts,
                            from_address=from_addr,
                            to_address=to_addr,
                            token=symbol,
                            amount=amt,
                            amount_usd=round(amt_usd, 2),
                            is_contract_call=is_contract,
                            log_index=int(it.get("logIndex", 0) or 0)
                        ))

                    if len(items) < min(limit, 100):
                        break
                    if page == settings.ADAPTER_MAX_PAGES:
                        is_truncated = True

        if is_truncated and results:
            results[-1].truncated = True

        return results

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        async with httpx.AsyncClient() as client:
            params = {
                "module": "proxy",
                "action": "eth_getTransactionByHash",
                "txhash": tx_hash
            }
            data = await self._fetch_with_retry(client, params)
            it = data.get("result")
            if not it or not isinstance(it, dict):
                return None
            
            raw_val = int(it.get("value", "0x0"), 16) if isinstance(it.get("value"), str) else 0
            val_eth = raw_val / 1e18
            
            return Transaction(
                chain=self.chain_id,
                tx_hash=tx_hash,
                block_number=int(it.get("blockNumber", "0x0"), 16) if isinstance(it.get("blockNumber"), str) else 0,
                timestamp=datetime.now(timezone.utc),
                from_address=it.get("from", ""),
                to_address=it.get("to", ""),
                value=val_eth,
                status="success"
            )

    async def get_balance(self, address: str) -> List[TokenBalance]:
        summary = await self.get_address_summary(address)
        return [TokenBalance(token=self.native_symbol, symbol=self.native_symbol, balance=0.0, balance_usd=summary.balance_usd)]

    def normalize(self, raw: dict) -> Transfer:
        return Transfer(**raw)
