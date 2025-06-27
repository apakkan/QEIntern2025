import os
import psycopg2
from langchain_openai import OpenAIEmbeddings
from langchain_neo4j import Neo4jGraph
from dotenv import load_dotenv
import numpy as np

load_dotenv()

embedding_provider = OpenAIEmbeddings(
    openai_api_key=os.getenv('OPENAI_EMBEDDING_API_KEY'),
    azure_endpoint=os.getenv('OPENAI_EMBEDDING_API_BASE'),
    azure_deployment=os.getenv('OPENAI_EMBEDDING_DEPLOYMENT'),
    azure_api_version=os.getenv('OPENAI_EMBEDDING_API_VERSION')
)

# Neo4j connection
graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USERNAME'),
    password=os.getenv('NEO4J_PASSWORD')
)

# Postgres connection
def get_pg_conn():
    return psycopg2.connect(
        database=os.environ.get("POSTGRES_DB", "mydb"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        host=os.environ.get("POSTGRES_HOST", "maindb"),
        port=os.environ.get("POSTGRES_PORT", "5432")
    )

def fetch_central_vectors():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT story_number, source, title, description, user_persona, user_story,
               functionality, related_stories, business_priority, agent_output, embedding
        FROM central_vectors
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def to_py_vector(pg_vector):
    if pg_vector is None:
        return None
    if isinstance(pg_vector, memoryview):
        return np.frombuffer(pg_vector, dtype=np.float32).tolist()
    if isinstance(pg_vector, np.ndarray):
        return pg_vector.tolist()
    if isinstance(pg_vector, list):
        return pg_vector
    # If it's a string (shouldn't be), try to parse
    try:
        import ast
        return ast.literal_eval(pg_vector)
    except Exception:
        return None

records = fetch_central_vectors()
for rec in records:
    (
        story_number, source, title, description, user_persona, user_story,
        functionality, related_stories, business_priority, agent_output, embedding
    ) = rec

    # Convert embedding to list of floats if needed
    embedding = to_py_vector(embedding)

    if embedding is None or not isinstance(embedding, list) or len(embedding) == 0:
        print(f"Skipping story_number {story_number}: invalid embedding")
        continue

    # Choose label based on source, or always use Requirement
    label = "Requirement" if source == "requirement_agent" else "RawRequirement"
    properties = {
        "story_number": story_number,
        "source": source,
        "title": title,
        "description": description,
        "user_persona": user_persona,
        "user_story": user_story,
        "functionality": functionality,
        "related_stories": related_stories,
        "business_priority": business_priority,
        "agent_output": str(agent_output) if agent_output else None
    }
    # Remove None values for Cypher
    properties = {k: v for k, v in properties.items() if v is not None}
    # Insert node and embedding
    graph.query(f"""
        MERGE (r:{label} {{story_number: $story_number}})
        SET r += $properties
        WITH r
        CALL db.create.setNodeVectorProperty(r, 'textEmbedding', $embedding)
    """, {"story_number": story_number, "properties": properties, "embedding": embedding})

# Create the vector index (if not exists)
graph.query("""
    CREATE VECTOR INDEX `requirementVector`
    IF NOT EXISTS
    FOR (r:Requirement) ON (r.textEmbedding)
    OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
    }};""")