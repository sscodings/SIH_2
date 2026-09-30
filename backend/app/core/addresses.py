import re
from typing import Optional

EVM_CHAINS = {"ethereum", "eth", "bsc", "binance", "polygon", "matic", "arbitrum", "arb"}

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
            # Theta
            C = [state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4] for x in range(5)]
            D = [C[(x - 1) % 5] ^ rotl(C[(x + 1) % 5], 1) for x in range(5)]
            for x in range(5):
                for y in range(5):
                    state[x][y] ^= D[x]
            # Rho and Pi
            B = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    B[y][(2 * x + 3 * y) % 5] = rotl(state[x][y], r[x][y])
            # Chi
            for x in range(5):
                for y in range(5):
                    state[x][y] = B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) & 0xFFFFFFFFFFFFFFFF
            # Iota
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
    Normalizes an address according to its blockchain network rules:
    - EVM (Ethereum, BSC, Polygon, Arbitrum): lowercased for storage / DB lookup / node keys
    - Tron & Bitcoin: Exact case preserved (Tron Base58 and BTC Base58/Bech32 are case-sensitive)
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
    Returns the canonical display format:
    - EVM: EIP-55 checksummed (e.g. 0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed)
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
    """
    Composite graph node key: f"{chain}:{normalized}"
    Prevents cross-chain EVM address collisions while respecting chain case sensitivity.
    """
    c = (chain or "unknown").lower().strip()
    norm = normalize(c, address)
    return f"{c}:{norm}"
