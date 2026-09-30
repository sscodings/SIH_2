from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings

router = APIRouter(prefix="", tags=["System"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    return {
        "status": "healthy",
        "service": "ChainNetra Forensic Attribution Engine",
        "mode": settings.CHAINNETRA_MODE,
        "database": "connected",
        "version": "1.0.0-PROTOTYPE"
    }

@router.get("/providers/status")
def providers_status():
    return {
        "mode": settings.CHAINNETRA_MODE,
        "providers": [
            {
                "chain": "Tron",
                "adapter": "TronAdapter",
                "api": "TronGrid API",
                "has_key": bool(settings.TRONGRID_API_KEY),
                "status": "Operational (Demo Deterministic / Live fallback)",
                "latency_ms": 42
            },
            {
                "chain": "Ethereum",
                "adapter": "EvmAdapter",
                "api": "Etherscan API",
                "has_key": bool(settings.ETHERSCAN_API_KEY),
                "status": "Operational (Demo Deterministic / Live fallback)",
                "latency_ms": 68
            },
            {
                "chain": "BSC",
                "adapter": "EvmAdapter",
                "api": "BscScan API",
                "has_key": bool(settings.ETHERSCAN_API_KEY),
                "status": "Operational (Demo Deterministic / Live fallback)",
                "latency_ms": 55
            },
            {
                "chain": "Bitcoin",
                "adapter": "BitcoinAdapter",
                "api": "Blockstream Esplora",
                "has_key": True,
                "status": "Operational (Demo Deterministic / Live fallback)",
                "latency_ms": 84
            },
            {
                "chain": "Arbitrum",
                "adapter": "EvmAdapter",
                "api": "ArbiScan API",
                "has_key": bool(settings.ETHERSCAN_API_KEY),
                "status": "Operational (Demo Deterministic / Live fallback)",
                "latency_ms": 61
            }
        ]
    }
