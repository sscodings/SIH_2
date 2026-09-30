import os
import secrets
import logging
from typing import Optional, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("chainnetra.config")

DEMO_KNOWN_SECRETS = {
    "chainnetra-forensic-secret-key-32bytes-hex-demo",
    "netra-super-secret-jwt-forensic-key-2026-sih-prototype",
    "change-me",
    "secret",
    "admin",
    "password"
}

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChainNetra"
    API_V1_STR: str = "/api/v1"
    
    # Operating Mode: "DEMO" or "LIVE"
    CHAINNETRA_MODE: str = "DEMO"
    
    # Security Secrets
    SECRET_KEY: Optional[str] = None
    WEBHOOK_SECRET: Optional[str] = None
    AUDIT_HMAC_KEY: Optional[str] = None
    
    # JWT & Session Lifecycles
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite:///./chainnetra.db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # Currency rates
    USD_INR: float = 83.50
    
    # Blockchain Providers & Oracles
    TRONGRID_API_KEY: Optional[str] = ""
    ETHERSCAN_API_KEY: Optional[str] = ""
    BLOCKSTREAM_API_URL: str = "https://blockstream.info/api"
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    ADAPTER_MAX_PAGES: int = 5
    ADAPTER_TIMEOUT: float = 10.0
    
    # Audit Checkpoint Interval (Entries)
    AUDIT_CHECKPOINT_INTERVAL: int = 50
    
    # Tracing defaults
    DEFAULT_MAX_DEPTH: int = 6
    DEFAULT_MIN_VALUE_USD: float = 50.0
    DEFAULT_MAX_NODES: int = 400
    DEFAULT_TIME_WINDOW_HOURS: int = 72
    DEFAULT_TAINT_MODEL: str = "haircut"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    def validate_and_finalize_security(self):
        mode = (self.CHAINNETRA_MODE or "DEMO").upper()
        
        if mode == "LIVE":
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("LIVE MODE ERROR: SECRET_KEY must be configured and at least 32 characters long.")
            if self.SECRET_KEY in DEMO_KNOWN_SECRETS:
                raise ValueError("LIVE MODE ERROR: SECRET_KEY cannot match known default or demo secrets.")
            if not self.WEBHOOK_SECRET or len(self.WEBHOOK_SECRET) < 16:
                raise ValueError("LIVE MODE ERROR: WEBHOOK_SECRET must be configured with at least 16 characters.")
            if not self.AUDIT_HMAC_KEY or len(self.AUDIT_HMAC_KEY) < 16:
                raise ValueError("LIVE MODE ERROR: AUDIT_HMAC_KEY must be configured with at least 16 characters.")
        else:
            # DEMO mode initialization with random generated ephemeral fallback
            if not self.SECRET_KEY:
                self.SECRET_KEY = secrets.token_hex(32)
                logger.warning("DEMO MODE NOTICE: Generated random ephemeral SECRET_KEY for session.")
            if not self.WEBHOOK_SECRET:
                self.WEBHOOK_SECRET = secrets.token_hex(16)
            if not self.AUDIT_HMAC_KEY:
                self.AUDIT_HMAC_KEY = secrets.token_hex(32)

settings = Settings()
settings.validate_and_finalize_security()
