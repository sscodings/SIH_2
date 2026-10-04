import os
import csv
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.labels.base import LabelSource, LabelRecord
from app.core.addresses import normalize, validate_address
from app.core.time import utcnow

logger = logging.getLogger("chainnetra.labels.exchange_csv")

CHAIN_MAP = {
    "ETH": "ethereum",
    "ETHEREUM": "ethereum",
    "BSC": "bsc",
    "BINANCE": "bsc",
    "TRX": "tron",
    "TRON": "tron",
    "BTC": "bitcoin",
    "BITCOIN": "bitcoin"
}

class ExchangeCsvLabelSource(LabelSource):
    name: str = "Exchange CSV"
    source_url: str = "Official exchange reserve declarations"
    license: str = "Public Exchange Disclosures"
    weight_tier: str = "unverified_official"

    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = csv_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "tests", "fixtures", "exchange_addresses.csv"
        )
        if not os.path.exists(self.csv_path):
            alt_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "docs", "research", "exchange_addresses.csv"
            )
            if os.path.exists(alt_path):
                self.csv_path = alt_path

    @staticmethod
    def normalize_wallet_type(raw_type: str) -> str:
        if not raw_type:
            return "unknown"
        t = raw_type.lower().strip()
        if t == "hot":
            return "hot"
        if t in ("cold", "cold_storage"):
            return "cold"
        if t == "deposit":
            return "deposit"
        return "unknown"

    @staticmethod
    def get_recommendation_guidance(wallet_type: str) -> str:
        wt = (wallet_type or "unknown").lower().strip()
        if wt in ("hot", "deposit"):
            return "Freeze notice recommended immediately (deposit or hot wallet reached)."
        elif wt == "cold":
            return "funds moved past the exchange's deposit layer; contact the exchange"
        else:
            return "exchange-controlled wallet reached; confirm wallet type with the exchange, then request freeze"

    @staticmethod
    def parse_optional_date(val: Optional[str]) -> Optional[datetime]:
        if not val or not val.strip():
            return None
        s = val.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None

    def fetch(self) -> List[LabelRecord]:
        if not os.path.exists(self.csv_path):
            logger.error(f"Exchange CSV file not found at {self.csv_path}")
            return []

        records: List[LabelRecord] = []
        with open(self.csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_chain = row.get("chain", "").strip()
                if raw_chain not in CHAIN_MAP:
                    logger.warning(f"Rejecting unknown chain '{raw_chain}' in row {row}")
                    continue

                canonical_chain = CHAIN_MAP[raw_chain]
                raw_addr = row.get("address", "").strip()
                norm_addr = normalize(canonical_chain, raw_addr)

                entity = row.get("entity", "").strip()
                source_url = row.get("source_url", "").strip()
                verified_date_str = row.get("verified_date", "").strip()
                snapshot_date_str = row.get("snapshot_date", "").strip()
                raw_wallet_type = row.get("wallet_type", "").strip()
                verification_status = row.get("verification_status", "").strip()

                # Read optional columns directly
                valid_from_str = row.get("valid_from", "").strip()
                valid_to_str = row.get("valid_to", "").strip()
                record_status = row.get("record_status", "").strip() or "active"
                superseded_by = row.get("superseded_by", "").strip() or None

                norm_wallet_type = self.normalize_wallet_type(raw_wallet_type)

                # Weight tier: official_source_only -> unverified_official
                weight_tier = "unverified_official"
                if verification_status and not verification_status.startswith("official_source_only"):
                    weight_tier = "exchange_self_disclosure"

                # Parse dates
                valid_from = self.parse_optional_date(valid_from_str)
                valid_to = self.parse_optional_date(valid_to_str)
                verified_at = self.parse_optional_date(verified_date_str)

                # Unocoin ETH address: strictly labeled ONLY on ethereum
                if entity.lower() == "unocoin" and canonical_chain != "ethereum" and raw_addr.startswith("0x"):
                    canonical_chain = "ethereum"

                record = LabelRecord(
                    chain=canonical_chain,
                    address=norm_addr,
                    entity=entity,
                    category="VASP",
                    source=self.name,
                    source_url=source_url,
                    license=self.license,
                    weight_tier=weight_tier,
                    wallet_type=norm_wallet_type,
                    raw_wallet_type=raw_wallet_type,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    superseded_by=superseded_by,
                    record_status=record_status,
                    snapshot_date=snapshot_date_str,
                    verified_at=verified_at,
                    fetched_at=utcnow()
                )
                records.append(record)

        logger.info(f"Loaded {len(records)} exchange address labels from CSV")
        return records
