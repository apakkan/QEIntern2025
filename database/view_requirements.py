import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    return psycopg2.connect(
        database=os.environ.get("POSTGRES_DB", "mydb"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        host=os.environ.get("POSTGRES_HOST", "maindb"),
        port=os.environ.get("POSTGRES_PORT", "5432")
    )

def print_requirements():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, description, status, priority, release, user_persona, user_story, functionality
        FROM requirements
    """)
    rows = cur.fetchall()
    for row in rows:
        print(dict(
            id=row[0],
            title=row[1],
            description=row[2],
            status=row[3],
            priority=row[4],
            release=row[5],
            user_persona=row[6],
            user_story=row[7],
            functionality=row[8]
        ))
    cur.close()
    conn.close()

if __name__ == "__main__":
    print_requirements()