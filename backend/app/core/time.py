from datetime import datetime, timezone
from typing import Optional

def utcnow() -> datetime:
    """Returns current timezone-aware UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalizes naive datetimes (e.g. from SQLite) to UTC timezone-aware datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
