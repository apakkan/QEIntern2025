"""Tests for on-demand + cached real risk (P4).

Universal + LLM-free: RiskAgent is injected as a fake, and cache rows are inserted
into central_vectors directly via SQL. No hardcoded requirement ids drive the logic;
the sentinel ids below are just disposable test fixtures, cleaned up after.
"""
import json

import pytest

from database.qtest_db import connect_db, create_tables
from gpt_agent import parse_risk_output, get_cached_risk, get_or_compute_risk

_REQ_HIT, _REQ_MISS, _REQ_ABSENT = 999_000_201, 999_000_202, 999_000_203


class _FakeRiskAgent:
    """Stand-in for RiskAgent: records call count, returns a fixed risk dict in the
    real agent's output shape (note the capitalized 'Risk Factor'/'User_persona')."""
    def __init__(self, risk_factor=7, persona="Case Worker"):
        self.calls = 0
        self._rf = risk_factor
        self._persona = persona

    def run(self, **kwargs):
        self.calls += 1
        stories = kwargs["user_stories"]
        return [{
            "story_number": stories[0]["story_number"],
            "user_story": stories[0].get("user_story", ""),
            "functionality": stories[0].get("description", ""),
            "User_persona": self._persona,
            "Risk Factor": self._rf,
        }]


# ── pure unit: parse_risk_output ─────────────────────────────────────────────

def test_parse_pulls_risk_factor_and_persona_from_agent_output():
    out = {"Risk Factor": 5, "User_persona": "Case Manager", "functionality": "X"}
    assert parse_risk_output(out) == {"risk_factor": 5, "persona": "Case Manager"}


def test_parse_defaults_to_none_when_keys_absent():
    assert parse_risk_output({}) == {"risk_factor": None, "persona": None}


# ── integration helpers ──────────────────────────────────────────────────────

def _insert_requirement(cur, rid, title="sentinel"):
    cur.execute(
        "INSERT INTO requirements (id, title) VALUES (%s, %s) "
        "ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title",
        (rid, title),
    )


def _insert_cached_risk(cur, rid, agent_output):
    cur.execute(
        "INSERT INTO central_vectors (story_number, source, agent_output) "
        "VALUES (%s, 'risk_agent', %s::jsonb) "
        "ON CONFLICT (story_number, source) DO UPDATE SET agent_output=EXCLUDED.agent_output",
        (rid, json.dumps(agent_output)),
    )


def _cleanup(cur, *rids):
    for rid in rids:
        cur.execute("DELETE FROM central_vectors WHERE story_number=%s", (rid,))
        cur.execute("DELETE FROM requirements WHERE id=%s", (rid,))


# ── integration: get_cached_risk ─────────────────────────────────────────────

@pytest.mark.integration
def test_get_cached_risk_returns_parsed_row_or_none():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _insert_requirement(cur, _REQ_HIT)
        _insert_cached_risk(cur, _REQ_HIT, {"Risk Factor": 4, "User_persona": "X"})
        conn.commit()
        assert get_cached_risk(conn, _REQ_HIT) == {"risk_factor": 4, "persona": "X"}
        assert get_cached_risk(conn, _REQ_MISS) is None
    finally:
        _cleanup(cur, _REQ_HIT); conn.commit(); cur.close(); conn.close()


# ── integration: get_or_compute_risk ─────────────────────────────────────────

@pytest.mark.integration
def test_compute_serves_cache_without_calling_agent():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _insert_requirement(cur, _REQ_HIT)
        _insert_cached_risk(cur, _REQ_HIT, {"Risk Factor": 9, "User_persona": "Cached"})
        conn.commit()
        agent = _FakeRiskAgent(risk_factor=1)
        result = get_or_compute_risk(conn, _REQ_HIT, agent=agent)
        assert agent.calls == 0, "cache hit must not invoke the agent"
        assert result["risk_factor"] == 9
        assert result["source"] == "cached"
    finally:
        _cleanup(cur, _REQ_HIT); conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_compute_on_miss_then_caches():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _insert_requirement(cur, _REQ_MISS)          # requirement exists, no cached risk
        conn.commit()
        agent = _FakeRiskAgent(risk_factor=7, persona="Case Worker")
        first = get_or_compute_risk(conn, _REQ_MISS, agent=agent)
        assert agent.calls == 1
        assert first["risk_factor"] == 7 and first["persona"] == "Case Worker"
        assert first["source"] == "computed"
        second = get_or_compute_risk(conn, _REQ_MISS, agent=agent)
        assert agent.calls == 1, "second call must be served from cache, not recomputed"
        assert second["risk_factor"] == 7
    finally:
        _cleanup(cur, _REQ_MISS); conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_compute_raises_lookuperror_when_requirement_absent():
    conn = connect_db(); create_tables(conn); cur = conn.cursor()
    try:
        _cleanup(cur, _REQ_ABSENT); conn.commit()    # ensure truly absent
        with pytest.raises(LookupError):
            get_or_compute_risk(conn, _REQ_ABSENT, agent=_FakeRiskAgent())
    finally:
        _cleanup(cur, _REQ_ABSENT); conn.commit(); cur.close(); conn.close()
