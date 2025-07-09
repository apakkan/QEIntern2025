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

# --- Azure OpenAI and Neo4j Setup ---
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



# Initialize Neo4j graph connection
graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

# --- Data Fetching Functions ---
def fetch_raw_requirements():
    """Fetch raw requirements from the database."""
    rows = query_postgres("SELECT id as story_number, title as user_story, description FROM requirements")
    return [
        {"story_number": row[0], "user_story": row[1], "description": row[2]}
        for row in rows
    ]

def fetch_analyzed_requirements():
    """Fetch analyzed requirements from the database (refinedrequirements table)."""
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

# --- LLM Tool Functions ---
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
            "content": ("you are a test automation assistant.\n"
                        "Your task is to generate test cases for the following user stories.\n"
                        "Given the following user story and description, do the following:\n"
                        "1. identify the relevant test scenarios that cover the behavior described.\n"
                        "2. For each test case, return:\n"
                        "- test_case_id: unique identifier for the test case, use the format 'TC-XXX' ( e.g., 'TC-001', 'TC-002', ...)\n"
                        "- title: a short, descriptive title for the test case\n"
                        "- test_description: a berief description of what the test case will validate\n"
                        "For each user story you need to return the number of the user story, a test_case_id, title, and test_description.\n"
                        "Make sure each test case is clear, tracble, and testable.\n"
                        "Include both positive and negative test cases if relevant.\n"
                        "Respond in JSON array, one object per test case.")
        },
        { "role": "user", "content": formatted }
    ]
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages
    )
    return response.choices[0].message.content

