from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.adapters.base import ChainAdapter, AddressSummary, Transfer, Transaction, TokenBalance
from app.db.database import SessionLocal
from app.db.models import Transfer as DBTransfer, Wallet as DBWallet
from app.core.addresses import normalize

class DemoAdapter(ChainAdapter):
    def __init__(self, chain_id: str):
        self.chain_id = chain_id.lower()

    async def get_address_summary(self, address: str) -> AddressSummary:
        db: Session = SessionLocal()
        try:
            norm_addr = normalize(self.chain_id, address)
            wallet = db.query(DBWallet).filter(
                DBWallet.address == norm_addr,
                DBWallet.chain == self.chain_id
            ).first()
            if wallet:
                return AddressSummary(
                    address=wallet.address,
                    chain=wallet.chain,
                    total_received=wallet.total_in_usd,
                    total_received_usd=wallet.total_in_usd,
                    total_sent=wallet.total_out_usd,
                    total_sent_usd=wallet.total_out_usd,
                    balance_usd=wallet.balance_usd,
                    tx_count=wallet.tx_count,
                    first_seen=wallet.first_seen,
                    last_seen=wallet.last_seen,
                    entity_label=wallet.label,
                    entity_type=wallet.entity_type
                )
            # Default empty summary
            return AddressSummary(
                address=address,
                chain=self.chain_id,
                total_received=0.0,
                total_received_usd=0.0,
                total_sent=0.0,
                total_sent_usd=0.0,
                balance_usd=0.0,
                tx_count=0
            )
        finally:
            db.close()

    async def get_transfers(
        self,
        address: str,
        direction: str = "both",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 200
    ) -> List[Transfer]:
        db: Session = SessionLocal()
        try:
            norm_addr = normalize(self.chain_id, address)
            query = db.query(DBTransfer).filter(DBTransfer.chain == self.chain_id)
            if direction == "out":
                query = query.filter(DBTransfer.from_address == norm_addr)
            elif direction == "in":
                query = query.filter(DBTransfer.to_address == norm_addr)
            else:
                query = query.filter(
                    (DBTransfer.from_address == norm_addr) | (DBTransfer.to_address == norm_addr)
                )

            if since:
                query = query.filter(DBTransfer.timestamp >= since)
            if until:
                query = query.filter(DBTransfer.timestamp <= until)

            db_transfers = query.order_by(DBTransfer.timestamp.asc()).limit(limit).all()
            return [
                Transfer(
                    chain=t.chain,
                    tx_hash=t.tx_hash,
                    block_number=t.block_number,
                    timestamp=t.timestamp,
                    from_address=t.from_address,
                    to_address=t.to_address,
                    token=t.token,
                    amount=t.amount,
                    amount_usd=t.amount_usd,
                    is_contract_call=t.is_contract_call,
                    method=t.method_name,
                    log_index=t.log_index
                )
                for t in db_transfers
            ]
        finally:
            db.close()

    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        db: Session = SessionLocal()
        try:
            t = db.query(DBTransfer).filter(
                DBTransfer.chain == self.chain_id,
                DBTransfer.tx_hash == tx_hash
            ).first()
            if not t:
                return None
            return Transaction(
                chain=t.chain,
                tx_hash=t.tx_hash,
                block_number=t.block_number,
                timestamp=t.timestamp,
                from_address=t.from_address,
                to_address=t.to_address,
                value=t.amount
            )
        finally:
            db.close()

    async def get_balance(self, address: str) -> List[TokenBalance]:
        db: Session = SessionLocal()
        try:
            norm_addr = normalize(self.chain_id, address)
            wallet = db.query(DBWallet).filter(
                DBWallet.address == norm_addr,
                DBWallet.chain == self.chain_id
            ).first()
            bal = wallet.balance_usd if wallet else 0.0
            return [
                TokenBalance(
                    token="USDT",
                    symbol="USDT",
                    balance=bal,
                    balance_usd=bal
                )
            ]
        finally:
            db.close()

    def normalize(self, raw: dict) -> Transfer:
        return Transfer(**raw)
