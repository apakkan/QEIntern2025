"""Tests for related_stories INTEGER[] coercion in upsert_central_vector (KG bug).

RequirementAgent emits related_stories as strings, which psycopg2 renders as text[]
and clashes with the INTEGER[] column (DatatypeMismatch / InvalidTextRepresentation).
The helper now normalizes to int[], dropping non-numeric refs with a warning.
Pure unit tests are LLM- and DB-free; integration tests hit the real column, self-clean.
"""
import logging

import pytest

from database.qtest_db import connect_db, upsert_central_vector, _normalize_int_array


# ── pure unit: _normalize_int_array ──────────────────────────────────────────

def test_none_stays_none():
    assert _normalize_int_array(None) is None


def test_int_list_passes_through():
    assert _normalize_int_array([1, 2]) == [1, 2]


def test_numeric_strings_become_ints():
    assert _normalize_int_array(["1", "2"]) == [1, 2]


def test_empty_list_stays_empty():
    assert _normalize_int_array([]) == []


def test_scalar_string_is_not_split_into_chars():
    assert _normalize_int_array("123") == [123]


def test_non_numeric_ref_is_dropped_with_warning(caplog):
    with caplog.at_level(logging.WARNING):
        result = _normalize_int_array([1, "US-3"])
    assert result == [1]
    assert any("US-3" in r.getMessage() for r in caplog.records)


# ── integration: the real column no longer rejects string lists ──────────────

_SENT = 999_000_411


def _read_related(cur, source):
    cur.execute(
        "SELECT related_stories FROM central_vectors WHERE story_number=%s AND source=%s",
        (_SENT, source),
    )
    return cur.fetchone()[0]


def _upsert(conn, source, related):
    upsert_central_vector(
        conn, story_number=_SENT, source=source, title=None, description=None,
        user_persona=None, user_story=None, functionality=None,
        related_stories=related, business_priority=None, agent_output={"x": 1}, embedding=None,
    )


@pytest.mark.integration
def test_upsert_accepts_and_coerces_string_related_stories():
    conn = connect_db(); cur = conn.cursor()
    try:
        _upsert(conn, "coerce_str", ["1", "2"])   # would DatatypeMismatch before the fix
        assert _read_related(cur, "coerce_str") == [1, 2]
    finally:
        cur.execute("DELETE FROM central_vectors WHERE story_number=%s", (_SENT,))
        conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_upsert_drops_non_numeric_related_stories():
    conn = connect_db(); cur = conn.cursor()
    try:
        _upsert(conn, "coerce_mixed", [1, "US-3"])  # would InvalidTextRepresentation before
        assert _read_related(cur, "coerce_mixed") == [1]
    finally:
        cur.execute("DELETE FROM central_vectors WHERE story_number=%s", (_SENT,))
        conn.commit(); cur.close(); conn.close()
