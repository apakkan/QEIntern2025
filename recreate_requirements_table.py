import psycopg2
import os

def recreate_requirements_table():
    conn = psycopg2.connect(
        database=os.environ.get("POSTGRES_DB", "mydb"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        host=os.environ.get("POSTGRES_HOST", "maindb"),
        port=os.environ.get("POSTGRES_PORT", "5432")
    )
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS requirements;")
    cur.execute("""
        CREATE TABLE requirements (
            story_number BIGINT PRIMARY KEY,
            user_story TEXT,
            description TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("requirements table dropped and recreated.")

if __name__ == "__main__":
    recreate_requirements_table()
