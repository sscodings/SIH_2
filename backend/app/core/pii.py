import os
import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger("chainnetra.core.pii")

def _get_fernet_key() -> bytes:
    key_str = getattr(settings, "PII_ENCRYPTION_KEY", None)
    if key_str and len(key_str.strip()) >= 32:
        # Base64 urlsafe encoded 32-byte key
        try:
            return base64.urlsafe_b64encode(key_str.strip().encode("utf-8")[:32])
        except Exception:
            pass
    # Derive deterministic key from SECRET_KEY
    secret = (getattr(settings, "SECRET_KEY", "") or "default-chainnetra-secret-salt-key-32").encode("utf-8")
    derived = hashlib.sha256(secret).digest()
    return base64.urlsafe_b64encode(derived)

_FERNET = Fernet(_get_fernet_key())

def encrypt_pii(text: Optional[str]) -> Optional[str]:
    """Encrypts victim reference / contact information at rest."""
    if not text:
        return None
    try:
        return _FERNET.encrypt(text.strip().encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"PII encryption failed: {e}")
        return text

def decrypt_pii(ciphertext: Optional[str], role: str) -> Optional[str]:
    """Decrypts victim reference ONLY for supervisor or admin roles; otherwise returns masked."""
    if not ciphertext:
        return None
    r = (role or "").lower().strip()
    if r not in ("supervisor", "admin"):
        # For investigators and external consumers, return masked placeholder
        return "REDACTED"
    try:
        return _FERNET.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception:
        # If not encrypted (legacy plain text), return as is for supervisor/admin
        return ciphertext
