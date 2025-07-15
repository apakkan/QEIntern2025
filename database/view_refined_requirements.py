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

def print_refined_requirements():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT requirement_id, user_persona, user_story, functionality, description, release, related_story, business_priority
        FROM refinedrequirements
    """)
    rows = cur.fetchall()
    for row in rows:
        print(dict(
            requirement_id=row[0],
            user_persona=row[1],
            user_story=row[2],
            functionality=row[3],
            description=row[4],
            release=row[5],
            related_story=row[6],
            business_priority=row[7]
        ))
    cur.close()
    conn.close()