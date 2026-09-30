import logging
import httpx
from datetime import datetime
from typing import List, Optional
from backend.app.adapters.base import ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance
from backend.app.adapters.demo import DemoAdapter
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

EVM_ENDPOINTS = {
    "ethereum": "https://api.etherscan.io/api",
    "bsc": "https://api.bscscan.com/api",
    "polygon": "https://api.polygonscan.com/api",
    "arbitrum": "https://api.arbiscan.io/api"
}

class EvmAdapter(ChainAdapter):
    def __init__(self, chain_id: str = "ethereum"):
        self.chain_id = chain_id
        self.api_key = settings.ETHERSCAN_API_KEY
        self.base_url = EVM_ENDPOINTS.get(chain_id, EVM_ENDPOINTS["ethereum"])
        self.demo_fallback = DemoAdapter(chain_id)

    async def get_address_summary(self, address: str) -> AddressSummary:
        return await self.demo_fallback.get_address_summary(address)

    async def get_transfers(self, address: str, direction: str = "both", since: Optional[datetime] = None, limit: int = 100) -> List[Transfer]:
        if not self.api_key and settings.CHAINNETRA_MODE != "LIVE":
            return await self.demo_fallback.get_transfers(address, direction, since, limit)
        try:
            params = {
                "module": "account",
                "action": "tokentx",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": min(limit, 50),
                "sort": "desc",
                "apikey": self.api_key or ""
            }
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(self.base_url, params=params)
                if res.status_code == 200 and res.json().get("status") == "1":
                    items = res.json().get("result", [])
                    results = []
                    for it in items:
                        val = float(it.get("value", 0)) / (10 ** int(it.get("tokenDecimal", 18) or 18))
                        ts = datetime.fromtimestamp(int(it.get("timeStamp", 0)))
                        results.append(Transfer(
                            chain=self.chain_id,
                            tx_hash=it.get("hash", ""),
                            block_number=int(it.get("blockNumber", 0)),
                            timestamp=ts,
                            from_address=it.get("from", ""),
                            to_address=it.get("to", ""),
                            token=it.get("tokenSymbol", "USDT"),
                            amount=val,
                            amount_usd=val
                        ))
                    if results:
                        return results
        except Exception as e:
            logger.warning(f"EVM ({self.chain_id}) API error: {e}. Falling back to demo data.")
        return await self.demo_fallback.get_transfers(address, direction, since, limit)

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        return await self.demo_fallback.get_transaction(tx_hash)

    async def get_balance(self, address: str) -> List[TokenBalance]:
        return await self.demo_fallback.get_balance(address)

    def normalize(self, raw: dict) -> Transfer:
        return Transfer(**raw)
