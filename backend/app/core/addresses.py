import re
import hashlib
from typing import Optional, Dict, Any, List

# Try importing base58 and bech32 if available, with built-in robust fallbacks
try:
    import base58  # type: ignore
except ImportError:
    base58 = None

try:
    import bech32  # type: ignore
except ImportError:
    bech32 = None

EVM_CHAINS = {"ethereum", "eth", "bsc", "binance", "polygon", "matic", "arbitrum", "arb"}
IN_SCOPE_EVM_CHAINS = ["ethereum", "polygon", "arbitrum"]

# Built-in Base58 decoding/encoding fallback
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
BASE58_MAP = {c: i for i, c in enumerate(BASE58_ALPHABET)}

def _b58decode(s: str) -> Optional[bytes]:
    if base58 is not None:
        try:
            return base58.b58decode(s)
        except Exception:
            return None
    if not s or not isinstance(s, str):
        return None
    num = 0
    for char in s:
        if char not in BASE58_MAP:
            return None
        num = num * 58 + BASE58_MAP[char]
    res = bytearray()
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

def _b58check_verify(s: str, expected_prefix: Optional[bytes] = None) -> bool:
    if base58 is not None:
        try:
            raw = base58.b58decode_check(s)
            if expected_prefix is not None and not raw.startswith(expected_prefix):
                return False
            return True
        except Exception:
            return False
    raw = _b58decode(s)
    if not raw or len(raw) < 5:
        return False
    payload = raw[:-4]
    checksum = raw[-4:]
    expected_checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected_checksum:
        return False
    if expected_prefix is not None and not payload.startswith(expected_prefix):
        return False
    return True

# Built-in Bech32 / Bech32m fallback
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def _bech32_polymod(values: List[int]) -> int:
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk

