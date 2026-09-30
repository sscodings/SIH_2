from typing import List, Dict

class TaintModel:
    """
    Implements the three industry-standard cryptocurrency taint models:
    1. Haircut: Proportional taint based on the ratio of tainted inputs to total wallet balance/inflows.
    2. FIFO: First-in, First-out matching where outflows consume the earliest tainted inflows until exhausted.
    3. Poison: 100% taint propagation where any outflow from a tainted wallet carries full taint value up to the transfer amount.
    """
    
    @staticmethod
    def calculate_taint(
        model_name: str,
        inflow_tainted_amount: float,
        total_wallet_inflow: float,
        outflow_amount: float,
        remaining_taint_balance: float = None
    ) -> float:
        model = (model_name or "haircut").lower()
        if outflow_amount <= 0:
            return 0.0

        if model == "poison":
            # Any outgoing transfer from a tainted wallet is considered fully tainted
            return outflow_amount

        elif model == "fifo":
            # First-In First-Out: Outflow consumes tainted balance directly until consumed
            curr_taint = remaining_taint_balance if remaining_taint_balance is not None else inflow_tainted_amount
            consumed = min(curr_taint, outflow_amount)
            return consumed

        else: # "haircut" (default)
            # Proportional Haircut: taint_ratio = tainted_in / total_in
            if total_wallet_inflow <= 0:
                return outflow_amount
            ratio = min(1.0, max(0.0, inflow_tainted_amount / total_wallet_inflow))
            return outflow_amount * ratio
