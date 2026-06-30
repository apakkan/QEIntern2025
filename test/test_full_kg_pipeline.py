import os
import sys
import time
import json
from langchain_neo4j import Neo4jGraph
from database.qtest_db import connect_db, create_tables, upsert_central_vector
from database.embedding_utils import get_embedding

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.mark.integration
def test_full_kg_pipeline():
    # 1. Insert a sample requirement into Postgres
    conn = connect_db()
    create_tables(conn)
    story_number = 123456
    upsert_central_vector(
        conn,
        story_number=story_number,
        source="raw",
        title="Sample Requirement",
        description="A requirement for full KG pipeline test.",
        user_persona="User",
        user_story="As a user, I want to test the KG pipeline.",
        functionality="Pipeline",
        related_stories=[],
        business_priority="Medium",
        agent_output=None,
        embedding=get_embedding("A requirement for full KG pipeline test."),
        kg_node_id=None
    )
    conn.close()

    # 2. Sync requirements to Neo4j
    import importlib.util
    script_path = os.path.join(os.path.dirname(__file__), "../knowledge_graph/sample_kg.py")
    spec = importlib.util.spec_from_file_location("sample_kg", script_path)
    sample_kg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sample_kg)

    # 3. Query Neo4j to verify the node exists (agents write :Requirement nodes)
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
    print("Neo4j node:", result[0]['r'])

    print("Full KG pipeline test passed.")
