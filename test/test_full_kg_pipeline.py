import os
import sys
import time
import json
from langchain_neo4j import Neo4jGraph
from database.qtest_db import connect_db, create_tables, upsert_central_vector
from database.embedding_utils import get_embedding

# Add your app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_full_kg_pipeline():
    # 1. Insert a sample requirement into Postgres
    # conn = connect_db()
    # create_tables(conn)
    # story_number = 123456
    # upsert_central_vector(
    #     conn,
    #     story_number=story_number,
    #     source="raw",
    #     title="Sample Requirement",
    #     description="A requirement for full KG pipeline test.",
    #     user_persona="User",
    #     user_story="As a user, I want to test the KG pipeline.",
    #     functionality="Pipeline",
    #     related_stories=[],
    #     business_priority="Medium",
    #     agent_output=None,
    #     embedding=get_embedding("A requirement for full KG pipeline test."),
    #     kg_node_id=None
    # )
    # conn.close()

    # 2. Sync requirements to Neo4j
    import importlib.util
    script_path = os.path.join(os.path.dirname(__file__), "../knowledge_graph/sample_kg.py")
    spec = importlib.util.spec_from_file_location("sample_kg", script_path)
    sample_kg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sample_kg)

    # 3. Run your GPT agent to enrich requirements and generate test cases
    # (You may want to import and call your gpt_agent.py logic here)
    # For example:
    # from gpt_agent import RequirementAgent, TestAgent, get_requirements_from_kg
    # ...run agents and insert outputs into Neo4j...

    # 4. Query Neo4j to verify enriched requirements and test cases exist
    graph = Neo4jGraph(
        url=os.getenv('NEO4J_URI'),
        username=os.getenv('NEO4J_USERNAME'),
        password=os.getenv('NEO4J_PASSWORD')
    )
    time.sleep(2)
    result = graph.query(
        "MATCH (r:RawRequirement {story_number: $story_number}) RETURN r LIMIT 1",
        {"story_number": story_number}
    )
    assert result, "RawRequirement node not found in Neo4j!"
    print("Neo4j node:", result[0]['r'])

    # 5. Have your test agent read from Neo4j and verify output
    # test_cases = TestAgent().run(raw_requirements=get_requirements_from_kg(), req_analysis=...)
    # assert test_cases, "No test cases generated from KG!"

    print("Full KG pipeline test passed.")

if __name__ == "__main__":
    test_full_kg_pipeline()