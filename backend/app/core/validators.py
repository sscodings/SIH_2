import re
import hashlib
from typing import Tuple, Optional
from app.core.config import settings

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE58_MAP = {c: i for i, c in enumerate(BASE58_ALPHABET)}

def decode_base58(s: str) -> Optional[bytes]:
    if not s or not isinstance(s, str):
        return None
    num = 0
    for char in s:
        if char not in BASE58_MAP:
            return None
        num = num * 58 + BASE58_MAP[char]
    
    res = []
    while num > 0:
        res.append(num & 0xFF)
        num >>= 8
    res.reverse()
    
    pad = 0
    for char in s:
        if char == BASE58_ALPHABET[0]:
            pad += 1
        else:
            break
    return (b"\x00" * pad) + bytes(res)

def verify_base58check(s: str, expected_prefix: Optional[bytes] = None) -> bool:
    raw = decode_base58(s)
    if not raw or len(raw) < 5:
        return False
    payload = raw[:-4]
    checksum = raw[-4:]
    expected_checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected_checksum:
        return False
    if expected_prefix is not None:
        if not payload.startswith(expected_prefix):
            return False
    return True

BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def bech32_polymod(values):
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk

def bech32_hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def verify_bech32(s: str) -> bool:
    if not isinstance(s, str) or len(s) < 14 or len(s) > 90:
        return False
    if not (s.islower() or s.isupper()):
        return False
    s_lower = s.lower()
    pos = s_lower.rfind('1')
    if pos < 1 or pos + 7 > len(s_lower):
        return False
    hrp = s_lower[:pos]
    data = s_lower[pos + 1:]
    if hrp != "bc":
        return False
    data_values = []
    for c in data:
        if c not in BECH32_CHARSET:
            return False
        data_values.append(BECH32_CHARSET.find(c))
    
    polymod = bech32_polymod(bech32_hrp_expand(hrp) + data_values)
    return polymod in (1, 0x2bc830a3)

def verify_evm_address(address: str) -> bool:
    if not isinstance(address, str):
        return False
    if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
        return False
    return True

def verify_tron_address(address: str) -> bool:
    if not isinstance(address, str) or not address.startswith("T"):
        return False
    if len(address) == 34:
        if verify_base58check(address, expected_prefix=b"\x41"):
            return True
        if re.match(r"^T[1-9A-HJ-NP-Za-km-z]{33}$", address):
            return True
    return False

def verify_bitcoin_address(address: str) -> bool:
    if not isinstance(address, str):
        return False
    if address.startswith("bc1"):
        if verify_bech32(address):
            return True
        if re.match(r"^bc1[a-z0-9]{11,70}$", address):
            return True
    elif address.startswith("1") or address.startswith("3"):
        if verify_base58check(address):
            return True
        if re.match(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$", address):
            return True
    return False

def validate_crypto_address(address: str, chain: str) -> bool:
    if not address or not isinstance(address, str):
        return False
    addr = address.strip()
    chain_norm = (chain or "").lower().strip()
    
    if chain_norm in ("tron", "trx"):
        return verify_tron_address(addr)
    elif chain_norm in ("ethereum", "eth", "bsc", "arbitrum", "polygon", "evm"):
        return verify_evm_address(addr)
    elif chain_norm in ("bitcoin", "btc"):
        return verify_bitcoin_address(addr)
    else:
        return verify_evm_address(addr) or verify_tron_address(addr) or verify_bitcoin_address(addr)
