# Imports and environment setup
import json
import os
from openai import AzureOpenAI as OpenAIAzureClient
from dotenv import load_dotenv
from agno.agent import Agent
from agno.tools import tool
from agno import memory
from agno.models.azure import AzureOpenAI as AgnoAzureModel
import sys
from tools.db_tools import query_postgres, vector_search_tool, query_postgres_tool
from database.qtest_db import connect_db, upsert_central_vector, insert_testcases
from database.embedding_utils import get_embedding
from database.rag_utils import insert_refined_requirement
from langchain_neo4j import Neo4jGraph
import time

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_VERSION = os.getenv("API_VERSION")
ENDPOINT = os.getenv("ENDPOINT")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")

# Initialize Azure OpenAI client
client = OpenAIAzureClient(
    api_key=API_KEY,
    api_version=API_VERSION,
    azure_endpoint=ENDPOINT,
)

azure_model = AgnoAzureModel(
    id="gpt-4.1",  # or your deployment/model name
    api_key=API_KEY,
    azure_endpoint=ENDPOINT,
    azure_deployment=DEPLOYMENT_NAME,
    api_version=API_VERSION,
)

graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

def fetch_raw_requirements():
    """Fetch raw requirements from the database."""
    rows = query_postgres("SELECT id as story_number, title as user_story, description FROM requirements")
    return [
        {"story_number": row[0], "user_story": row[1], "description": row[2]}
        for row in rows
    ]

def fetch_analyzed_requirements():
    """Fetch analyzed requirements from the database. (refinedrequirements label)"""
    rows = query_postgres("SELECT requirement_id, user_persona, user_story, functionality, description, release, related_story, business_priority FROM refinedrequirements")
    return [
        {
            "story_number": row[0],
            "user_persona": row[1],
            "user_story": row[2],
            "functionality": row[3],
            "description": row[4],
            "release": row[5],
            "related_stories": json.loads(row[6]) if row[6] else [],
            "business_priority": row[7],
        }
        for row in rows
    ]

def refine_requirement(raw_requirement: list) -> list:
    """Send requirements to LLM for analysis (related stories, functionality)."""
    formatted = "\n".join([
        f"{s['story_number']}: {s['user_story']} - {s['description']}"
        for s in raw_requirement
    ])
    messages = [
        {
            "role": "system",
            "content": ("You are quality engineer assistant. Given a list of story numbers, user stories, and descriptions,"
                        "analyze and return for each:\n"
                        "- related_stories: list of story_numbers that are linked or depend on each other\n"
                        "- functionality: which system feature, module, or function this story addresses.\n"
                        "Respond in JSON array, one object per story."),
        },
        {
            "role": "user",
            "content": f"Analyze the following requirements:\n\n {formatted}",
        }
    ]
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages
    )
    return response.choices[0].message.content

def generate_test_cases_tool(raw_requirement: list) -> list:
    """Send enriched requirements to LLM to generate test cases for each story."""
    formatted = "\n".join([
        f"{s['story_number']}: {s['user_story']} - {s['description']} | Related: {s.get('related_stories', [])} | Group: {s.get('functionality_group', [])}"
        for s in raw_requirement
    ])
    messages = [
        {
            "role": "system",
            "content": (
                "You are a test automation assistant specialized in generating comprehensive test cases from user stories. "
                "Your goal is to create test cases that cover: "
                "Functional testing, Integration testing, API testing, End-to-End (E2E) testing, Compliance, User Roles, and Permissions.\n"
                "For each user story: "
                "- Identify positive and negative test scenarios.\n"
                "- Include preconditions, test steps, expected results, and test data where applicable.\n"
                "- Ensure clarity, traceability, and alignment with acceptance criteria.\n"
                "- Focus on acceptance criteria, end-to-end process validation, user roles, permissions, and compliance.\n"
                "- Include regulatory and audit requirements if mentioned.\n"
                "Output structure (JSON): For each user story, return an object with these fields: "
                "executive_summary (string), user_story (string), happy_path_summary (string), "
                "scenario_table (list of objects: Test Case ID, Brief Description), "
                "detailed_test_cases (list of objects: Test Case ID, EPIC, Feature, User Story, Business Process, Sub-Process Title, Activity Title, Test Scenario Title, Precondition, Test Data, T-Code, SAP Fiori Application ID, User Role, Detailed Test Steps, Expected Result, Dependent Module/Process). "
                "Respond in a JSON array, one object per user story."
            )
        },
        { "role": "user", "content": formatted }
    ]
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages
    )
    return response.choices[0].message.content

def strip_code_blocks(text):
    """Remove code block markers from LLM output."""
    if text is None:
        return ''
    return text.replace('```json', '').replace('```', '').strip()

