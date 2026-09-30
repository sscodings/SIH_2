import asyncio
import logging
import httpx
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.adapters.base import ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance, AdapterError
from app.core.config import settings
from app.services.pricing import PricingService

logger = logging.getLogger(__name__)

class BitcoinAdapter(ChainAdapter):
    chain_id: str = "bitcoin"

    def __init__(self):
        self.base_url = settings.BLOCKSTREAM_API_URL.rstrip('/')

    async def _fetch_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Any:
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                res = await client.get(url, params=params, timeout=settings.ADAPTER_TIMEOUT)
                if res.status_code == 429:
                    await asyncio.sleep(0.3 * (2 ** attempt))
                    continue
                if res.status_code >= 400:
                    raise AdapterError(f"Blockstream Esplora HTTP {res.status_code}: {res.text}")
                return res.json()
            except Exception as e:
                last_error = e
                if isinstance(e, AdapterError) and attempt == max_retries:
                    raise
                if attempt < max_retries:
                    await asyncio.sleep(0.2 * (2 ** (attempt - 1)))
                else:
                    if isinstance(e, AdapterError):
                        raise
                    raise AdapterError(f"Blockstream Esplora request failed after {max_retries} attempts: {str(e)}") from e
        raise AdapterError(f"Blockstream Esplora request failed: {last_error}")

    async def get_address_summary(self, address: str) -> AddressSummary:
        async with httpx.AsyncClient() as client:
            btc_price = await PricingService.get_price_usd("BTC", client)
            url = f"{self.base_url}/address/{address}"
            data = await self._fetch_with_retry(client, url)
            
            chain_stats = data.get("chain_stats", {})
            mempool_stats = data.get("mempool_stats", {})

            funded_sat = chain_stats.get("funded_txo_sum", 0) + mempool_stats.get("funded_txo_sum", 0)
            spent_sat = chain_stats.get("spent_txo_sum", 0) + mempool_stats.get("spent_txo_sum", 0)
            balance_sat = max(0, funded_sat - spent_sat)

            funded_btc = funded_sat / 100_000_000.0
            spent_btc = spent_sat / 100_000_000.0
            balance_btc = balance_sat / 100_000_000.0

            return AddressSummary(
                address=address,
                chain="bitcoin",
                total_received=round(funded_btc, 8),
                total_received_usd=round(funded_btc * btc_price, 2),
                total_sent=round(spent_btc, 8),
                total_sent_usd=round(spent_btc * btc_price, 2),
                balance_usd=round(balance_btc * btc_price, 2),
                tx_count=chain_stats.get("tx_count", 0) + mempool_stats.get("tx_count", 0)
            )

    async def get_transfers(
        self,
        address: str,
        direction: str = "both",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Transfer]:
        results: List[Transfer] = []
        is_truncated = False
        addr_lower = address.lower()

        async with httpx.AsyncClient() as client:
            btc_price = await PricingService.get_price_usd("BTC", client)
            last_seen_txid = None

            for page in range(settings.ADAPTER_MAX_PAGES):
                if last_seen_txid:
                    url = f"{self.base_url}/address/{address}/txs/chain/{last_seen_txid}"
                else:
                    url = f"{self.base_url}/address/{address}/txs"

                txs = await self._fetch_with_retry(client, url)
                if not isinstance(txs, list) or len(txs) == 0:
                    break

                for tx in txs:
                    tx_id = tx.get("txid", "")
                    status = tx.get("status", {})
                    block_time = status.get("block_time")
                    ts = datetime.fromtimestamp(block_time, tz=timezone.utc) if block_time else datetime.now(timezone.utc)

                    if since and ts < since.replace(tzinfo=timezone.utc if since.tzinfo is None else since.tzinfo):
                        continue
                    if until and ts > until.replace(tzinfo=timezone.utc if until.tzinfo is None else until.tzinfo):
                        continue

                    vin = tx.get("vin", [])
                    vout = tx.get("vout", [])
                    is_multi_input = len(vin) > 1

                    in_addrs = [
                        v.get("prevout", {}).get("scriptpubkey_address", "")
                        for v in vin if v.get("prevout")
                    ]
                    in_addrs_clean = [a for a in in_addrs if a]
                    in_addrs_lower = [a.lower() for a in in_addrs_clean]

                    # Check if address is sender
                    is_sender = any(a == addr_lower for a in in_addrs_lower)

                    if is_sender and direction in ["out", "both"]:
                        primary_from = address
                        for v in vout:
                            to_addr = v.get("scriptpubkey_address", "")
                            if not to_addr:
                                continue
                            sat_val = v.get("value", 0)
                            amt_btc = sat_val / 100_000_000.0
                            amt_usd = amt_btc * btc_price

                            results.append(Transfer(
                                chain="bitcoin",
                                tx_hash=tx_id,
                                block_number=status.get("block_height", 0) or 0,
                                timestamp=ts,
                                from_address=primary_from,
                                to_address=to_addr,
                                token="BTC",
                                amount=round(amt_btc, 8),
                                amount_usd=round(amt_usd, 2),
                                multi_input=is_multi_input
                            ))

                    # Check if address is receiver
                    for v in vout:
                        to_addr = v.get("scriptpubkey_address", "")
                        if to_addr and to_addr.lower() == addr_lower and direction in ["in", "both"]:
                            sat_val = v.get("value", 0)
                            amt_btc = sat_val / 100_000_000.0
                            amt_usd = amt_btc * btc_price
                            primary_from = in_addrs_clean[0] if in_addrs_clean else "coinbase"

                            results.append(Transfer(
                                chain="bitcoin",
                                tx_hash=tx_id,
                                block_number=status.get("block_height", 0) or 0,
                                timestamp=ts,
                                from_address=primary_from,
                                to_address=address,
                                token="BTC",
                                amount=round(amt_btc, 8),
                                amount_usd=round(amt_usd, 2),
                                multi_input=is_multi_input
                            ))

                last_seen_txid = txs[-1].get("txid")
                if len(txs) < 25:
                    break
                if page == settings.ADAPTER_MAX_PAGES - 1:
                    is_truncated = True

        if is_truncated and results:
            results[-1].truncated = True

        return results

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/tx/{tx_hash}"
            try:
                tx = await self._fetch_with_retry(client, url)
                status = tx.get("status", {})
                block_time = status.get("block_time")
                ts = datetime.fromtimestamp(block_time, tz=timezone.utc) if block_time else datetime.now(timezone.utc)

                vin = tx.get("vin", [])
                vout = tx.get("vout", [])

                from_addr = vin[0].get("prevout", {}).get("scriptpubkey_address", "coinbase") if vin and vin[0].get("prevout") else "coinbase"
                to_addr = vout[0].get("scriptpubkey_address", "") if vout else ""
                total_val = sum(v.get("value", 0) for v in vout) / 100_000_000.0

                return Transaction(
                    chain="bitcoin",
                    tx_hash=tx_hash,
                    block_number=status.get("block_height", 0) or 0,
                    timestamp=ts,
                    from_address=from_addr,
                    to_address=to_addr,
                    value=round(total_val, 8),
                    fee_usd=round((tx.get("fee", 0) / 100_000_000.0) * 65000.0, 2),
                    status="success" if status.get("confirmed") else "pending"
                )
            except Exception as e:
                raise AdapterError(f"Failed to fetch Bitcoin transaction {tx_hash}: {e}")

    async def get_balance(self, address: str) -> List[TokenBalance]:
        summary = await self.get_address_summary(address)
        return [TokenBalance(token="BTC", symbol="BTC", balance=summary.total_received - summary.total_sent, balance_usd=summary.balance_usd)]

    def normalize(self, raw: dict) -> Transfer:
        return Transfer(**raw)
