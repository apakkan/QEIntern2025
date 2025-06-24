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