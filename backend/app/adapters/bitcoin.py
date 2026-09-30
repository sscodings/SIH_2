import logging
import httpx
from datetime import datetime
from typing import List, Optional
from backend.app.adapters.base import ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance
from backend.app.adapters.demo import DemoAdapter
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class BitcoinAdapter(ChainAdapter):
    chain_id: str = "bitcoin"

    def __init__(self):
        self.base_url = "https://blockstream.info/api"
        self.demo_fallback = DemoAdapter("bitcoin")

    async def get_address_summary(self, address: str) -> AddressSummary:
        if settings.CHAINNETRA_MODE != "LIVE":
            return await self.demo_fallback.get_address_summary(address)
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(f"{self.base_url}/address/{address}")
                if res.status_code == 200:
                    data = res.json()
                    chain_stats = data.get("chain_stats", {})
                    funded = chain_stats.get("funded_txo_sum", 0) / 100_000_000.0
                    spent = chain_stats.get("spent_txo_sum", 0) / 100_000_000.0
                    bal = funded - spent
                    return AddressSummary(
                        address=address,
                        chain="bitcoin",
                        total_received=funded,
                        total_received_usd=funded * 65000.0,
                        total_sent=spent,
                        total_sent_usd=spent * 65000.0,
                        balance_usd=bal * 65000.0,
                        tx_count=chain_stats.get("tx_count", 0)
                    )
        except Exception as e:
            logger.warning(f"Bitcoin Esplora error: {e}. Falling back to demo data.")
        return await self.demo_fallback.get_address_summary(address)

    async def get_transfers(self, address: str, direction: str = "both", since: Optional[datetime] = None, limit: int = 50) -> List[Transfer]:
        return await self.demo_fallback.get_transfers(address, direction, since, limit)

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        return await self.demo_fallback.get_transaction(tx_hash)

    async def get_balance(self, address: str) -> List[TokenBalance]:
        return await self.demo_fallback.get_balance(address)

    def normalize(self, raw: dict) -> Transfer:
        return Transfer(**raw)