def find_relations(user_stories: list, test_cases: list) -> list:
    """Send requirements to LLM for analysis (related stories, functionality)."""

    filtered_stories = [s for s in user_stories if 'user_story' in s and 'related_stories' in s]
    formatted_stories = "\n".join([
        f"Story {s['story_number']}: {s['user_story']} | Related: {s.get('related_stories', [])}" for s in filtered_stories
    ])
    formatted_cases = "\n".join([
        f"TestCase {tc.get('test_case_id', 'N/A')} (Story {tc.get('story_number', 'N/A')}): {tc.get('title', 'N/A')} - {tc.get('test_description', '')}"
        for tc in test_cases if 'story_number' in tc
    ])
    formatted = f"User Stories:\n{formatted_stories}\n\nTest Cases:\n{formatted_cases}"
    
    messages = [
        {
            "role": "system",
            "content": ("You are a requirements and test case relation analysis assistant.\n"
            "You will be given a list of user stories and a list of test cases.\n"
            "Each user story has: story_number, user_story, and related_stories.\n"
            "Each test case has: test_case_id, title, test_description, and is linked to a user story by story_number.\n\n"
            "Your tasks:\n"
            "1. For every user story, calculate a 'relation percentage' (0-100) only to the stories related to the user story. Use semantic similarity, related_stories, and content. When possible, estimate this as if you were using cosine similarity between vector embeddings of the stories.\n"
            "2. For every test case, calculate a 'relation percentage' (0-100) to its own user story, using semantic similarity and relevance. Again, estimate this as if you were using cosine similarity between the test case and the user story embeddings.\n\n"
            "Return your answer as a JSON object with two keys:\n"
            "  'user_story_relations': {story_number: {other_story_number: percentage, ...}, ...}\n"
            "  'test_case_to_story_relations': {test_case_id: percentage, ...}\n\n"
            "Be concise and only output the JSON object.\n"
            "Here is the data:\n"),
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

def strip_code_blocks(text):
    """Remove code block markers from LLM output."""
    if text is None:
        return ''
    return text.replace('```json', '').replace('```', '').strip()

def analyze_risk(user_stories: list) -> str:
    """Analyze risk based on user stories."""
    formatted = "\n".join([
        f"{s['story_number']}: Persona {s.get('user_persona', '')} | Story: {s.get('user_story', '')} | Functionality: {s.get('functionality', 'N/A')} | Description: {s.get('description', '')}"
        for s in user_stories
    ])
    messages = [
        {
            "role": "system",
            "content": ("You are a risk analysis assistant. For each user story, assign a business Risk Factor value (proiority number) from 1 (highest priority) to 10 (lowest priority) based on:.\n"
                        "- the user persona (e.g is the persona is a case manager, that increases priority)\n"
                        "- the functionality field"
                        "Return a JSON array, one object per user story with the following fields:\n"
                        "story_number, user_story, User_persona, functionality, and Risk Factor value (priority number)."),
        },
        {
            "role": "user",
            "content": f"Analyze the following user stories for risk/priority:\n\n {formatted}",
        }
    ]
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages
    )
    return response.choices[0].message.content
   



class RequirementAgent(Agent):
    """Agent for analyzing requirements and writing results to the database and Neo4j."""
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
    """Agent for generating test cases for requirements and writing to the database."""
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
            for tc in test_cases:
                if 'story_number' not in tc:
                    if 'requirement_id' in tc:
                        tc['story_number'] = tc['requirement_id']
                    elif 'story_number' in batch[0]:
                        tc['story_number'] = batch[0]['story_number']
            all_test_cases.extend(test_cases)

       
        conn = connect_db()
        db_test_cases = []
        for tc in all_test_cases:
            db_test_cases.append({
                "requirement_id": tc.get('story_number'),
                "title": tc.get('title', ""),
                "test_case_description": tc.get('test_description', ""),
                "test_case_id": tc.get('test_case_id', ""),
            })
        if db_test_cases:
            insert_testcases(conn, db_test_cases)
        if conn:
            conn.close()
        return all_test_cases


class RelationAgent(Agent):
    """Agent for analyzing relations between user stories and test cases using LLM."""
    tools = [find_relations]
    memory = memory.Memory(memory="")

    def run(self, **kwargs):
        user_stories = kwargs["user_stories"]
        test_cases = kwargs["test_cases"]

        rel_output = find_relations(user_stories, test_cases)
        rel_output_clean = strip_code_blocks(rel_output)
        try:
            rel_output_dict = json.loads(rel_output_clean)
        except Exception as e:
            print(f"Error parsing relation agent output: {e}\nOutput was: {rel_output_clean}")
            return {}
        
        conn = connect_db()
        user_story_relations = rel_output_dict.get('user_story_relations', {})
        for story_number, relations in user_story_relations.items():
            upsert_central_vector(
                conn,
                story_number=story_number,
                source='relation_agent',
                title=None,
                description=None,
                user_persona=None,
                user_story=None,
                functionality=None,
                related_stories=[int(k) for k in relations.keys() if str(k).isdigit()],
                business_priority=None,
                agent_output=relations,
                embedding=None  # No embedding for relations
            )

        test_case_relations = rel_output_dict.get('test_case_to_story_relations', {})
        for test_case_id, percentage in test_case_relations.items():
            linked_story_number = None
            for tc in test_cases:
                if tc.get('test_case_id') == test_case_id:
                    linked_story_number = tc.get('story_number')
                    break
            upsert_central_vector(
                conn,
                story_number=linked_story_number,
                source='relation_agent_test_case',
                title=test_case_id,
                description=None,
                user_persona=None,
                user_story=None,
                functionality=None,
                related_stories=None,
                business_priority=None,
                agent_output={
                    "test_case_id": test_case_id,
                    "relation_percentage": percentage,
                    "linked_story_number": linked_story_number
                },
                embedding=None  # No embedding for relations
            )
        if conn:
            conn.close()
        return rel_output_dict
    

class RiskAgent(Agent):
    """Agent for analyzing risk and business priority for user stories."""
    tools = [analyze_risk]
    memory = memory.Memory(memory="")

    def run(self, **kwargs):
        user_stories = kwargs["user_stories"]
        risk_output = analyze_risk(user_stories)
        risk_output_clean = strip_code_blocks(risk_output)
        try:
            risk_output_list = json.loads(risk_output_clean)
        except Exception as e:
            print(f"Error parsing risk agent output: {e}\nOutput was: {risk_output_clean}")
            return []

        # Upsert risk analysis to the database
        conn = connect_db()
        for risk in risk_output_list:
            upsert_central_vector(
                conn,
                story_number=risk.get('story_number'),
                source='risk_agent',
                title=None,
                description=None,
                user_persona=risk.get('user_persona'),
                user_story=risk.get('user_story'),
                functionality=risk.get('functionality'),
                related_stories=None,
                business_priority=str(risk.get('business_priority')),
                agent_output=risk,
                embedding=None  # No embedding for risk analysis
            )
        if conn:
            conn.close()
        return risk_output_list

# --- Utility Functions ---
def get_requirements_from_kg():
    """Fetch requirements from the Neo4j knowledge graph."""
    results = graph.query("MATCH (r:Requirement) RETURN r")
    return [record['r'] for record in results]

def batch_upsert_requirements_to_neo4j(requirements, embeddings, batch_size=1):
    """Batch upsert requirements and their embeddings to Neo4j."""
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

# --- Main Workflow ---
if __name__ == "__main__":
    # Fetch raw requirements from the database
    raw_requirements = fetch_raw_requirements()

    # Run requirement analysis and write to database/KG
    req_agent = RequirementAgent()
    req_output_list = req_agent.run(raw_requirements=raw_requirements)
    #print(json.dumps(req_output_list, indent=2))

    # Fetch analyzed requirements from the database
    req_analysis = fetch_analyzed_requirements()

    # Run test case generation (batched)
    test_agent = TestAgent()
    test_output = test_agent.run(raw_requirements=raw_requirements, req_analysis=req_analysis)
    #print(json.dumps(test_output, indent=2))

    # Run relation analysis between user stories and test cases
    relation_agent = RelationAgent()
    relation_output = relation_agent.run(user_stories=req_analysis, test_cases=test_output)
    #print(json.dumps(relation_output, indent=2))

    # Run risk analysis on raw requirements
    risk_agent = RiskAgent()
    risk_output = risk_agent.run(user_stories=raw_requirements)
    print(json.dumps(risk_output, indent=2))

    # Upsert requirements to Postgres (central vector table)
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
