from typing import Dict
from backend.app.adapters.base import ChainAdapter
from backend.app.adapters.demo import DemoAdapter
from backend.app.adapters.tron import TronAdapter
from backend.app.adapters.evm import EvmAdapter
from backend.app.adapters.bitcoin import BitcoinAdapter
from backend.app.core.config import settings

_adapters: Dict[str, ChainAdapter] = {}

def get_chain_adapter(chain: str) -> ChainAdapter:
    chain = chain.lower()
    mode = settings.CHAINNETRA_MODE.upper()

    if mode == "DEMO":
        return DemoAdapter(chain)

    # In LIVE mode, instantiate live adapters
    key = f"{mode}:{chain}"
    if key in _adapters:
        return _adapters[key]

    if chain == "tron":
        adapter = TronAdapter()
    elif chain in ["ethereum", "bsc", "polygon", "arbitrum"]:
        adapter = EvmAdapter(chain)
    elif chain == "bitcoin":
        adapter = BitcoinAdapter()
    else:
        adapter = DemoAdapter(chain)

    _adapters[key] = adapter
    return adapter
