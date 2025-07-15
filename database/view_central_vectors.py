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

def print_central_vectors():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, story_number, source, title, description, user_persona, user_story, functionality, business_priority
        FROM central_vectors
    """)
    rows = cur.fetchall()
    for row in rows:
        print(dict(
            id=row[0],
            story_number=row[1],
            source=row[2],
            title=row[3],
            description=row[4],
            user_persona=row[5],
            user_story=row[6],
            functionality=row[7],
            business_priority=row[8]
        ))
    cur.close()
    conn.close()

if __name__ == "__main__":
    print_central_vectors()