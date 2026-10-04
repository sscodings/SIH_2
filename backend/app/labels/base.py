from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from abc import ABC, abstractmethod
from app.core.time import utcnow

@dataclass
class LabelRecord:
    chain: str
    address: str
    entity: str
    category: str
    source: str
    source_url: Optional[str] = None
    license: Optional[str] = None
    weight_tier: str = "unverified_official"
    wallet_type: str = "unknown"
    raw_wallet_type: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    superseded_by: Optional[str] = None
    record_status: str = "active"  # active, pending, revoked, inactive
    snapshot_date: Optional[str] = None
    verified_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = field(default_factory=utcnow)

class LabelSource(ABC):
    name: str = "base"
    source_url: str = ""
    license: str = ""
    weight_tier: str = "unverified_official"

    @abstractmethod
    def fetch(self) -> List[LabelRecord]:
        """Fetch labels from source."""
        ...
