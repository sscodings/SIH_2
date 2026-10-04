import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx
from app.adapters.base import ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance, AdapterError, RateLimited
from app.core.config import settings
from app.adapters.http import HttpClientManager
from app.services.pricing import PricingService

logger = logging.getLogger(__name__)

class TronAdapter(ChainAdapter):
    chain_id: str = "tron"

    def __init__(self):
        self.api_key = settings.TRONGRID_API_KEY
        self.base_url = "https://api.trongrid.io"
        self.http_mgr = HttpClientManager.get_instance()

    def _get_headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers["TRON-PRO-API-KEY"] = self.api_key
        return headers

    async def _fetch_with_retry(
        self,
        client: Optional[httpx.AsyncClient],
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        resp = await self.http_mgr.request(
            provider="trongrid",
            method="GET",
            url=url,
            params=params,
            headers=self._get_headers(),
            client=client,
            max_retries=max_retries
        )

        if resp.status_code in (403, 429):
            raise RateLimited(f"TronGrid HTTP {resp.status_code}: Rate limit or quota reached")
        if resp.status_code >= 400:
            raise AdapterError(f"TronGrid HTTP {resp.status_code}: {resp.text}")

        try:
            data = resp.json()
        except Exception as e:
            raise AdapterError(f"Malformed JSON response from TronGrid: {resp.text}") from e

        if not isinstance(data, dict):
            raise AdapterError(f"Malformed response structure from TronGrid: {data}")

        return data

    async def get_address_summary(self, address: str, client: Optional[httpx.AsyncClient] = None) -> AddressSummary:
        url = f"{self.base_url}/v1/accounts/{address}"
        data = await self._fetch_with_retry(client, url)
        account_data = data.get("data", [{}])
        if not account_data:
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
                    total_balance_usd += val  # Default assuming USDT 1.0 peg
                except Exception:
                    pass

        create_time = acc.get("create_time")
        first_seen = datetime.fromtimestamp(create_time / 1000.0, tz=timezone.utc) if create_time else None
        latest_op_time = acc.get("latest_opration_time")
        last_seen = datetime.fromtimestamp(latest_op_time / 1000.0, tz=timezone.utc) if latest_op_time else None

        # Sample transfers
        transfers = await self.get_transfers(address, limit=50, client=client)
        total_rec = sum(t.amount_usd for t in transfers if t.to_address == address)
        total_sent = sum(t.amount_usd for t in transfers if t.from_address == address)
        is_trunc = any(t.truncated for t in transfers)

        return AddressSummary(
            address=address,
            chain="tron",
            total_received=total_rec / trx_price if trx_price > 0 else 0.0,
            total_received_usd=total_rec,
            total_sent=total_sent / trx_price if trx_price > 0 else 0.0,
            total_sent_usd=total_sent,
            balance_usd=total_balance_usd,
            tx_count=len(transfers),
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
        results: List[Transfer] = []
        is_truncated = False
        max_pages = getattr(settings, "ADAPTER_MAX_PAGES", 5)
        max_transfers = getattr(settings, "ADAPTER_MAX_TRANSFERS_PER_ADDRESS", 500)

        # 1. Fetch TRC20 transfers
        trc20_url = f"{self.base_url}/v1/accounts/{address}/transactions/trc20"
        fingerprint = None

        for page in range(1, max_pages + 1):
            params: Dict[str, Any] = {"limit": min(limit, 100)}
            if fingerprint:
                params["fingerprint"] = fingerprint
            if since:
                params["min_timestamp"] = int(since.timestamp() * 1000)
            if until:
                params["max_timestamp"] = int(until.timestamp() * 1000)

            data = await self._fetch_with_retry(client, trc20_url, params=params)
            items = data.get("data", [])
            if not isinstance(items, list) or len(items) == 0:
                break

            for it in items:
                from_addr = it.get("from", "")
                to_addr = it.get("to", "")
                if direction == "out" and from_addr != address:
                    continue
                if direction == "in" and to_addr != address:
                    continue

                token_info = it.get("token_info", {})
                symbol = token_info.get("symbol", "USDT")
                decimals = int(token_info.get("decimals", 6) or 6)
                raw_val = float(it.get("value", 0) or 0)
                amt = raw_val / (10 ** decimals)
                token_price = 1.0 if symbol in ["USDT", "USDC"] else await PricingService.get_price_usd(symbol, client)
                amt_usd = amt * token_price
                ts = datetime.fromtimestamp(int(it.get("block_timestamp", 0) or 0) / 1000.0, tz=timezone.utc)

                results.append(Transfer(
                    chain="tron",
                    tx_hash=it.get("transaction_id", ""),
                    block_number=0,
                    timestamp=ts,
                    from_address=from_addr,
                    to_address=to_addr,
                    token=symbol,
                    amount=amt,
                    amount_usd=amt_usd,
                    is_contract_call=True,
                    truncated=False
                ))

                if len(results) >= max_transfers:
                    is_truncated = True
                    break

            meta = data.get("meta", {})
            fingerprint = meta.get("fingerprint")
            if not fingerprint or is_truncated:
                break

            if page == max_pages:
                is_truncated = True

        if is_truncated:
            for t in results:
                t.truncated = True

        return results

    async def get_transaction(self, tx_hash: str, client: Optional[httpx.AsyncClient] = None) -> Optional[Transaction]:
        url = f"{self.base_url}/wallet/gettransactionbyid"
        json_body = {"value": tx_hash}
        resp = await self.http_mgr.request(
            provider="trongrid",
            method="POST",
            url=url,
            headers=self._get_headers(),
            json_data=json_body,
            client=client
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data or not data.get("txID"):
            return None

        raw_data = data.get("raw_data", {})
        contracts = raw_data.get("contract", [{}])
        contract = contracts[0] if contracts else {}
        val_obj = contract.get("parameter", {}).get("value", {})
        from_hex = val_obj.get("owner_address", "")
        to_hex = val_obj.get("to_address", "")
        amt_sun = val_obj.get("amount", 0)
        amt_trx = amt_sun / 1_000_000.0
        trx_price = await PricingService.get_price_usd("TRX", client)

        return Transaction(
            chain="tron",
            tx_hash=tx_hash,
            block_number=0,
            timestamp=datetime.fromtimestamp(raw_data.get("timestamp", 0) / 1000.0, tz=timezone.utc),
            from_address=from_hex,
            to_address=to_hex,
            value=amt_trx,
            fee_usd=0.0,
            status="success"
        )

    async def get_balance(self, address: str, client: Optional[httpx.AsyncClient] = None) -> List[TokenBalance]:
        summary = await self.get_address_summary(address, client=client)
        trx_price = await PricingService.get_price_usd("TRX", client)
        bal_trx = summary.balance_usd / trx_price if trx_price > 0 else 0.0
        return [
            TokenBalance(
                token="TRX",
                symbol="TRX",
                balance=bal_trx,
                balance_usd=summary.balance_usd
            )
        ]

    def normalize(self, raw: dict) -> Transfer:
        amt = float(raw.get("value", 0)) / 1_000_000.0
        return Transfer(
            chain="tron",
            tx_hash=raw.get("transaction_id", ""),
            block_number=0,
            timestamp=datetime.fromtimestamp(raw.get("block_timestamp", 0) / 1000.0, tz=timezone.utc),
            from_address=raw.get("from", ""),
            to_address=raw.get("to", ""),
            token="USDT",
            amount=amt,
            amount_usd=amt * 1.0
        )
