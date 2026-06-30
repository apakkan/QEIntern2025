import os
import sys
import time
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from database.qtest_db import connect_db, create_tables, upsert_central_vector
from database.embedding_utils import get_embedding
from langchain_neo4j import Neo4jGraph

load_dotenv()


@pytest.mark.integration
def test_full_workflow():
    # 1. Initialize DB and tables
    conn = connect_db()
    assert conn, "Failed to connect to Postgres"
    create_tables(conn)

    # 2. Insert a sample requirement into central_vectors
    story_number = 999999
    sample_text = "Test requirement for workflow integration"
    embedding = get_embedding(sample_text)
    upsert_central_vector(
        conn,
        story_number=story_number,
        source="requirement_agent",
        title="Test Requirement",
        description=sample_text,
        user_persona="QA",
        user_story="As a QA, I want to test the workflow.",
        functionality="Testing",
        related_stories=[888888],
        business_priority="High",
        agent_output={"executive_summary": "Test summary"},
        embedding=embedding,
        kg_node_id=None
    )
    conn.close()

    # 3. Run the Neo4j sync script (sample_kg.py)
    import importlib.util
    script_path = os.path.join(os.path.dirname(__file__), "../knowledge_graph/sample_kg.py")
    spec = importlib.util.spec_from_file_location("sample_kg", script_path)
    sample_kg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sample_kg)

    # 4. Query Neo4j to verify the node exists
    graph = Neo4jGraph(
        url=os.getenv('NEO4J_URI'),
        username=os.getenv('NEO4J_USERNAME'),
        password=os.getenv('NEO4J_PASSWORD')
    )
    time.sleep(2)
    result = graph.query(
        "MATCH (r:Requirement {story_number: $story_number}) RETURN r LIMIT 1",
        {"story_number": story_number}
    )
    assert result, "Requirement node not found in Neo4j!"
    node = result[0]['r']
    print("Neo4j node properties:", node)

    assert 'textEmbedding' in node, "Embedding not found on Neo4j node!"

    print("Workflow integration test passed.")
