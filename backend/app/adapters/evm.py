import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx
from app.adapters.base import (
    ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance,
    AdapterError, RateLimited, ChainUnsupported, QuotaExhausted
)
from app.core.config import settings
from app.adapters.http import HttpClientManager
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
        self.http_mgr = HttpClientManager.get_instance()

    def _check_provider_support(self):
        # Section 6: Free Etherscan does not cover BSC; map bsc to "none" -> raises ChainUnsupported
        provider = self.http_mgr.get_provider_for_chain(self.chain_id)
        if provider == "none":
            raise ChainUnsupported(f"Chain '{self.chain_id}' is unsupported by available providers")
        return provider

    async def _fetch_with_retry(
        self,
        client: Optional[httpx.AsyncClient],
        params: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        self._check_provider_support()
        
        request_params = {**params, "chainid": self.numeric_chain_id}
        if self.api_key:
            request_params["apikey"] = self.api_key

        resp = await self.http_mgr.request(
            provider="etherscan",
            method="GET",
            url=self.base_url,
            params=request_params,
            client=client,
            max_retries=max_retries
        )

        try:
            data = resp.json()
        except Exception as e:
            raise AdapterError(f"Malformed JSON response from Etherscan V2: {resp.text}") from e

        if not isinstance(data, dict):
            raise AdapterError(f"Malformed response structure from Etherscan V2: {data}")

        status = str(data.get("status", ""))
        msg = str(data.get("message", ""))
        result_str = str(data.get("result", ""))

        # Check explicit error messages
        if "max rate limit reached" in result_str.lower() or "max rate limit" in msg.lower():
            raise RateLimited(f"Etherscan V2 error: {result_str or msg}")
        if "free api access is not supported for this chain" in result_str.lower() or "free api access is not supported" in msg.lower():
            raise ChainUnsupported(f"Etherscan V2 error: {result_str or msg}")
        if "community free api limit reached" in result_str.lower() or "community free api limit reached" in msg.lower():
            raise QuotaExhausted(f"Etherscan V2 error: {result_str or msg}")

        # "No transactions found" / "No records found" returns status="0", which is not an error
        if status == "0" and "no transactions found" not in msg.lower() and "no records found" not in msg.lower():
            raise AdapterError(f"Etherscan V2 API error: {result_str or msg}")

        return data

    async def get_address_summary(self, address: str, client: Optional[httpx.AsyncClient] = None) -> AddressSummary:
        self._check_provider_support()
        native_price = await PricingService.get_price_usd(self.native_symbol, client)

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

        # Fetch tx count
        tx_count_params = {
            "module": "proxy",
            "action": "eth_getTransactionCount",
            "address": address,
            "tag": "latest"
        }
        tx_count_data = await self._fetch_with_retry(client, tx_count_params)
        tx_count_hex = tx_count_data.get("result", "0x0")
        tx_count = int(tx_count_hex, 16) if isinstance(tx_count_hex, str) and tx_count_hex.startswith("0x") else 0

        # Sample recent transfers to calculate sent/received totals
        transfers = await self.get_transfers(address, limit=50, client=client)
        total_rec = sum(t.amount_usd for t in transfers if t.to_address.lower() == address.lower())
        total_sent = sum(t.amount_usd for t in transfers if t.from_address.lower() == address.lower())
        is_trunc = any(t.truncated for t in transfers)

        first_seen = min([t.timestamp for t in transfers], default=None)
        last_seen = max([t.timestamp for t in transfers], default=None)

        return AddressSummary(
            address=address,
            chain=self.chain_id,
            total_received=total_rec / native_price if native_price > 0 else 0.0,
            total_received_usd=total_rec,
            total_sent=total_sent / native_price if native_price > 0 else 0.0,
            total_sent_usd=total_sent,
            balance_usd=bal_usd,
            tx_count=tx_count,
            first_seen=first_seen,
            last_seen=last_seen,
            truncated=is_trunc
        )

    async def get_transfers(
        self,
        address: str,
        direction: str = "both",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        client: Optional[httpx.AsyncClient] = None
    ) -> List[Transfer]:
        self._check_provider_support()
        results: List[Transfer] = []
        is_truncated = False
        addr_lower = address.lower()

        native_price = await PricingService.get_price_usd(self.native_symbol, client)

        actions = [
            ("tokentx", "ERC20"),
            ("txlist", "NATIVE"),
            ("txlistinternal", "INTERNAL")
        ]

        max_pages = getattr(settings, "ADAPTER_MAX_PAGES", 5)
        max_transfers = getattr(settings, "ADAPTER_MAX_TRANSFERS_PER_ADDRESS", 500)

        for action_name, action_type in actions:
            if len(results) >= max_transfers:
                is_truncated = True
                break

            for page in range(1, max_pages + 1):
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

                    if direction == "out" and from_lower != addr_lower:
                        continue
                    if direction == "in" and to_lower != addr_lower:
                        continue

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
                    else:
                        symbol = self.native_symbol
                        raw_val = float(it.get("value", 0) or 0)
                        amt = raw_val / 1e18
                        amt_usd = amt * native_price

                    results.append(Transfer(
                        chain=self.chain_id,
                        tx_hash=it.get("hash", ""),
                        block_number=int(it.get("blockNumber", 0) or 0),
                        timestamp=ts,
                        from_address=from_addr,
                        to_address=to_addr,
                        token=symbol,
                        amount=amt,
                        amount_usd=amt_usd,
                        is_contract_call=(action_type != "NATIVE"),
                        method=it.get("functionName"),
                        truncated=False
                    ))

                    if len(results) >= max_transfers:
                        is_truncated = True
                        break

                if is_truncated or len(items) < min(limit, 100):
                    break

                if page == max_pages:
                    is_truncated = True

        if is_truncated:
            for t in results:
                t.truncated = True

        return results

    async def get_transaction(self, tx_hash: str, client: Optional[httpx.AsyncClient] = None) -> Optional[Transaction]:
        self._check_provider_support()
        params = {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash
        }
        data = await self._fetch_with_retry(client, params)
        tx_data = data.get("result")
        if not tx_data or not isinstance(tx_data, dict):
            return None

        val_hex = tx_data.get("value", "0x0")
        val_eth = int(val_hex, 16) / 1e18 if isinstance(val_hex, str) and val_hex.startswith("0x") else 0.0

        receipt_params = {
            "module": "proxy",
            "action": "eth_getTransactionReceipt",
            "txhash": tx_hash
        }
        receipt_data = await self._fetch_with_retry(client, receipt_params)
        receipt = receipt_data.get("result", {})
        status = "success" if receipt.get("status") == "0x1" else "failed"

        gas_used = int(receipt.get("gasUsed", "0x0"), 16) if isinstance(receipt.get("gasUsed"), str) else 0
        gas_price = int(tx_data.get("gasPrice", "0x0"), 16) if isinstance(tx_data.get("gasPrice"), str) else 0
        fee_native = (gas_used * gas_price) / 1e18
        native_price = await PricingService.get_price_usd(self.native_symbol, client)

        blk_hex = tx_data.get("blockNumber", "0x0")
        blk_num = int(blk_hex, 16) if isinstance(blk_hex, str) and blk_hex.startswith("0x") else 0

        return Transaction(
            chain=self.chain_id,
            tx_hash=tx_hash,
            block_number=blk_num,
            timestamp=datetime.now(timezone.utc),
            from_address=tx_data.get("from", ""),
            to_address=tx_data.get("to", ""),
            value=val_eth,
            fee_usd=fee_native * native_price,
            status=status
        )

    async def get_balance(self, address: str, client: Optional[httpx.AsyncClient] = None) -> List[TokenBalance]:
        self._check_provider_support()
        summary = await self.get_address_summary(address, client=client)
        native_price = await PricingService.get_price_usd(self.native_symbol, client)
        bal_native = summary.balance_usd / native_price if native_price > 0 else 0.0
        return [
            TokenBalance(
                token=self.native_symbol,
                symbol=self.native_symbol,
                balance=bal_native,
                balance_usd=summary.balance_usd
            )
        ]

    def normalize(self, raw: dict) -> Transfer:
        val = float(raw.get("value", 0)) / 1e18
        return Transfer(
            chain=self.chain_id,
            tx_hash=raw.get("hash", ""),
            block_number=int(raw.get("blockNumber", 0)),
            timestamp=datetime.fromtimestamp(int(raw.get("timeStamp", 0)), tz=timezone.utc),
            from_address=raw.get("from", ""),
            to_address=raw.get("to", ""),
            token=raw.get("tokenSymbol", self.native_symbol),
            amount=val,
            amount_usd=val * 3000.0
        )
