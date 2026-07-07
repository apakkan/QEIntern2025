"""Tests for cached test-case generation (P5).

Test cases were regenerated on every /test-cases call, so counts drifted run to
run. These cover the cache: generate once, serve the same set thereafter, with an
explicit regenerate. LLM-free (fake agents), synthetic cache rows, self-cleaning.
"""
import json

import pytest

from database.qtest_db import connect_db, create_tables
from gpt_agent import get_cached_testcases, get_or_compute_testcases

_REQ_HIT, _REQ_MISS, _REQ_REGEN, _REQ_ABSENT = 999_000_301, 999_000_302, 999_000_303, 999_000_304


class _FakeTestAgent:
    def __init__(self, cases=None):
        self.calls = 0
        self._cases = cases or [{"test_case_id": "TC-1", "title": "a case"}]

    def run(self, **kwargs):
        self.calls += 1
        # fresh copy each call so enrichment doesn't leak across calls
        return [dict(c) for c in self._cases]


class _FakeRelationAgent:
    def __init__(self, relations=None):
        self.calls = 0
        self._relations = relations or {"TC-1": 80}

    def run(self, **kwargs):
        self.calls += 1
        return {"test_case_to_story_relations": self._relations}


def _insert_requirement(cur, rid, title="sentinel"):
    cur.execute(
        "INSERT INTO requirements (id, title) VALUES (%s, %s) "
        "ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title",
        (rid, title),
    )


def _insert_cached_testcases(cur, rid, cases):
    cur.execute(
        "INSERT INTO central_vectors (story_number, source, agent_output) "
        "VALUES (%s, 'test_agent', %s::jsonb) "
        "ON CONFLICT (story_number, source) DO UPDATE SET agent_output=EXCLUDED.agent_output",
        (rid, json.dumps({"test_cases": cases})),
    )


def _cleanup(cur, *rids):
    for rid in rids:
        cur.execute("DELETE FROM central_vectors WHERE story_number=%s", (rid,))
        cur.execute("DELETE FROM requirements WHERE id=%s", (rid,))


@pytest.mark.integration
def test_get_cached_testcases_returns_list_or_none():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _insert_requirement(cur, _REQ_HIT)
        _insert_cached_testcases(cur, _REQ_HIT, [{"test_case_id": "TC-9", "title": "cached"}])
        conn.commit()
        cached = get_cached_testcases(conn, _REQ_HIT)
        assert cached == [{"test_case_id": "TC-9", "title": "cached"}]
        assert get_cached_testcases(conn, _REQ_MISS) is None
    finally:
        _cleanup(cur, _REQ_HIT); conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_cache_hit_does_not_call_agents():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _insert_requirement(cur, _REQ_HIT)
        _insert_cached_testcases(cur, _REQ_HIT, [{"test_case_id": "TC-9", "title": "cached"}])
        conn.commit()
        ta, ra = _FakeTestAgent(), _FakeRelationAgent()
        result = get_or_compute_testcases(conn, _REQ_HIT, test_agent=ta, relation_agent=ra)
        assert ta.calls == 0 and ra.calls == 0
        assert result == [{"test_case_id": "TC-9", "title": "cached"}]
    finally:
        _cleanup(cur, _REQ_HIT); conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_cache_miss_generates_enriches_and_caches():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _insert_requirement(cur, _REQ_MISS)
        conn.commit()
        ta = _FakeTestAgent(cases=[{"test_case_id": "TC-1", "title": "x"}])
        ra = _FakeRelationAgent(relations={"TC-1": 80})
        first = get_or_compute_testcases(conn, _REQ_MISS, test_agent=ta, relation_agent=ra)
        assert ta.calls == 1
        assert first[0]["coverage"] == 80          # enriched from RelationAgent
        # second call served from cache — no regeneration
        second = get_or_compute_testcases(conn, _REQ_MISS, test_agent=ta, relation_agent=ra)
        assert ta.calls == 1
        assert second == first
    finally:
        _cleanup(cur, _REQ_MISS); conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_regenerate_bypasses_cache():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _insert_requirement(cur, _REQ_REGEN)
        _insert_cached_testcases(cur, _REQ_REGEN, [{"test_case_id": "OLD", "title": "old"}])
        conn.commit()
        ta = _FakeTestAgent(cases=[{"test_case_id": "TC-NEW", "title": "new"}])
        ra = _FakeRelationAgent(relations={"TC-NEW": 55})
        result = get_or_compute_testcases(conn, _REQ_REGEN, regenerate=True, test_agent=ta, relation_agent=ra)
        assert ta.calls == 1, "regenerate must recompute even when cached"
        assert result[0]["test_case_id"] == "TC-NEW"
        assert result[0]["coverage"] == 55
    finally:
        _cleanup(cur, _REQ_REGEN); conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_raises_lookuperror_when_requirement_absent():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _cleanup(cur, _REQ_ABSENT); conn.commit()
        with pytest.raises(LookupError):
            get_or_compute_testcases(conn, _REQ_ABSENT, test_agent=_FakeTestAgent(), relation_agent=_FakeRelationAgent())
    finally:
        _cleanup(cur, _REQ_ABSENT); conn.commit(); cur.close(); conn.close()
