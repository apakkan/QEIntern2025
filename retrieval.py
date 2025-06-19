def retrieve_similar_requirements(conn, query_embedding, top_k=5):
    """
    Returns the top_k most similar refined requirements using pgvector.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, requirement_id, title, description, status, embedding <=> %s AS distance
        FROM RefinedRequirements
        ORDER BY embedding <=> %s
        LIMIT %s
        """,
        (query_embedding, query_embedding, top_k)
    )
    results = cursor.fetchall()
    cursor.close()
    return results