"""Integration test: insert_requirement persists priority + sprint.

Uses the real Postgres (Neon) so the actual INSERT column list is exercised, but
mocks the embedding call so it does not spend LLM quota and stays about the
columns. Cleans up its sentinel row. Marked integration (needs a live DB).
"""
from unittest.mock import patch

import pytest

from database import qtest_db
from database.qtest_db import connect_db, create_tables, insert_requirement

_SENTINEL_ID = 999_000_001


@pytest.mark.integration
def test_insert_requirement_persists_priority_and_sprint():
    conn = connect_db()
    assert conn is not None, "no DB connection"
    create_tables(conn)
    try:
        # embedding width must match the table's vector(N); mock returns that width
        dim = qtest_db.OPENAI_EMBEDDING_DIM
        with patch.object(qtest_db, "get_embedding", return_value=[0.0] * dim):
            insert_requirement(
                conn,
                req_id=_SENTINEL_ID,
                title="Sentinel requirement",
                description="body",
                status="Approved",
                priority="Medium",
                sprint="Sprint 3",
            )
        cur = conn.cursor()
        cur.execute(
            "SELECT title, description, status, priority, sprint FROM requirements WHERE id=%s",
            (_SENTINEL_ID,),
        )
        row = cur.fetchone()
        cur.close()
        assert row == ("Sentinel requirement", "body", "Approved", "Medium", "Sprint 3")
    finally:
        cur = conn.cursor()
        cur.execute("DELETE FROM requirements WHERE id=%s", (_SENTINEL_ID,))
        conn.commit()
        cur.close()
        conn.close()
