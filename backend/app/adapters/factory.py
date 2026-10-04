from typing import Dict, Optional
from app.adapters.base import ChainAdapter, AdapterError
from app.adapters.demo import DemoAdapter
from app.adapters.tron import TronAdapter
from app.adapters.evm import EvmAdapter
from app.adapters.bitcoin import BitcoinAdapter
from app.core.config import settings

_adapters: Dict[str, ChainAdapter] = {}
_custom_registry: Dict[str, ChainAdapter] = {}

def register_adapter(chain: str, adapter: ChainAdapter):
    """Allows test fixtures to inject mock/fake adapters."""
    _custom_registry[chain.lower()] = adapter

def clear_custom_adapters():
    """Clears any custom test injected adapters."""
    _custom_registry.clear()
    _adapters.clear()

def get_chain_adapter(chain: str) -> ChainAdapter:
    chain = chain.lower()
    
    # 1. Custom injected test adapter takes precedence
    if chain in _custom_registry:
        return _custom_registry[chain]

    mode = settings.CHAINNETRA_MODE.upper()

    if mode == "DEMO":
        if chain not in _adapters:
            _adapters[chain] = DemoAdapter(chain)
        return _adapters[chain]

    # In LIVE mode, instantiate and cache live adapters (never fallback to DemoAdapter)
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
        raise AdapterError(f"No live blockchain adapter available for chain: '{chain}' in {mode} mode")

    _adapters[key] = adapter
    return adapter
