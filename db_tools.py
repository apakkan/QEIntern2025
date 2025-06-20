import psycopg2
import os

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