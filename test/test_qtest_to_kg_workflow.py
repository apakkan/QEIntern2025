import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from gpt_agent import RequirementAgent, TestAgent, get_requirements_from_kg
from database.qtest_db import connect_db, upsert_central_vector
from database.embedding_utils import get_embedding
from langchain_neo4j import Neo4jGraph


def remove_vectors(data):
    if isinstance(data, list):
        return [remove_vectors(item) for item in data]
    elif isinstance(data, dict):
        return {
            k: remove_vectors(v)
            for k, v in data.items()
            if k not in ("embedding", "textEmbedding")
        }
    else:
        return data


@pytest.mark.integration
def test_end_to_end_workflow():
    # 1. Load requirements from DB (populated from qTest)
    conn = connect_db()
    rows = conn.cursor()
    rows.execute("SELECT id as story_number, title as user_story, description FROM requirements")
    raw_requirements = [
        {"story_number": row[0], "user_story": row[1], "description": row[2]}
        for row in rows.fetchall()
    ]
    rows.close()
    assert raw_requirements, "No requirements found in the database!"

    # 2. Run RequirementAgent to enrich requirements (returns a parsed list directly)
    req_agent = RequirementAgent()
    req_output_list = req_agent.run(raw_requirements=raw_requirements)
    assert req_output_list, "RequirementAgent did not return valid output!"

    # 3. Insert enriched requirements into central_vectors and Neo4j
    for req in req_output_list:
        embedding = get_embedding(f"{req.get('user_story', '')} {req.get('description', '')}")
        upsert_central_vector(
            conn,
            story_number=req.get('story_number'),
            source='requirement_agent',
            title=None,
            description=req.get('description'),
            user_persona=req.get('user_persona'),
            user_story=req.get('user_story'),
            functionality=req.get('functionality'),
            related_stories=req.get('related_stories'),
            business_priority=req.get('business_priority'),
            agent_output=req,
            embedding=embedding
        )
    conn.close()

    # 4. Sync to Neo4j (run sample_kg.py)
    import importlib.util
    script_path = os.path.join(os.path.dirname(__file__), "../knowledge_graph/sample_kg.py")
    spec = importlib.util.spec_from_file_location("sample_kg", script_path)
    sample_kg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sample_kg)

    # 5. Run TestAgent using requirements from KG
    enriched_reqs = get_requirements_from_kg()
    enriched_reqs = [
        {
            **(record['r'] if 'r' in record else record),
            'user_story': (
                record['r'].get('user_story') if 'r' in record and 'user_story' in record['r']
                else record['r'].get('title') if 'r' in record and 'title' in record['r']
                else record.get('user_story') if 'user_story' in record
                else record.get('title', '')
            ),
            'description': (
                record['r'].get('description') if 'r' in record and 'description' in record['r']
                else record.get('description', '')
            )
        }
        for record in enriched_reqs
    ]
    print("enriched_reqs (flattened):", json.dumps(remove_vectors(enriched_reqs), indent=2))
    test_agent = TestAgent()
    test_cases = test_agent.run(raw_requirements=enriched_reqs, req_analysis=req_output_list)
    assert test_cases, "No test cases generated from KG!"
    print("Generated test cases:", json.dumps(test_cases, indent=2))
    print("End-to-end workflow test passed.")
