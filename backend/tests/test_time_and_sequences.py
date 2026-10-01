import re
import ast
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures
import pytest
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.time import utcnow, ensure_utc
from app.db.database import Base
from app.db.models import (
    SystemCounter, Case, FreezeRequest, Complaint,
    get_next_sequence_number
)
from app.core.audit import (
    log_audit_action, verify_audit_chain, format_audit_timestamp,
    compute_entry_hash, GENESIS_HASH
)
from app.db.models import AuditLog


def test_utcnow_is_timezone_aware():
    """Verifies utcnow() returns timezone-aware UTC datetime."""
    now = utcnow()
    assert isinstance(now, datetime)
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_ensure_utc_helper():
    """Verifies ensure_utc normalizes naive and aware datetimes, and handles None."""
    assert ensure_utc(None) is None

    naive = datetime(2026, 5, 1, 12, 0, 0)
    aware = ensure_utc(naive)
    assert aware.tzinfo == timezone.utc
    assert aware.year == 2026 and aware.month == 5 and aware.hour == 12

    # Already aware
    already_aware = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    res = ensure_utc(already_aware)
    assert res == already_aware


def test_zero_deprecated_utcnow_in_backend_app():
    """AST / text scan verifying zero calls to datetime.utcnow() in backend/app."""
    app_dir = Path(__file__).resolve().parent.parent / "app"
    violations = []

    for py_file in app_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        # Check text pattern
        for line_no, line in enumerate(content.splitlines(), start=1):
            if "datetime.utcnow()" in line and "replaces deprecated" not in line:
                violations.append(f"{py_file.name}:{line_no}: {line.strip()}")

    assert not violations, f"Found deprecated datetime.utcnow() calls: {violations}"


def test_models_datetime_columns_have_timezone_true():
    """Verifies that DateTime columns in models specify timezone=True."""
    from sqlalchemy import DateTime
    for table_name, table in Base.metadata.tables.items():
        for col in table.columns:
            if isinstance(col.type, DateTime):
                assert col.type.timezone is True, f"Column {table_name}.{col.name} missing timezone=True"


def test_format_audit_timestamp_iso():
    """Verifies audit timestamp formats with ISO string and +00:00 UTC offset."""
    dt = datetime(2026, 10, 1, 14, 30, 0, tzinfo=timezone.utc)
    ts_str = format_audit_timestamp(dt)
    assert "+00:00" in ts_str
    assert ts_str.startswith("2026-10-01T14:30:00")


def test_audit_chain_backward_compatibility(db_session: Session):
    """Verifies that audit chains with legacy naive timestamps remain verifiable."""
    # 1. Insert a legacy entry manually with naive timestamp and legacy format hash
    legacy_ts = "2026-01-01T10:00:00"
    legacy_hash = compute_entry_hash(
        prev_hash=GENESIS_HASH,
        timestamp_str=legacy_ts,
        user_email="legacy@chainnetra.local",
        action="LEGACY_ACTION",
        entity_type="SYSTEM",
        entity_id="1",
        details_json="{}"
    )

    entry1 = AuditLog(
        timestamp=datetime(2026, 1, 1, 10, 0, 0),
        user_email="legacy@chainnetra.local",
        action="LEGACY_ACTION",
        entity_type="SYSTEM",
        entity_id="1",
        details="{}",
        prev_hash=GENESIS_HASH,
        entry_hash=legacy_hash,
        signature=None
    )
    db_session.add(entry1)
    db_session.commit()

    # 2. Add modern entry with timezone-aware timestamp
    log_audit_action(
        db=db_session,
        user_email="modern@chainnetra.local",
        action="MODERN_ACTION",
        entity_type="CASE",
        entity_id="2"
    )

    # 3. Verify entire chain passes verification seamlessly
    result = verify_audit_chain(db_session)
    assert result["valid"] is True, f"Audit chain verification failed: {result}"


def test_concurrent_sequence_numbering(db_session: Session):
    """
    Tests 10 concurrent requests producing 10 sequential IDs with zero duplicates.
    """
    counter_name = "test_case"
    prefix = "TEST"
    engine = db_session.get_bind()
    ThreadSession = sessionmaker(bind=engine)

    results = []

    def get_seq(i):
        session = ThreadSession()
        try:
            seq = get_next_sequence_number(session, counter_name=counter_name, prefix=prefix)
            session.commit()
            return seq
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_seq, i) for i in range(10)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    # Assert 10 distinct IDs
    assert len(results) == 10
    assert len(set(results)) == 10, f"Duplicate IDs generated: {results}"

    # Extract integer sequence values and sort
    numbers = [int(r.split("-")[-1]) for r in results]
    numbers.sort()

    # Check they form a strictly sequential contiguous range with no gaps
    min_num = numbers[0]
    expected_sequence = list(range(min_num, min_num + 10))
    assert numbers == expected_sequence, f"Non-consecutive sequence numbers: {numbers} vs {expected_sequence}"


def test_delete_record_never_reuses_sequence(db_session: Session):
    """
    Verifies that deleting a case or complaint never regresses or reuses the sequence counter.
    """
    # 1. Create a case
    c1_num = get_next_sequence_number(db_session, "case", "CASE")
    case1 = Case(
        case_number=c1_num,
        title="Temporary Case",
        description="To be deleted",
        primary_chain="tron",
        primary_address="TLyqzVGLV1srkB7dToTAVHguKzc15geTnU",
        created_by="officer@chainnetra.local"
    )
    db_session.add(case1)
    db_session.commit()

    # 2. Delete the case
    db_session.delete(case1)
    db_session.commit()

    # 3. Generate next sequence number
    c2_num = get_next_sequence_number(db_session, "case", "CASE")

    # Sequence must NOT be the same as deleted c1_num
    assert c1_num != c2_num
    val1 = int(c1_num.split("-")[-1])
    val2 = int(c2_num.split("-")[-1])
    assert val2 > val1, f"Sequence number regressed or reused: {c2_num} <= {c1_num}"
