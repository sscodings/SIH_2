import asyncio
import logging
import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.adapters.base import ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance, AdapterError
from app.core.config import settings
from app.services.pricing import PricingService

logger = logging.getLogger(__name__)

class TronAdapter(ChainAdapter):
    chain_id: str = "tron"

    def __init__(self):
        self.api_key = settings.TRONGRID_API_KEY
        self.base_url = "https://api.trongrid.io"

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers["TRON-PRO-API-KEY"] = self.api_key
        return headers

    async def _fetch_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                res = await client.get(url, params=params, headers=self._get_headers(), timeout=settings.ADAPTER_TIMEOUT)
                if res.status_code == 429:
                    # Rate limited - backoff
                    await asyncio.sleep(0.3 * (2 ** attempt))
                    continue
                if res.status_code >= 400:
                    raise AdapterError(f"TronGrid HTTP {res.status_code}: {res.text}")
                data = res.json()
                if not isinstance(data, dict):
                    raise AdapterError(f"Malformed response from TronGrid: {data}")
                return data
            except Exception as e:
                last_error = e
                if isinstance(e, AdapterError):
                    if attempt == max_retries:
                        raise
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (2 ** (attempt - 1)))
                else:
                    if isinstance(e, AdapterError):
                        raise
                    raise AdapterError(f"TronGrid request failed after {max_retries} attempts: {str(e)}") from e
        raise AdapterError(f"TronGrid request failed: {last_error}")

    async def get_address_summary(self, address: str) -> AddressSummary:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/v1/accounts/{address}"
            data = await self._fetch_with_retry(client, url)
            account_data = data.get("data", [{}])
            if not account_data:
                # Fresh account with no txs
                return AddressSummary(
                    address=address,
                    chain="tron",
                    total_received=0.0,
                    total_received_usd=0.0,
                    total_sent=0.0,
                    total_sent_usd=0.0,
                    balance_usd=0.0,
                    tx_count=0
                )
            acc = account_data[0]
            balance_trx = acc.get("balance", 0) / 1_000_000.0
            trx_price = await PricingService.get_price_usd("TRX", client)
            total_balance_usd = balance_trx * trx_price

            # Sum TRC20 balances
            for token_obj in acc.get("trc20", []):
                for token_contract, val_str in token_obj.items():
                    try:
                        val = float(val_str) / 1_000_000.0
                        total_balance_usd += val  # Default assuming USDT 1.0
                    except Exception:
                        pass

            create_time = acc.get("create_time")
            first_seen = datetime.fromtimestamp(create_time / 1000.0, tz=timezone.utc) if create_time else None

            return AddressSummary(
                address=address,
                chain="tron",
                total_received=0.0,
                total_received_usd=0.0,
                total_sent=0.0,
                total_sent_usd=0.0,
                balance_usd=round(total_balance_usd, 2),
                tx_count=len(acc.get("trc20", [])) + 1,
                first_seen=first_seen
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

        async with httpx.AsyncClient() as client:
            trx_price = await PricingService.get_price_usd("TRX", client)

            # 1. Fetch TRC-20 token transfers
            trc20_url = f"{self.base_url}/v1/accounts/{address}/transactions/trc20"
            fingerprint = None

            for page in range(settings.ADAPTER_MAX_PAGES):
                params: Dict[str, Any] = {
                    "limit": min(limit, 50),
                    "order_by": "block_timestamp,desc"
                }
                if direction == "out":
                    params["only_from"] = "true"
                elif direction == "in":
                    params["only_to"] = "true"

                if since:
                    params["min_timestamp"] = int(since.timestamp() * 1000)
                if until:
                    params["max_timestamp"] = int(until.timestamp() * 1000)

                if fingerprint:
                    params["fingerprint"] = fingerprint

                data = await self._fetch_with_retry(client, trc20_url, params=params)
                items = data.get("data", [])
                for it in items:
                    token_info = it.get("token_info", {})
                    symbol = token_info.get("symbol", "USDT").upper()
                    decimals = int(token_info.get("decimals", 6) or 6)
                    raw_val = float(it.get("value", 0))
                    amt = raw_val / (10 ** decimals)
                    
                    token_price = 1.0 if symbol in ["USDT", "USDC"] else await PricingService.get_price_usd(symbol, client)
                    amt_usd = amt * token_price
                    ts = datetime.fromtimestamp(it.get("block_timestamp", 0) / 1000.0, tz=timezone.utc)

                    from_addr = it.get("from", "")
                    to_addr = it.get("to", "")

                    if direction == "out" and from_addr.lower() != address.lower():
                        continue
                    if direction == "in" and to_addr.lower() != address.lower():
                        continue
                    if since and ts < since.replace(tzinfo=timezone.utc if since.tzinfo is None else since.tzinfo):
                        continue
                    if until and ts > until.replace(tzinfo=timezone.utc if until.tzinfo is None else until.tzinfo):
                        continue

                    results.append(Transfer(
                        chain="tron",
                        tx_hash=it.get("transaction_id", ""),
                        block_number=0,
                        timestamp=ts,
                        from_address=from_addr,
                        to_address=to_addr,
                        token=symbol,
                        amount=amt,
                        amount_usd=round(amt_usd, 2)
                    ))

                meta = data.get("meta", {})
                fingerprint = meta.get("fingerprint")
                if not fingerprint or len(items) == 0:
                    break
                if page == settings.ADAPTER_MAX_PAGES - 1 and fingerprint:
                    is_truncated = True

            # 2. Fetch Native TRX Transfers
            trx_url = f"{self.base_url}/v1/accounts/{address}/transactions"
            fingerprint = None
            for page in range(min(2, settings.ADAPTER_MAX_PAGES)):
                params = {
                    "limit": min(limit, 50),
                    "order_by": "block_timestamp,desc"
                }
                if direction == "out":
                    params["only_from"] = "true"
                elif direction == "in":
                    params["only_to"] = "true"
                if since:
                    params["min_timestamp"] = int(since.timestamp() * 1000)
                if until:
                    params["max_timestamp"] = int(until.timestamp() * 1000)
                if fingerprint:
                    params["fingerprint"] = fingerprint

                data = await self._fetch_with_retry(client, trx_url, params=params)
                items = data.get("data", [])
                for it in items:
                    raw_data = it.get("raw_data", {})
                    contracts = raw_data.get("contract", [])
                    ts = datetime.fromtimestamp(it.get("block_timestamp", 0) / 1000.0, tz=timezone.utc)

                    if since and ts < since.replace(tzinfo=timezone.utc if since.tzinfo is None else since.tzinfo):
                        continue
                    if until and ts > until.replace(tzinfo=timezone.utc if until.tzinfo is None else until.tzinfo):
                        continue

                    for contract in contracts:
                        if contract.get("type") == "TransferContract":
                            val_obj = contract.get("parameter", {}).get("value", {})
                            amt_sun = val_obj.get("amount", 0)
                            amt_trx = amt_sun / 1_000_000.0
                            owner_addr = val_obj.get("owner_address", "")
                            to_addr = val_obj.get("to_address", "")

                            results.append(Transfer(
                                chain="tron",
                                tx_hash=it.get("txID", ""),
                                block_number=0,
                                timestamp=ts,
                                from_address=owner_addr,
                                to_address=to_addr,
                                token="TRX",
                                amount=amt_trx,
                                amount_usd=round(amt_trx * trx_price, 2)
                            ))

                meta = data.get("meta", {})
                fingerprint = meta.get("fingerprint")
                if not fingerprint or len(items) == 0:
                    break

        if is_truncated and results:
            results[-1].truncated = True

        return results

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/v1/transactions/{tx_hash}"
            try:
                data = await self._fetch_with_retry(client, url)
                items = data.get("data", [])
                if not items:
                    return None
                it = items[0]
                ts = datetime.fromtimestamp(it.get("block_timestamp", 0) / 1000.0, tz=timezone.utc)
                return Transaction(
                    chain="tron",
                    tx_hash=tx_hash,
                    block_number=it.get("blockNumber", 0),
                    timestamp=ts,
                    from_address=it.get("ownerAddress", ""),
                    to_address=it.get("toAddress", ""),
                    value=0.0,
                    status="success"
                )
            except Exception as e:
                raise AdapterError(f"Failed to fetch Tron transaction {tx_hash}: {e}")

    async def get_balance(self, address: str) -> List[TokenBalance]:
        summary = await self.get_address_summary(address)
        return [TokenBalance(token="TRX", symbol="TRX", balance=0.0, balance_usd=summary.balance_usd)]

    def normalize(self, raw: dict) -> Transfer:
        return Transfer(**raw)
