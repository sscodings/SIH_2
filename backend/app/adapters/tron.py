import logging
import httpx
from datetime import datetime
from typing import List, Optional
from backend.app.adapters.base import ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance
from backend.app.adapters.demo import DemoAdapter
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class TronAdapter(ChainAdapter):
    chain_id: str = "tron"

    def __init__(self):
        self.api_key = settings.TRONGRID_API_KEY
        self.base_url = "https://api.trongrid.io"
        self.demo_fallback = DemoAdapter("tron")

    async def get_address_summary(self, address: str) -> AddressSummary:
        if not self.api_key and settings.CHAINNETRA_MODE != "LIVE":
            return await self.demo_fallback.get_address_summary(address)
        try:
            headers = {"TRON-PRO-API-KEY": self.api_key} if self.api_key else {}
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(f"{self.base_url}/v1/accounts/{address}", headers=headers)
                if res.status_code == 200:
                    data = res.json().get("data", [{}])[0]
                    balance_trx = data.get("balance", 0) / 1_000_000.0
                    return AddressSummary(
                        address=address,
                        chain="tron",
                        total_received=0.0,
                        total_received_usd=0.0,
                        total_sent=0.0,
                        total_sent_usd=0.0,
                        balance_usd=balance_trx * 0.15,
                        tx_count=len(data.get("trc20", []))
                    )
        except Exception as e:
            logger.warning(f"TronGrid API error: {e}. Falling back to DemoAdapter.")
        return await self.demo_fallback.get_address_summary(address)

    async def get_transfers(self, address: str, direction: str = "both", since: Optional[datetime] = None, limit: int = 100) -> List[Transfer]:
        if not self.api_key and settings.CHAINNETRA_MODE != "LIVE":
            return await self.demo_fallback.get_transfers(address, direction, since, limit)
        try:
            headers = {"TRON-PRO-API-KEY": self.api_key} if self.api_key else {}
            async with httpx.AsyncClient(timeout=6.0) as client:
                url = f"{self.base_url}/v1/accounts/{address}/transactions/trc20?limit={min(limit, 50)}"
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    items = res.json().get("data", [])
                    results = []
                    for it in items:
                        val = float(it.get("value", 0)) / 1_000_000.0
                        ts = datetime.fromtimestamp(it.get("block_timestamp", 0) / 1000.0)
                        results.append(Transfer(
                            chain="tron",
                            tx_hash=it.get("transaction_id", ""),
                            block_number=0,
                            timestamp=ts,
                            from_address=it.get("from", ""),
                            to_address=it.get("to", ""),
                            token=it.get("token_info", {}).get("symbol", "USDT"),
                            amount=val,
                            amount_usd=val
                        ))
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"TronGrid transfer fetch error: {e}. Falling back to demo data.")
        return await self.demo_fallback.get_transfers(address, direction, since, limit)

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        return await self.demo_fallback.get_transaction(tx_hash)

    async def get_balance(self, address: str) -> List[TokenBalance]:
        return await self.demo_fallback.get_balance(address)

    def normalize(self, raw: dict) -> Transfer:
        return Transfer(**raw)
