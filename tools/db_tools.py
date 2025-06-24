import psycopg2
import os
from database.qtest_db import connect_db
from database.embedding_utils import get_embedding
from database.rag_utils import find_similar_requirements
from agno.tools import tool

@tool
def query_postgres(sql_query: str):
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
    conn = connect_db()
    embedding = get_embedding(query)
    results = find_similar_requirements(conn, embedding, top_k=top_k)
    conn.close()
    return [
        {"id": row[0], "title": row[1], "description": row[2], "distance": row[3]}
        for row in results
    ]