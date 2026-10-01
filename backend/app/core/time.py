from datetime import datetime, timezone

def utcnow() -> datetime:
    """Returns current timezone-aware UTC datetime (replaces deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)
