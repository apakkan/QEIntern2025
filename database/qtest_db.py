import time
import psycopg2
import os
import requests
import json
from database.embedding_utils import get_embedding
from dotenv import load_dotenv

load_dotenv()

# ==== Global Constants ====
OPENAI_EMBEDDING_DIM = 1536  # Dimension of OpenAI embeddings
DEFAULT_PAGE_SIZE = 20       # Default page size for API pagination
MAX_PAGES = 100              # Max number of pages to fetch from API
RETRY_COUNT = 5              # Number of DB connection retries
RETRY_DELAY = 3              # Delay (seconds) between DB connection retries

# ==== Database Connection ====
def connect_db(retries=RETRY_COUNT, delay=RETRY_DELAY):
    """
    Connect to the PostgreSQL database with retry logic.
    """
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

# ==== Table Creation ====
def create_tables(conn):
    """
    Create all necessary tables if they do not exist.
    """
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS central_vectors (
            id SERIAL PRIMARY KEY,
            story_number INTEGER,
            source TEXT, -- 'raw', 'requirement_agent', 'test_agent'
            title TEXT,
            description TEXT,
            user_persona TEXT,
            user_story TEXT,
            functionality TEXT,
            related_stories INTEGER[],
            business_priority TEXT,
            agent_output JSONB,
            embedding vector({OPENAI_EMBEDDING_DIM}),
            kg_node_id TEXT,
            UNIQUE (story_number, source)
        );
    """)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT,
            priority TEXT,
            sprint TEXT,
            user_persona TEXT,
            user_story TEXT,
            functionality TEXT,              
            embedding vector({OPENAI_EMBEDDING_DIM})
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
    cursor.execute(f"""
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
            embedding vector({OPENAI_EMBEDDING_DIM})
        );
    """)
    conn.commit()
    cursor.close()
    print("Tables created successfully")

# ==== Insert Functions ====
def insert_requirement(conn, req_id, title, description, status):
    """
    Insert or update a requirement with embedding.
    """
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
    """
    Bulk insert test cases.
    """
    cursor = conn.cursor()
    data = [
        (
            tc.get("requirement_id"),
            tc.get("title"),
            tc.get("steps"),
            tc.get("expected_result")
        )
        for tc in testcases
    ]
    cursor.executemany(
        """
        INSERT INTO testcases (requirement_id, title, steps, expected_result)
        VALUES (%s, %s, %s, %s)
        """,
        data
    )
    conn.commit()
    cursor.close()

def insert_testruns(conn, testruns):
    """
    Bulk insert test runs.
    """
    cursor = conn.cursor()
    data = [
        (
            tr.get("testcase_id"),
            tr.get("status"),
            tr.get("executed_at")
        )
        for tr in testruns
    ]
    cursor.executemany(
        """
        INSERT INTO testruns (testcase_id, status, executed_at)
        VALUES (%s, %s, %s)
        """,
        data
    )
    conn.commit()
    cursor.close()

def insert_defects(conn, defects):
    """
    Bulk insert defects.
    """
    cursor = conn.cursor()
    data = [
        (
            defect.get("requirement_id"),
            defect.get("description"),
            defect.get("status")
        )
        for defect in defects
    ]
    cursor.executemany(
        """
        INSERT INTO defects (requirement_id, description, status)
        VALUES (%s, %s, %s)
        """,
        data
    )
    conn.commit()
    cursor.close()

def upsert_central_vector(
    conn, story_number, source, title, description, user_persona, user_story,
    functionality, related_stories, business_priority, agent_output, embedding, kg_node_id=None
):
    cursor = conn.cursor()
    # Convert agent_output to JSON string if it's a dict
    if agent_output is not None and isinstance(agent_output, dict):
        agent_output = json.dumps(agent_output)
    cursor.execute(
        """
        INSERT INTO central_vectors (
            story_number, source, title, description, user_persona, user_story,
            functionality, related_stories, business_priority, agent_output, embedding, kg_node_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (story_number, source) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            user_persona = EXCLUDED.user_persona,
            user_story = EXCLUDED.user_story,
            functionality = EXCLUDED.functionality,
            related_stories = EXCLUDED.related_stories,
            business_priority = EXCLUDED.business_priority,
            agent_output = EXCLUDED.agent_output,
            embedding = EXCLUDED.embedding,
            kg_node_id = EXCLUDED.kg_node_id
        """,
        (
            story_number, source, title, description, user_persona, user_story,
            functionality, related_stories, business_priority, agent_output, embedding, kg_node_id
        )
    )
    conn.commit()
    cursor.close()

# ==== qTest API Fetching ====
def fetch_qtest_entities(api_url_env, entity_name, sort_param="id"):
    """
    Fetch paginated entities from the qTest API.
    """
    url = os.environ.get(api_url_env)
    api_key = os.environ.get("QTEST_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    all_data = []
    seen_ids = set()
    page = 1
    page_size = DEFAULT_PAGE_SIZE

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
    """
    Fetch requirements from qTest.
    """
    return fetch_qtest_entities("QTEST_REQUIREMENTS_API_URL", "requirements", sort_param=None)  # requirements may not support sort

def get_qtest_testcases():
    """
    Fetch test cases from qTest.
    """
    return fetch_qtest_entities("QTEST_TESTCASES_API_URL", "testcases", sort_param="id")

def get_qtest_testruns():
    """
    Fetch test runs from qTest.
    """
    return fetch_qtest_entities("QTEST_TESTRUNS_API_URL", "testruns", sort_param="id")

def get_qtest_defects():
    """
    Fetch defects from qTest.
    """
    return fetch_qtest_entities("QTEST_DEFECTS_API_URL", "defects", sort_param="id")

# ==== Main Execution Block ====
if __name__ == "__main__":
    # Connect to the database
    conn = connect_db()
    if conn:
        create_tables(conn)

        # Fetch and insert requirements
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

        # Fetch and insert test cases
        testcases = get_qtest_testcases()
        if testcases:
            insert_testcases(conn, testcases)

        # Fetch and insert test runs
        testruns = get_qtest_testruns()
        if testruns:
            insert_testruns(conn, testruns)

        # Fetch and insert defects
        defects = get_qtest_defects()
        if defects:
            insert_defects(conn, defects)

        conn.close()

