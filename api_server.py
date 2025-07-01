from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import psycopg2
from neo4j import GraphDatabase
from typing import List, Optional

app = FastAPI()

# --- PostgreSQL Connection ---
def get_pg_conn():
    return psycopg2.connect(
        database=os.environ.get("POSTGRES_DB", "mydb"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        host=os.environ.get("POSTGRES_HOST", "maindb"),
        port=os.environ.get("POSTGRES_PORT", "5432")
    )

# --- Neo4j Connection ---
def get_neo4j_driver():
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME")
    pwd = os.environ.get("NEO4J_PASSWORD")
    return GraphDatabase.driver(uri, auth=(user, pwd))

# --- Pydantic Models ---
class Requirement(BaseModel):
    story_number: int
    title: Optional[str]
    description: Optional[str]
    status: Optional[str]

class TestCase(BaseModel):
    id: int
    requirement_id: int
    title: Optional[str]
    test_case_description: Optional[str]

# --- API Endpoints ---

@app.get("/requirements/", response_model=List[Requirement])
def get_requirements():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, status FROM requirements")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        Requirement(
            story_number=row[0],
            title=row[1],
            description=row[2],
            status=row[3]
        ) for row in rows
    ]

@app.get("/testcases/", response_model=List[TestCase])
def get_testcases():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, requirement_id, title, test_case_description FROM testcases")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        TestCase(
            id=row[0],
            requirement_id=row[1],
            title=row[2],
            test_case_description=row[3]
        ) for row in rows
    ]

@app.get("/testcases/requirement/{requirement_id}", response_model=List[TestCase])
def get_testcases_for_requirement(requirement_id: int):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, requirement_id, title, test_case_description FROM testcases WHERE requirement_id = %s", (requirement_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        TestCase(
            id=row[0],
            requirement_id=row[1],
            title=row[2],
            test_case_description=row[3]
        ) for row in rows
    ]

@app.get("/kg/requirement/{story_number}")
def get_kg_requirement(story_number: int):
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (r:Requirement {story_number: $story_number}) RETURN r",
            story_number=story_number
        )
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Requirement not found in KG")
        node = record["r"]
        return dict(node)

@app.get("/kg/testcase/{test_case_id}")
def get_kg_testcase(test_case_id: int):
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(
            "MATCH (t:TestCase {test_case_id: $test_case_id}) RETURN t",
            test_case_id=test_case_id
        )
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Test case not found in KG")
        node = record["t"]
        return dict(node)

@app.get("/kg/requirement/{story_number}/testcases")
def get_kg_testcases_for_requirement(story_number: int):
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (r:Requirement {story_number: $story_number})-[:HAS_TEST_CASE]->(t:TestCase)
            RETURN t
            """,
            story_number=story_number
        )
        testcases = [dict(record["t"]) for record in result]
        if not testcases:
            raise HTTPException(status_code=404, detail="No test cases found for this requirement in KG")
        return testcases