class RequirementAgent(Agent):
    tools = [refine_requirement]
    memory = memory.Memory(memory="")

    def run(self, **kwargs):
        """Run requirement analysis using the LLM and write to the database."""
        raw_requirements = kwargs["raw_requirements"]
        req_output = refine_requirement(raw_requirements)
        req_output_clean = strip_code_blocks(req_output)
        try:
            req_output_list = json.loads(req_output_clean)
        except Exception as e:
            print(f"Error parsing requirement agent output: {e}\nOutput was: {req_output_clean}")
            return []
        # Write each analyzed requirement to the database and Neo4j
        conn = connect_db()
        for req in req_output_list:
            embedding = get_embedding(f"{req.get('user_story', '')} {req.get('description', '')}")
            insert_refined_requirement(
                conn,
                requirement_id=req.get('story_number'),
                user_persona=req.get('user_persona'),
                user_story=req.get('user_story'),
                functionality=req.get('functionality'),
                refined_description=req.get('description'),
                release=req.get('release'),
                related_story=json.dumps(req.get('related_stories')) if req.get('related_stories') is not None else None,
                business_priority=req.get('business_priority'),
                embedding=embedding
            )
            # Also upsert to Neo4j:
            properties = {
                "story_number": req.get('story_number'),
                "user_story": req.get('user_story'),
                "description": req.get('description'),
                "functionality": req.get('functionality'),
                "related_stories": req.get('related_stories'),
                "business_priority": req.get('business_priority'),
                "agent_output": json.dumps(req)
            }
            properties = {k: v for k, v in properties.items() if v is not None}
            graph.query("""
                MERGE (r:Requirement {story_number: $story_number})
                SET r += $properties
                WITH r
                CALL db.create.setNodeVectorProperty(r, 'textEmbedding', $embedding)
            """, {"story_number": req.get('story_number'), "properties": properties, "embedding": embedding})

        if conn:
            conn.close()
        return req_output_list

class TestAgent(Agent):
    tools = [generate_test_cases_tool]
    memory = memory.Memory(memory="")

    def run(self, **kwargs):
        raw_requirements = kwargs["raw_requirements"]
        req_analysis = kwargs.get("req_analysis", [])

        # Map story number to requirement analysis
        analysis_map = {r['story_number']: r for r in req_analysis}

        # Group by functionality
        functionality_map = {}
        for r in req_analysis:
            functionality = r.get('functionality', 'Unknown')
            functionality_map.setdefault(functionality, []).append(r["story_number"])

        # Enrich stories with related stories and functionality group
        enriched_stories = []
        for story in raw_requirements:
            sn = story['story_number']
            ra = analysis_map.get(sn, {})
            enriched_stories.append({
                "story_number": sn,
                "user_story": story['user_story'],
                "description": story['description'],
                "related_stories": ra.get('related_stories', []),
                "functionality_group": functionality_map.get(ra.get('functionality', 'Unknown'), [])
            })

        # Batch the enriched stories to avoid LLM truncation (default 5 per batch)
        batch_size = 5
        all_test_cases = []
        for i in range(0, len(enriched_stories), batch_size):
            batch = enriched_stories[i:i+batch_size]
            llm_output = generate_test_cases_tool(batch)
            cleaned = strip_code_blocks(llm_output)
            try:
                test_cases = json.loads(cleaned)
            except Exception as e:
                print(f"Error parsing LLM output: {e}\nOutput: {llm_output}")
                continue
            all_test_cases.extend(test_cases)

        # Optionally, write all test cases to DB
        conn = connect_db()
        db_test_cases = []
        for tc in all_test_cases:
            db_test_cases.append({
                "requirement_id": tc.get('story_number'),
                "title": tc.get('title', ""),
                "test_case_description": tc.get('test_description', "")
            })
        if db_test_cases:
            insert_testcases(conn, db_test_cases)
        if conn:
            conn.close()
        return all_test_cases

def get_requirements_from_kg():
    results = graph.query("MATCH (r:Requirement) RETURN r")
    return [record['r'] for record in results]

def batch_upsert_requirements_to_neo4j(requirements, embeddings, batch_size=1):
    from langchain_neo4j import Neo4jGraph
    import os, time
    for i in range(0, len(requirements), batch_size):
        graph = Neo4jGraph(
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        batch = requirements[i:i+batch_size]
        batch_embeddings = embeddings[i:i+batch_size]
        for req, embedding in zip(batch, batch_embeddings):
            properties = {
                "story_number": req.get('story_number'),
                "user_story": req.get('user_story'),
                "description": req.get('description'),
                "functionality": req.get('functionality'),
                "related_stories": req.get('related_stories'),
                "business_priority": req.get('business_priority'),
                "agent_output": json.dumps(req)
            }
            properties = {k: v for k, v in properties.items() if v is not None}
            graph.query("""
                MERGE (r:Requirement {story_number: $story_number})
                SET r += $properties
            """, {"story_number": req.get('story_number'), "properties": properties})
        time.sleep(0.5)

if __name__ == "__main__":
    # Fetch raw requirements from the database
    raw_requirements = fetch_raw_requirements()

    # Run requirement analysis and write to database/KG
    req_agent = RequirementAgent()
    req_output_list = req_agent.run(raw_requirements=raw_requirements)
    print(json.dumps(req_output_list, indent=2))

    # Fetch analyzed requirements from the database
    req_analysis = fetch_analyzed_requirements()

    # Run test case generation (batched)
    test_agent = TestAgent()
    test_output = test_agent.run(raw_requirements=raw_requirements, req_analysis=req_analysis)
    print(json.dumps(test_output, indent=2))

    # Upsert requirements to Postgres
    conn = connect_db()
    embeddings = []
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
            agent_output=req,  # store the whole dict as JSONB
            embedding=embedding
        )
        embeddings.append(embedding)
    if conn:
        conn.close()

    # --- Batch upsert to Neo4j ---
    batch_upsert_requirements_to_neo4j(req_output_list, embeddings, batch_size=1)
