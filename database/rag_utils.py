from dotenv import load_dotenv

load_dotenv()

def insert_refined_requirement(
    conn,
    requirement_id,
    user_persona,
    user_story,
    functionality,
    refined_description,
    release,
    related_story,
    business_priority,
    embedding
):
    """
    Insert or update a refined requirement in the database.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO refinedrequirements (
                requirement_id, user_persona, user_story, functionality, description,
                release, related_story, business_priority, embedding
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (requirement_id) DO UPDATE SET
                user_persona = EXCLUDED.user_persona,
                user_story = EXCLUDED.user_story,
                functionality = EXCLUDED.functionality,
                description = EXCLUDED.description,
                release = EXCLUDED.release,
                related_story = EXCLUDED.related_story,
                business_priority = EXCLUDED.business_priority,
                embedding = EXCLUDED.embedding
            """,
            (
                requirement_id, user_persona, user_story, functionality, refined_description,
                release, related_story, business_priority, embedding
            )
        )
    conn.commit()

def find_similar_requirements(conn, query_embedding, top_k=3):
    """
    Find the top_k most similar requirements by vector distance.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, description, embedding <-> %s::vector AS distance
            FROM requirements
            ORDER BY embedding <-> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, top_k)
        )
        results = cursor.fetchall()
    return results


def _relationship_score(distance):
    """Map a pgvector COSINE distance to a 0-100 relationship score.

    Cosine distance is 0 for identical direction and grows as vectors diverge
    (1 = orthogonal). similarity% = (1 - distance) * 100, clamped to [0, 100].
    General: no dataset-specific thresholds — the same formula holds for any data.
    """
    return max(0, min(100, round((1.0 - float(distance)) * 100)))


def find_related_requirements(conn, requirement_id, top_k=5):
    """Return the top_k requirements most semantically similar to ``requirement_id``.

    Universal: nearest neighbours by embedding COSINE distance over whatever is in
    the table — no hardcoded ids/sprints/functionality. The target itself is excluded
    by value, and rows without an embedding are skipped.

    Raises:
        LookupError: the target requirement id does not exist.
    Returns:
        list[dict] of {id, name, description, relationship}; empty when the target
        has no embedding (nothing to compare against).
    """
    with conn.cursor() as cursor:
        cursor.execute("SELECT embedding::text FROM requirements WHERE id = %s", (requirement_id,))
        row = cursor.fetchone()
        if row is None:
            raise LookupError(f"requirement {requirement_id} not found")
        target_embedding = row[0]
        if target_embedding is None:
            return []

        cursor.execute(
            """
            SELECT id, title, description, embedding <=> %s::vector AS distance
            FROM requirements
            WHERE id != %s AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (target_embedding, requirement_id, target_embedding, top_k),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": r[0],
            "name": r[1] or "Untitled",
            "description": r[2] or "No description",
            "relationship": _relationship_score(r[3]),
        }
        for r in rows
    ]