import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChainNetra"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "chainnetra-forensic-secret-key-32bytes-hex-demo"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite:///./chainnetra.db"
    
    # Operating Mode: "DEMO" or "LIVE"
    CHAINNETRA_MODE: str = "DEMO"
    
    # Currency rates
    USD_INR: float = 83.50
    
    # API Keys for Live Mode (Optional)
    TRONGRID_API_KEY: Optional[str] = ""
    ETHERSCAN_API_KEY: Optional[str] = ""
    
    # Webhook HMAC Secret
    WEBHOOK_SECRET: str = "netra-webhook-hmac-secret-key"
    
    # Tracing defaults
    DEFAULT_MAX_DEPTH: int = 6
    DEFAULT_MIN_VALUE_USD: float = 50.0
    DEFAULT_MAX_NODES: int = 400
    DEFAULT_TIME_WINDOW_HOURS: int = 72
    DEFAULT_TAINT_MODEL: str = "haircut"  # haircut, fifo, poison

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
