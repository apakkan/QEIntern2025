import time
import psycopg2
import os
import requests
from database.embedding_utils import get_embedding

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

def fetch_qtest_entities(api_url_env, entity_name, sort_param="id"):
    url = os.environ.get(api_url_env)
    api_key = os.environ.get("QTEST_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    all_data = []
    seen_ids = set()
    page = 1
    page_size = 20
    MAX_PAGES = 100

    while page <= MAX_PAGES:
        params = {"page": page, "pageSize": page_size}
        # Only add sort if supported by the endpoint
        if sort_param:
            params["sort"] = sort_param
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching qTest {entity_name}: {response.status_code}")
            break
        data = response.json()
        if not data or (isinstance(data, list) and len(data) == 0):
            break
        if not isinstance(data, list):
            print(f"qTest API: received non-list response for {entity_name}:", data)
            break

        new_count = 0
        for item in data:
            item_id = item.get("id")
            if item_id is not None and item_id not in seen_ids:
                all_data.append(item)
                seen_ids.add(item_id)
                new_count += 1

        print(f"Fetched page {page}, got {len(data)} {entity_name}, {new_count} new.")
        if len(data) < page_size or new_count == 0:
            break
        page += 1
    else:
        print(f"Warning: Reached maximum page limit for {entity_name}. Stopping fetch.")

    print(f"Total unique {entity_name} fetched: {len(all_data)}")
    return all_data

def get_qtest_requirements():
    return fetch_qtest_entities("QTEST_REQUIREMENTS_API_URL", "requirements", sort_param=None)  # requirements may not support sort

def get_qtest_testcases():
    return fetch_qtest_entities("QTEST_TESTCASES_API_URL", "testcases", sort_param="id")

def get_qtest_testruns():
    return fetch_qtest_entities("QTEST_TESTRUNS_API_URL", "testruns", sort_param="id")

def get_qtest_defects():
    return fetch_qtest_entities("QTEST_DEFECTS_API_URL", "defects", sort_param="id")

if __name__ == "__main__":
    conn = connect_db()
    if conn:
        create_tables(conn)

        requirements = get_qtest_requirements()
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