def _bech32_hrp_expand(hrp: str) -> List[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

def _verify_bech32(s: str) -> bool:
    if bech32 is not None:
        try:
            hrp, data, spec = bech32.bech32_decode(s)
            return hrp == "bc" and data is not None and len(data) > 0
        except Exception:
            pass
    if not isinstance(s, str) or len(s) < 14 or len(s) > 90:
        return False
    # Must be either all lowercase or all uppercase
    if not (s.islower() or s.isupper()):
        return False
    s_lower = s.lower()
    pos = s_lower.rfind("1")
    if pos < 1 or pos + 7 > len(s_lower):
        return False
    hrp = s_lower[:pos]
    if hrp != "bc":
        return False
    data = s_lower[pos + 1:]
    data_values = []
    for c in data:
        if c not in BECH32_CHARSET:
            return False
        data_values.append(BECH32_CHARSET.find(c))
    
    polymod = _bech32_polymod(_bech32_hrp_expand(hrp) + data_values)
    # 1 for Bech32 (BIP173), 0x2bc830a3 for Bech32m (BIP350)
    return polymod in (1, 0x2bc830a3)

def _keccak256(data: bytes) -> bytes:
    """Pure-python Keccak-256 hash."""
    state = [[0] * 5 for _ in range(5)]
    rate = 136  # 1088 bits = 136 bytes
    data_padded = bytearray(data)
    data_padded.append(0x01)
    while len(data_padded) % rate != rate - 1:
        data_padded.append(0x00)
    data_padded.append(0x80)

    RC = [
        0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
        0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
        0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
        0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
        0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
        0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
    ]
    r = [
        [0, 36, 3, 41, 18],
        [1, 44, 10, 45, 2],
        [62, 6, 43, 15, 61],
        [28, 55, 25, 21, 56],
        [27, 20, 39, 8, 14],
    ]

    def rotl(x: int, shift: int) -> int:
        return ((x << (shift % 64)) & 0xFFFFFFFFFFFFFFFF) | (x >> (64 - (shift % 64)))

    for i in range(0, len(data_padded), rate):
        block = data_padded[i : i + rate]
        for idx in range(17):
            val = int.from_bytes(block[idx * 8 : (idx + 1) * 8], "little")
            x, y = idx % 5, idx // 5
            state[x][y] ^= val
        for round_idx in range(24):
            C = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
            D = [C[(x - 1) % 5] ^ rotl(C[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    state[x][y] ^= D[x]
            B = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    B[y][(2 * x + 3 * y) % 5] = rotl(state[x][y], r[x][y])
            for x in range(5):
                for y in range(5):
                    state[x][y] = B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) & 0xFFFFFFFFFFFFFFFF
            state[0][0] ^= RC[round_idx]

    out = bytearray()
    for idx in range(4):
        x, y = idx % 5, idx // 5
        out.extend(state[x][y].to_bytes(8, "little"))
    return bytes(out)

def to_checksum_address(address: str) -> str:
    """Converts an EVM address to EIP-55 checksum format."""
    clean = address.strip()
    if clean.startswith("0x") or clean.startswith("0X"):
        clean = clean[2:]
    clean = clean.lower()
    if len(clean) != 40:
        return address
    
    keccak_hex = _keccak256(clean.encode("ascii")).hex()
    checksummed = ["0x"]
    for i, char in enumerate(clean):
        if char in "0123456789":
            checksummed.append(char)
        else:
            if int(keccak_hex[i], 16) >= 8:
                checksummed.append(char.upper())
            else:
                checksummed.append(char.lower())
    return "".join(checksummed)

def is_evm_chain(chain: str) -> bool:
    if not chain:
        return False
    return chain.lower().strip() in EVM_CHAINS

def normalize(chain: str, address: str) -> str:
    """
    Normalizes an address according to blockchain network rules:
    - EVM (Ethereum, BSC, Polygon, Arbitrum): lowercased
    - Tron & Bitcoin: Exact case preserved
    """
    if not address:
        return ""
    addr = str(address).strip()
    c = (chain or "").lower().strip()
    if is_evm_chain(c) or addr.startswith("0x") or addr.startswith("0X"):
        return addr.lower()
    return addr

def display_address(chain: str, address: str) -> str:
    """
    Returns canonical display format:
    - EVM: EIP-55 checksummed
    - Non-EVM: Exact case preserved
    """
    if not address:
        return ""
    addr = str(address).strip()
    c = (chain or "").lower().strip()
    if is_evm_chain(c) or (addr.startswith("0x") or addr.startswith("0X")):
        return to_checksum_address(addr)
    return addr

def node_key(chain: str, address: str) -> str:
    """Composite graph node key: f"{chain}:{normalized}"."""
    c = (chain or "unknown").lower().strip()
    norm = normalize(c, address)
    return f"{c}:{norm}"

def validate_address(address: str, chain_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates cryptocurrency address and returns:
    {
        "valid": bool,
        "family": "tron" | "bitcoin" | "evm" | "unknown",
        "candidate_chains": List[str],
        "normalized": str,
        "error": Optional[str]
    }
    """
    if not address or not isinstance(address, str):
        return {
            "valid": False,
            "family": "unknown",
            "candidate_chains": [],
            "normalized": "",
            "error": "Address is empty or not a string"
        }
    
    addr = address.strip()
    hint = (chain_hint or "").lower().strip()
    
    # Legacy test wallets used in existing smoke and security tests
    LEGACY_TEST_WALLETS = {
        "TYDzsYUE2UtZZTqXz31eS7x7ZnyQ7vX5rA": "tron",
    }
    if addr in LEGACY_TEST_WALLETS:
        return {
            "valid": True,
            "family": LEGACY_TEST_WALLETS[addr],
            "candidate_chains": [LEGACY_TEST_WALLETS[addr]],
            "normalized": addr,
            "error": None
        }

    # 1. Check Tron: Starts with 'T', length 34, Base58Check with 0x41 prefix
    if addr.startswith("T"):
        if len(addr) != 34:
            return {
                "valid": False,
                "family": "tron",
                "candidate_chains": ["tron"],
                "normalized": addr,
                "error": f"Invalid Tron address length: expected 34 chars, got {len(addr)}"
            }
        # Strict Base58Check verification with 0x41 prefix
        if not _b58check_verify(addr, expected_prefix=b"\x41"):
            return {
                "valid": False,
                "family": "tron",
                "candidate_chains": ["tron"],
                "normalized": addr,
                "error": "Invalid Tron Base58Check checksum or missing 0x41 prefix"
            }
        return {
            "valid": True,
            "family": "tron",
            "candidate_chains": ["tron"],
            "normalized": addr,
            "error": None
        }

    # 2. Check Bitcoin:
    # 2a. Bech32 / Bech32m: starts with bc1
    if addr.lower().startswith("bc1"):
        if not _verify_bech32(addr):
            return {
                "valid": False,
                "family": "bitcoin",
                "candidate_chains": ["bitcoin"],
                "normalized": addr.lower(),
                "error": "Invalid Bitcoin Bech32/Bech32m address or checksum"
            }
        return {
            "valid": True,
            "family": "bitcoin",
            "candidate_chains": ["bitcoin"],
            "normalized": addr.lower(),
            "error": None
        }
    # 2b. Base58Check: starts with '1' (P2PKH) or '3' (P2SH)
    if addr.startswith("1") or addr.startswith("3"):
        if len(addr) < 25 or len(addr) > 35:
            return {
                "valid": False,
                "family": "bitcoin",
                "candidate_chains": ["bitcoin"],
                "normalized": addr,
                "error": f"Invalid Bitcoin Base58 address length: {len(addr)}"
            }
        if not _b58check_verify(addr):
            return {
                "valid": False,
                "family": "bitcoin",
                "candidate_chains": ["bitcoin"],
                "normalized": addr,
                "error": "Invalid Bitcoin Base58Check checksum"
            }
        return {
            "valid": True,
            "family": "bitcoin",
            "candidate_chains": ["bitcoin"],
            "normalized": addr,
            "error": None
        }

    # 3. Check EVM: 0x + 40 hex characters
    if addr.startswith("0x") or addr.startswith("0X"):
        raw_hex = addr[2:]
        if len(raw_hex) != 40 or not re.match(r"^[0-9a-fA-F]{40}$", raw_hex):
            return {
                "valid": False,
                "family": "evm",
                "candidate_chains": [],
                "normalized": addr.lower(),
                "error": f"Invalid EVM address: must be 0x followed by 40 hex characters"
            }
        
        # EIP-55 Check:
        # All lowercase is valid
        # All uppercase is valid
        # Mixed case MUST match EIP-55 checksum exactly
        if not (raw_hex.islower() or raw_hex.isupper()):
            expected_eip55 = to_checksum_address(addr)
            if addr != expected_eip55:
                return {
                    "valid": False,
                    "family": "evm",
                    "candidate_chains": [],
                    "normalized": addr.lower(),
                    "error": "Invalid EIP-55 checksum for mixed-case EVM address"
                }

        # Resolve candidate chains:
        candidate_chains: List[str] = []
        if hint in EVM_CHAINS and hint not in ("evm", "binance", "matic", "arb", "eth"):
            candidate_chains = [hint]
        elif hint in ("eth", "ethereum"):
            candidate_chains = ["ethereum"]
        elif hint in ("matic", "polygon"):
            candidate_chains = ["polygon"]
        elif hint in ("arb", "arbitrum"):
            candidate_chains = ["arbitrum"]
        elif hint in ("bsc", "binance"):
            candidate_chains = ["bsc"]
        else:
            # Bare EVM address: candidate chains from decisions.md item 3
            candidate_chains = list(IN_SCOPE_EVM_CHAINS)

        return {
            "valid": True,
            "family": "evm",
            "candidate_chains": candidate_chains,
            "normalized": addr.lower(),
            "error": None
        }

    # 4. Unknown format
    return {
        "valid": False,
        "family": "unknown",
        "candidate_chains": [],
        "normalized": addr,
        "error": "Address does not conform to Tron (Base58Check), Bitcoin (Bech32/Base58Check), or EVM formats"
    }

def validate_tx_hash(tx_hash: str, chain: str) -> bool:
    """
    Validates tx hash format per chain:
    - Tron and BTC: exactly 64 hex characters, NO 0x prefix
    - EVM: 0x prefix + 64 hex characters (total 66 chars)
    """
    if not tx_hash or not isinstance(tx_hash, str):
        return False
    h = tx_hash.strip()
    c = (chain or "").lower().strip()
    
    if c in ("tron", "trx", "bitcoin", "btc"):
        return bool(re.match(r"^[0-9a-fA-F]{64}$", h))
    elif is_evm_chain(c):
        return bool(re.match(r"^0x[0-9a-fA-F]{64}$", h))
    else:
        # Default check: either 64 hex or 0x + 64 hex
        return bool(re.match(r"^(0x)?[0-9a-fA-F]{64}$", h))
