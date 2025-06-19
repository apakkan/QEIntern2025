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
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO RefinedRequirements (
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
    cursor.close()