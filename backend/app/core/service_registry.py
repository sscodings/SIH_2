from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.core.addresses import normalize, is_evm_chain

@dataclass
class ServiceEntry:
    chain: str
    address: str
    kind: str  # "mixer", "bridge", "dex_router", "vasp"
    name: str
    source: str
    verified_at: datetime = field(default_factory=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
    denominations: List[float] = field(default_factory=list)  # for mixers
    release_addresses: Dict[str, str] = field(default_factory=dict)  # for bridges: dest_chain -> release_address
    metadata: Dict[str, Any] = field(default_factory=dict)

class ServiceRegistry:
    """
    Curated registry for known crypto services (mixers, bridges, DEX routers, VASPs).
    Eliminates all string-matching heuristics ('mix', 'bridge') in favor of verified contract registries.
    """
    _registry: Dict[str, ServiceEntry] = {}

    @classmethod
    def register(cls, entry: ServiceEntry):
        norm_chain = entry.chain.lower().strip()
        norm_addr = normalize(norm_chain, entry.address)
        key = f"{norm_chain}:{norm_addr}"
        entry.chain = norm_chain
        entry.address = norm_addr
        cls._registry[key] = entry

    @classmethod
    def lookup(cls, chain: str, address: str) -> Optional[ServiceEntry]:
        norm_chain = (chain or "").lower().strip()
        norm_addr = normalize(norm_chain, address)
        key = f"{norm_chain}:{norm_addr}"
        return cls._registry.get(key)

    @classmethod
    def is_service(cls, chain: str, address: str) -> bool:
        return cls.lookup(chain, address) is not None

    @classmethod
    def is_mixer(cls, chain: str, address: str) -> bool:
        entry = cls.lookup(chain, address)
        return entry is not None and entry.kind == "mixer"

    @classmethod
    def is_bridge(cls, chain: str, address: str) -> bool:
        entry = cls.lookup(chain, address)
        return entry is not None and entry.kind == "bridge"

    @classmethod
    def is_dex_router(cls, chain: str, address: str) -> bool:
        entry = cls.lookup(chain, address)
        return entry is not None and entry.kind == "dex_router"

    @classmethod
    def is_vasp(cls, chain: str, address: str) -> bool:
        entry = cls.lookup(chain, address)
        return entry is not None and entry.kind == "vasp"

    @classmethod
    def clear(cls):
        cls._registry.clear()

    @classmethod
    def init_default_registry(cls):
        """Initializes curated registry of known verified services."""
        cls.clear()
        
        # 1. Mixers
        cls.register(ServiceEntry(
            chain="bitcoin",
            address="bc1qveilmixprivacytumbler00000000",
            kind="mixer",
            name="VeilMix Core Tumbler",
            source="Verified LEA Intel",
            verified_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            denominations=[0.1, 0.5, 1.0, 5.0, 10.0]
        ))
        cls.register(ServiceEntry(
            chain="ethereum",
            address="0x08b8b0e8b8b0e8b8b0e8b8b0e8b8b0e8b8b0e8b8",
            kind="mixer",
            name="Tornado Cash 100 ETH Pool",
            source="OFAC SDN List",
            verified_at=datetime(2025, 8, 1, tzinfo=timezone.utc),
            denominations=[0.1, 1.0, 10.0, 100.0]
        ))

        # 2. Bridges
        cls.register(ServiceEntry(
            chain="tron",
            address="TXSwiftBridgeTronPortal5555555555",
            kind="bridge",
            name="SwiftBridge Tron Portal",
            source="VASP Verified Registry",
            verified_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            release_addresses={
                "bsc": "0xswiftbridgebscreleasecontract333",
                "ethereum": "0xswiftbridgeethreleasecontract222",
                "arbitrum": "0xswiftbridgearbreleasecontract111"
            }
        ))
        cls.register(ServiceEntry(
            chain="ethereum",
            address="0xarbitrumbridgegatewayportal777",
            kind="bridge",
            name="Arbitrum One Bridge Gateway",
            source="Arbitrum Foundation",
            verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            release_addresses={
                "arbitrum": "0x0000000000000000000000000000000000000064"
            }
        ))

        # 3. DEX Routers
        cls.register(ServiceEntry(
            chain="ethereum",
            address="0xswaplabethrouterv344444444444444",
            kind="dex_router",
            name="SwapLab Router V3",
            source="VASP Verified Registry",
            verified_at=datetime(2026, 1, 10, tzinfo=timezone.utc)
        ))
        cls.register(ServiceEntry(
            chain="ethereum",
            address="0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
            kind="dex_router",
            name="Uniswap V2 Router",
            source="Uniswap Protocol",
            verified_at=datetime(2025, 6, 1, tzinfo=timezone.utc)
        ))

        # 4. VASPs / Hot Wallets
        cls.register(ServiceEntry(
            chain="tron",
            address="TXDemoxHotWalletPrimary88888888888",
            kind="vasp",
            name="DemoX Exchange Hot Wallet",
            source="VASP Verified Registry",
            verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        ))
        cls.register(ServiceEntry(
            chain="bsc",
            address="0xnovatradebschotwallet7777777777",
            kind="vasp",
            name="NovaTrade BSC Hot Wallet",
            source="VASP Verified Registry",
            verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        ))
        cls.register(ServiceEntry(
            chain="arbitrum",
            address="0xzenitharbitrumcoldvault666666666",
            kind="vasp",
            name="Zenith OTC Custody",
            source="Verified LEA Intel",
            verified_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        ))

# Initialize on import
ServiceRegistry.init_default_registry()
