"""Tests for semantic (vector) related-stories.

Universal by construction: no hardcoded requirement ids, sprints, or functionality
strings drive the logic. The integration tests insert synthetic requirements with
hand-crafted embedding vectors directly via SQL (no LLM, so no rate limits and fully
deterministic), assert nearest-neighbour ordering / self-exclusion / shape, then clean up.
"""
import pytest

from database.qtest_db import connect_db, OPENAI_EMBEDDING_DIM
from database.rag_utils import find_related_requirements, _relationship_score


# ── pure unit: distance → relationship score ─────────────────────────────────

def test_score_is_100_at_zero_distance():
    assert _relationship_score(0.0) == 100


def test_score_is_0_at_cosine_distance_1():
    assert _relationship_score(1.0) == 0


def test_score_decreases_with_distance():
    assert _relationship_score(0.2) > _relationship_score(0.8)


def test_score_clamped_to_0_100_range():
    assert _relationship_score(2.0) == 0      # opposite vectors
    assert _relationship_score(-0.1) == 100   # defensive lower clamp


# ── integration: vector search over real pgvector ────────────────────────────

def _vec(pairs):
    """Build a pgvector literal of width OPENAI_EMBEDDING_DIM with given (index,value)."""
    v = [0.0] * OPENAI_EMBEDDING_DIM
    for i, val in pairs:
        v[i] = val
    return "[" + ",".join(str(x) for x in v) + "]"


_T, _N1, _F, _NOEMB = 999_000_101, 999_000_102, 999_000_103, 999_000_110


@pytest.mark.integration
def test_related_orders_by_similarity_excludes_self_and_shapes():
    conn = connect_db()
    cur = conn.cursor()
    try:
        for rid, title, pairs in [
            (_T,  "target", [(0, 1.0)]),
            (_N1, "near",   [(0, 0.9), (1, 0.1)]),   # small angle from target
            (_F,  "far",    [(1, 1.0)]),             # orthogonal → cosine dist ~1
        ]:
            cur.execute(
                "INSERT INTO requirements (id,title,embedding) VALUES (%s,%s,%s::vector) "
                "ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, embedding=EXCLUDED.embedding",
                (rid, title, _vec(pairs)),
            )
        conn.commit()

        results = find_related_requirements(conn, _T, top_k=100)
        by_id = {r["id"]: r for r in results}

        assert _T not in by_id, "target must be excluded from its own related list"
        assert _N1 in by_id and _F in by_id
        assert by_id[_N1]["relationship"] > by_id[_F]["relationship"], "nearer story scores higher"
        assert {"id", "name", "description", "relationship"} <= set(by_id[_N1].keys())
        assert 0 <= by_id[_F]["relationship"] <= 100
    finally:
        cur.execute("DELETE FROM requirements WHERE id IN (%s,%s,%s)", (_T, _N1, _F))
        conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_related_is_empty_when_target_has_no_embedding():
    conn = connect_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO requirements (id,title,embedding) VALUES (%s,'no-emb',NULL) "
            "ON CONFLICT (id) DO UPDATE SET title='no-emb', embedding=NULL",
            (_NOEMB,),
        )
        conn.commit()
        assert find_related_requirements(conn, _NOEMB, top_k=5) == []
    finally:
        cur.execute("DELETE FROM requirements WHERE id=%s", (_NOEMB,))
        conn.commit(); cur.close(); conn.close()


@pytest.mark.integration
def test_related_raises_lookuperror_when_target_missing():
    conn = connect_db()
    try:
        with pytest.raises(LookupError):
            find_related_requirements(conn, 999_999_999, top_k=5)
    finally:
        conn.close()
