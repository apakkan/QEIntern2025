import psycopg2
import os
from database.qtest_db import connect_db
from database.embedding_utils import get_embedding
from database.rag_utils import find_similar_requirements
from agno.tools import tool

@tool
def query_postgres(sql_query: str):
    """
    Execute a raw SQL query on the PostgreSQL database and return all results.

    Args:
        sql_query (str): The SQL query to execute.

    Returns:
        list: Query result rows.
    """
    # Establish a direct connection using environment variables
    conn = psycopg2.connect(
        database=os.environ.get("POSTGRES_DB", "mydb"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        host=os.environ.get("POSTGRES_HOST", "maindb"),
        port=os.environ.get("POSTGRES_PORT", "5432")
    )
    cur = conn.cursor()
    cur.execute(sql_query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def vector_search_tool(query: str, top_k: int = 3):
    """
    Perform a semantic vector search for requirements most similar to the query.

    Args:
        query (str): The natural language query to embed and search with.
        top_k (int): Number of top similar requirements to return.

    Returns:
        list[dict]: List of matching requirements with id, title, description, and distance.
    """
    conn = connect_db()
    embedding = get_embedding(query)
    results = find_similar_requirements(conn, embedding, top_k=top_k)
    conn.close()
    # Format results as a list of dictionaries for easy consumption
    return [
        {"id": row[0], "title": row[1], "description": row[2], "distance": row[3]}
        for row in results
    ]