import os
import logging
from typing import Optional, List
from cryptography.fernet import Fernet, MultiFernet
from sqlalchemy.types import TypeDecorator, String, Text
from app.core.config import settings

logger = logging.getLogger("chainnetra.crypto")

_DEFAULT_DEV_KEY = Fernet.generate_key().decode()
_multi_fernet: Optional[MultiFernet] = None

def get_multi_fernet() -> MultiFernet:
    global _multi_fernet
    if _multi_fernet is not None:
        return _multi_fernet

    keys_str = os.getenv("PII_FERNET_KEYS", "").strip()
    is_live = getattr(settings, "CHAINNETRA_MODE", "").upper() == "LIVE"

    if not keys_str:
        if is_live:
            raise RuntimeError("FATAL: PII_FERNET_KEYS environment variable is mandatory in LIVE mode.")
        logger.warning("PII_FERNET_KEYS not set. Using ephemeral in-memory key for local dev/testing.")
        keys_str = _DEFAULT_DEV_KEY

    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    if not keys:
        if is_live:
            raise RuntimeError("FATAL: No valid encryption keys found in PII_FERNET_KEYS.")
        keys = [_DEFAULT_DEV_KEY]

    fernets = [Fernet(k.encode() if isinstance(k, str) else k) for k in keys]
    _multi_fernet = MultiFernet(fernets)
    return _multi_fernet

def set_custom_fernet_keys(keys_list: List[str]):
    global _multi_fernet
    fernets = [Fernet(k.encode() if isinstance(k, str) else k) for k in keys_list]
    _multi_fernet = MultiFernet(fernets)

def encrypt_pii(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return value
    mf = get_multi_fernet()
    # Check if already encrypted (starts with gAAAAA)
    if isinstance(value, str) and value.startswith("gAAAAA") and len(value) > 50:
        return value
    return mf.encrypt(value.encode("utf-8")).decode("utf-8")

def decrypt_pii(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return value
    # If not encrypted, return as is (graceful backwards compatibility)
    if not (isinstance(value, str) and value.startswith("gAAAAA")):
        return value
    try:
        mf = get_multi_fernet()
        return mf.decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decrypt PII ciphertext: {e}")
        return "[ENCRYPTED_PII_DECRYPT_ERROR]"

class EncryptedString(TypeDecorator):
    """SQLAlchemy type decorator that transparently encrypts strings at rest using MultiFernet."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_pii(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_pii(str(value))

class EncryptedText(TypeDecorator):
    """SQLAlchemy type decorator that transparently encrypts long text at rest using MultiFernet."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_pii(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_pii(str(value))
