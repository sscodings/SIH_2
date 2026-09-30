from typing import Protocol, List, Optional
from pydantic import BaseModel
from datetime import datetime

class AdapterError(Exception):
    """Raised when live blockchain adapter encounters an unrecoverable failure (network, rate limit, timeout, malformed payload, pricing failure)."""
    pass

class TokenBalance(BaseModel):
    token: str
    symbol: str
    balance: float
    balance_usd: float

class AddressSummary(BaseModel):
    address: str
    chain: str
    total_received: float
    total_received_usd: float
    total_sent: float
    total_sent_usd: float
    balance_usd: float
    tx_count: int
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    entity_label: Optional[str] = None
    entity_type: Optional[str] = None
    truncated: bool = False

class Transfer(BaseModel):
    chain: str
    tx_hash: str
    block_number: int = 0
    timestamp: datetime
    from_address: str
    to_address: str
    token: str = "USDT"
    amount: float
    amount_usd: float
    is_contract_call: bool = False
    method: Optional[str] = None
    log_index: int = 0
    multi_input: bool = False
    truncated: bool = False

class Transaction(BaseModel):
    chain: str
    tx_hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    value: float
    fee_usd: float = 0.0
    status: str = "success"

class ChainAdapter(Protocol):
    chain_id: str

    async def get_address_summary(self, address: str) -> AddressSummary:
        ...

    async def get_transfers(self, address: str, direction: str = "both", since: Optional[datetime] = None, until: Optional[datetime] = None, limit: int = 100) -> List[Transfer]:
        ...

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        ...

    async def get_balance(self, address: str) -> List[TokenBalance]:
        ...

    def normalize(self, raw: dict) -> Transfer:
        ...
