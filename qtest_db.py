import time
import psycopg2
import os
import requests
from embedding_utils import get_embedding

def connect_db(retries=5, delay=3):
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                database=os.environ.get("POSTGRES_DB", "mydb"),
                user=os.environ.get("POSTGRES_USER", "postgres"),
                password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
                host=os.environ.get("POSTGRES_HOST", "maindb"),
                port=os.environ.get("POSTGRES_PORT", "5432")
            )
            return conn
        except psycopg2.OperationalError as e:
            print(f"Connection error: {e}")
            if i < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                return None

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT,
            embedding vector(1536)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS testcases (
            id SERIAL PRIMARY KEY,
            requirement_id INTEGER REFERENCES requirements(id),
            title TEXT NOT NULL,
            steps TEXT,
            expected_result TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS testruns (
            id SERIAL PRIMARY KEY,
            testcase_id INTEGER REFERENCES testcases(id),
            status TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defects (
            id SERIAL PRIMARY KEY,
            requirement_id INTEGER REFERENCES requirements(id),
            description TEXT,
            status TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refinedrequirements (
            id SERIAL PRIMARY KEY,
            requirement_id INTEGER REFERENCES requirements(id) UNIQUE,
            user_persona TEXT,
            user_story TEXT,
            functionality TEXT,
            description TEXT,
            release TEXT,
            related_story TEXT,
            business_priority TEXT,
            embedding vector(1536)
        );
    """)
    conn.commit()
    cursor.close()
    print("Tables created successfully")

def insert_requirement(conn, req_id, title, description, status):
    embedding = get_embedding(f"{title} {description}")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO requirements (id, title, description, status, embedding)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            status = EXCLUDED.status,
            embedding = EXCLUDED.embedding
        """,
        (req_id, title, description, status, embedding)
    )
    conn.commit()
    cursor.close()

def insert_testcases(conn, testcases):
    cursor = conn.cursor()
    for tc in testcases:
        cursor.execute(
            """
            INSERT INTO testcases (requirement_id, title, steps, expected_result)
            VALUES (%s, %s, %s, %s)
            """,
            (tc.get("requirement_id"), tc.get("title"), tc.get("steps"), tc.get("expected_result"))
        )
    conn.commit()
    cursor.close()

def insert_testruns(conn, testruns):
    cursor = conn.cursor()
    for tr in testruns:
        cursor.execute(
            """
            INSERT INTO testruns (testcase_id, status, executed_at)
            VALUES (%s, %s, %s)
            """,
            (tr.get("testcase_id"), tr.get("status"), tr.get("executed_at"))
        )
    conn.commit()
    cursor.close()

def insert_defects(conn, defects):
    cursor = conn.cursor()
    for defect in defects:
        cursor.execute(
            """
            INSERT INTO defects (requirement_id, description, status)
            VALUES (%s, %s, %s)
            """,
            (defect.get("requirement_id"), defect.get("description"), defect.get("status"))
        )
    conn.commit()
    cursor.close()

def get_qtest_data():
    url = os.environ.get("QTEST_API_URL")
    api_key = os.environ.get("QTEST_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("Sample qTest API data:", data[:1] if isinstance(data, list) else data)
        return data
    else:
        print(f"Error fetching qTest data: {response.status_code}")
        return None
    

def get_qtest_testcases():
    return [
        {"requirement_id": 1, "title": "Upload file test", "steps": "Step 1: ...", "expected_result": "File uploaded"},
        {"requirement_id": 2, "title": "Download file test", "steps": "Step 1: ...", "expected_result": "File downloaded"}
    ]

def get_qtest_testruns():
    return [
        {"testcase_id": 1, "status": "Passed", "executed_at": "2024-06-19 10:00:00"},
        {"testcase_id": 2, "status": "Failed", "executed_at": "2024-06-19 11:00:00"}
    ]

def get_qtest_defects():
    return [
        {"requirement_id": 1, "description": "Upload button missing", "status": "Open"},
        {"requirement_id": 2, "description": "Download fails on large files", "status": "In Progress"}
    ]

if __name__ == "__main__":
    conn = connect_db()
    if conn:
        create_tables(conn)

        requirements = get_qtest_data()
        if requirements:
            for req in requirements:
                insert_requirement(
                    conn,
                    req_id=req["id"],
                    title=req.get("name", "Untitled"),
                    description=req.get("description", ""),
                    status=req.get("status", "New")
                )

        testcases = get_qtest_testcases()
        if testcases:
            insert_testcases(conn, testcases)

        testruns = get_qtest_testruns()
        if testruns:
            insert_testruns(conn, testruns)

        defects = get_qtest_defects()
        if defects:
            insert_defects(conn, defects)

        conn.close()

