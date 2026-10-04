import os
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime

from app.labels.base import LabelSource, LabelRecord
from app.core.addresses import validate_address
from app.core.time import utcnow

logger = logging.getLogger("chainnetra.labels.ofac")

# The 7 verified FeatureType IDs from ofac_sample.xml
VERIFIED_FEATURE_TYPES = {
    "344": "XBT",
    "345": "ETH",
    "444": "XMR",
    "686": "ZEC",
    "687": "DASH",
    "887": "USDT",
    "992": "TRX"
}

UNTRACEABLE_TICKERS = {"XMR", "DASH", "ZEC"}

class OfacLabelSource(LabelSource):
    name: str = "OFAC SDN"
    source_url: str = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADVANCED_XML"
    license: str = "US Department of the Treasury (Public Domain)"
    weight_tier: str = "verified_authority"

    def __init__(self, xml_path: Optional[str] = None):
        self.xml_path = xml_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "tests", "fixtures", "ofac_sample.xml"
        )
        if not os.path.exists(self.xml_path):
            alt_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "docs", "research", "ofac_sample.xml"
            )
            if os.path.exists(alt_path):
                self.xml_path = alt_path

    def _infer_chain(self, address: str, ticker: str) -> str:
        # Untraceable currencies: chain "unsupported:<ticker>"
        if ticker in UNTRACEABLE_TICKERS:
            return f"unsupported:{ticker.lower()}"

        # Infer chain from address format
        val = validate_address(address)
        if val["valid"]:
            family = val["family"]
            if family == "tron":
                return "tron"
            elif family == "evm":
                return "evm"
            elif family == "bitcoin":
                return "bitcoin"

        # If currency is known untraceable or unrecognized address format
        if ticker in UNTRACEABLE_TICKERS:
            return f"unsupported:{ticker.lower()}"

        return f"unsupported:{ticker.lower()}"

    def fetch(self) -> List[LabelRecord]:
        if not os.path.exists(self.xml_path):
            logger.warning(f"OFAC XML file not found at {self.xml_path}")
            return []

        tree = ET.parse(self.xml_path)
        root = tree.getroot()

        # Build FeatureType mapping dynamically from ReferenceValueSets/FeatureTypeValues if present
        # Fall back to the 7 verified FeatureType IDs
        ftypes: Dict[str, str] = dict(VERIFIED_FEATURE_TYPES)
        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            if tag == "FeatureType":
                fid = elem.get("ID")
                txt = elem.text or ""
                if "Digital Currency Address" in txt and fid:
                    ticker = txt.split(" - ")[-1].strip()
                    ftypes[fid] = ticker

        # Extract publish date if present in root/header
        publish_date = "2026-09-29"
        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            if tag in ("PublishDate", "DateOfPublication", "PublicationDate") and elem.text:
                publish_date = elem.text.strip()
                break

        records: List[LabelRecord] = []
        seen_keys = set()

        for party in root.iter():
            tag = party.tag.split("}")[-1]
            if tag != "DistinctParty":
                continue

            fixed_ref = party.get("FixedRef", "")

            # Get entity name
            name = ""
            for elem in party.iter():
                subtag = elem.tag.split("}")[-1]
                if subtag == "NamePartValue" and elem.text:
                    name = elem.text.strip()
                    break
            if not name:
                name = f"Sanctioned Entity #{fixed_ref}"

            for feat in party.iter():
                ftag = feat.tag.split("}")[-1]
                if ftag != "Feature":
                    continue

                fid = feat.get("FeatureTypeID", "")
                if fid not in ftypes:
                    continue

                ticker = ftypes[fid]

                for v in feat.iter():
                    vtag = v.tag.split("}")[-1]
                    if vtag != "VersionDetail":
                        continue

                    addr = (v.text or "").strip()
                    if not addr:
                        continue

                    chain = self._infer_chain(addr, ticker)
                    norm_addr = addr.lower() if chain == "evm" else addr

                    dedup_key = (chain, norm_addr, name)
                    if dedup_key in seen_keys:
                        continue
                    seen_keys.add(dedup_key)

                    records.append(LabelRecord(
                        chain=chain,
                        address=norm_addr,
                        entity=name,
                        category="sanctioned",
                        source=self.name,
                        source_url=self.source_url,
                        license=self.license,
                        weight_tier=self.weight_tier,
                        wallet_type="unknown",
                        raw_wallet_type=f"OFAC Feature {fid} ({ticker}) FixedRef {fixed_ref}",
                        valid_from=None,
                        valid_to=None,
                        superseded_by=None,
                        record_status="active",
                        snapshot_date=publish_date,
                        verified_at=utcnow(),
                        fetched_at=utcnow()
                    ))

        logger.info(f"Loaded {len(records)} OFAC sanctioned address labels")
        return records
