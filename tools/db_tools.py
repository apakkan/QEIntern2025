import psycopg2
import os
from dotenv import load_dotenv
from database.qtest_db import connect_db
from database.embedding_utils import get_embedding
from database.rag_utils import find_similar_requirements
from agno.tools import tool

load_dotenv()

def query_postgres(sql_query: str):
    """
    Execute a raw SQL query on the PostgreSQL database and return all results.
    """
    try:
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
    except Exception as e:
        return f"Postgres error: {e}"

@tool
def query_postgres_tool(sql_query: str):
    """
    Tool wrapper for query_postgres, for agent use.
    """
    return query_postgres(sql_query)

def vector_search_tool(query: str, top_k: int = 3):
    """
    Perform a semantic vector search for requirements most similar to the query.
    """
    conn = connect_db()
    embedding = get_embedding(query)
    results = find_similar_requirements(conn, embedding, top_k=top_k)
    conn.close()
    return [
        {"id": row[0], "title": row[1], "description": row[2], "distance": row[3]}
        for row in results
    ]

def query_pg(sql):
    """
    Run a SQL query on the Postgres database and return the results.
    Usage: query_pg("SELECT * FROM requirements LIMIT 5")
    """
    rows = query_postgres(sql)
    return str(rows)