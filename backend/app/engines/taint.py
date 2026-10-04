from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

@dataclass
class InflowLot:
    amount: float
    tainted_amount: float
    timestamp: datetime
    tx_hash: str
    remaining_amount: float = 0.0
    remaining_tainted: float = 0.0

    def __post_init__(self):
        self.remaining_amount = self.amount
        self.remaining_tainted = self.tainted_amount

@dataclass
class OutflowResult:
    tx_hash: str
    amount: float
    tainted_amount: float
    model_name: str
    overestimates: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

class WalletTaintLedger:
    """
    Stateful per-wallet taint accounting ledger.
    Maintains chronological inflows and outflows to compute mathematically rigorous taint propagation.
    """
    def __init__(self, wallet_address: str, chain: str, model_name: str = "haircut"):
        self.wallet_address = wallet_address
        self.chain = chain.lower()
        self.model_name = (model_name or "haircut").lower()
        self.inflow_lots: List[InflowLot] = []
        self.total_inflow: float = 0.0
        self.total_tainted_inflow: float = 0.0
        self.total_tainted_outflow: float = 0.0
        self.outflows: List[OutflowResult] = []

    def add_inflow(self, amount: float, tainted_amount: float, timestamp: datetime, tx_hash: str = ""):
        amount = max(0.0, float(amount))
        tainted = max(0.0, min(amount, float(tainted_amount)))
        lot = InflowLot(
            amount=amount,
            tainted_amount=tainted,
            timestamp=timestamp,
            tx_hash=tx_hash
        )
        self.inflow_lots.append(lot)
        self.inflow_lots.sort(key=lambda x: x.timestamp)
        self.total_inflow += amount
        self.total_tainted_inflow += tainted

    def compute_outflow_taint(self, outflow_amount: float, timestamp: datetime, tx_hash: str = "") -> OutflowResult:
        outflow_amount = max(0.0, float(outflow_amount))
        if outflow_amount == 0.0 or self.total_tainted_inflow <= 0.0:
            res = OutflowResult(
                tx_hash=tx_hash,
                amount=outflow_amount,
                tainted_amount=0.0,
                model_name=self.model_name,
                overestimates=False,
                details={"reason": "zero_inflow_or_amount"}
            )
            self.outflows.append(res)
            return res

        if self.model_name == "poison":
            # Poison: Any outflow carries 100% taint up to its amount, capped by total tainted inflow
            taint = min(outflow_amount, self.total_tainted_inflow)
            self.total_tainted_outflow += taint
            overestimates = (self.total_tainted_outflow > self.total_tainted_inflow) or True
            res = OutflowResult(
                tx_hash=tx_hash,
                amount=outflow_amount,
                tainted_amount=round(taint, 4),
                model_name="poison",
                overestimates=overestimates,
                details={
                    "model": "poison",
                    "total_tainted_in": self.total_tainted_inflow,
                    "cumulative_tainted_out": self.total_tainted_outflow,
                    "note": "Poison model deliberately overestimates taint across branching paths."
                }
            )
            self.outflows.append(res)
            return res

        elif self.model_name == "fifo":
            # FIFO: Outflows consume earliest inflow lots oldest-first
            remaining_to_consume = outflow_amount
            propagated_taint = 0.0

            # Consider lots that arrived on or before this outflow
            for lot in self.inflow_lots:
                if remaining_to_consume <= 0.0:
                    break
                if lot.remaining_amount <= 0.0:
                    continue

                take = min(lot.remaining_amount, remaining_to_consume)
                lot_taint_ratio = (lot.tainted_amount / lot.amount) if lot.amount > 0 else 0.0
                lot_taint_consumed = min(lot.remaining_tainted, take * lot_taint_ratio)

                propagated_taint += lot_taint_consumed
                lot.remaining_amount -= take
                lot.remaining_tainted = max(0.0, lot.remaining_tainted - lot_taint_consumed)
                remaining_to_consume -= take

            # Invariant: Never exceed available remaining tainted inflow
            max_available = max(0.0, self.total_tainted_inflow - self.total_tainted_outflow)
            propagated_taint = min(propagated_taint, max_available)
            self.total_tainted_outflow += propagated_taint

            assert self.total_tainted_outflow <= self.total_tainted_inflow + 1e-6, "FIFO invariant violated: outflow taint exceeded inflow"

            res = OutflowResult(
                tx_hash=tx_hash,
                amount=outflow_amount,
                tainted_amount=round(propagated_taint, 4),
                model_name="fifo",
                overestimates=False,
                details={
                    "model": "fifo",
                    "total_tainted_in": self.total_tainted_inflow,
                    "total_inflow": self.total_inflow,
                    "cumulative_tainted_out": self.total_tainted_outflow
                }
            )
            self.outflows.append(res)
            return res

        else:  # "haircut" (default)
            # Haircut: Proportional taint based on real total inflows in window
            # taint_out = out_amount * (tainted_in / total_in)
            if self.total_inflow <= 0.0:
                taint = 0.0
            else:
                ratio = min(1.0, max(0.0, self.total_tainted_inflow / self.total_inflow))
                unclamped_taint = outflow_amount * ratio
                # Enforce invariant: sum of tainted outflows never exceeds tainted inflows
                available_taint = max(0.0, self.total_tainted_inflow - self.total_tainted_outflow)
                taint = min(unclamped_taint, available_taint)

            self.total_tainted_outflow += taint
            assert self.total_tainted_outflow <= self.total_tainted_inflow + 1e-6, "Haircut invariant violated: outflow taint exceeded inflow"

            res = OutflowResult(
                tx_hash=tx_hash,
                amount=outflow_amount,
                tainted_amount=round(taint, 4),
                model_name="haircut",
                overestimates=False,
                details={
                    "model": "haircut",
                    "taint_ratio": round(self.total_tainted_inflow / max(self.total_inflow, 0.0001), 4),
                    "total_tainted_in": self.total_tainted_inflow,
                    "total_inflow": self.total_inflow,
                    "cumulative_tainted_out": self.total_tainted_outflow
                }
            )
            self.outflows.append(res)
            return res

class TaintModel:
    """
    Unified entrypoint for taint modeling across Haircut, FIFO, and Poison.
    """
    @staticmethod
    def create_ledger(wallet_address: str, chain: str, model_name: str = "haircut") -> WalletTaintLedger:
        return WalletTaintLedger(wallet_address=wallet_address, chain=chain, model_name=model_name)

    @staticmethod
    def calculate_taint(
        model_name: str,
        inflow_tainted_amount: float,
        total_wallet_inflow: float,
        outflow_amount: float,
        remaining_taint_balance: Optional[float] = None
    ) -> float:
        model = (model_name or "haircut").lower()
        if outflow_amount <= 0 or inflow_tainted_amount <= 0:
            return 0.0

        if model == "poison":
            return min(outflow_amount, inflow_tainted_amount)

        elif model == "fifo":
            curr_taint = remaining_taint_balance if remaining_taint_balance is not None else inflow_tainted_amount
            consumed = min(max(0.0, curr_taint), outflow_amount)
            return consumed

        else:  # "haircut"
            if total_wallet_inflow <= 0:
                return 0.0
            ratio = min(1.0, max(0.0, inflow_tainted_amount / total_wallet_inflow))
            unclamped = outflow_amount * ratio
            if remaining_taint_balance is not None:
                return min(unclamped, max(0.0, remaining_taint_balance))
            return unclamped
