import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.azure import AzureOpenAI
from agno.storage.sqlite import SqliteStorage
from rich.pretty import pprint
from langchain_neo4j import Neo4jGraph
from tools.db_tools import query_postgres

# Load environment variables
load_dotenv()

DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")
API_KEY = os.getenv("OPENAI_API_KEY")
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("OPENAI_API_VERSION")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

user_id = "ava"
db_file = "tmp/integration_agent.db"
os.makedirs("tmp", exist_ok=True)

# Set up memory
memory = Memory(
    model=AzureOpenAI(
        id=DEPLOYMENT_NAME,
        api_key=API_KEY,
        azure_endpoint=ENDPOINT,
        azure_deployment=DEPLOYMENT_NAME,
        api_version=API_VERSION,
    ),
    db=SqliteMemoryDb(table_name="user_memories", db_file=db_file),
)
storage = SqliteStorage(table_name="agent_sessions", db_file=db_file)

# Set up Neo4j
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)

# Tool: Query Neo4j
def query_neo4j(query):
    """
    Run a Cypher query on the Neo4j knowledge graph and return the results.
    Usage: query_neo4j("MATCH (n) RETURN n LIMIT 5")
    """
    try:
        results = graph.query(query)
        return str(results)
    except Exception as e:
        return f"Neo4j error: {e}"

# Tool: Query Postgres
def query_pg(sql):
    """
    Run a SQL query on the Postgres database and return the results.
    Usage: query_pg("SELECT * FROM requirements LIMIT 5")
    """
    try:
        rows = query_postgres(sql)
        return str(rows)
    except Exception as e:
        return f"Postgres error: {e}"

integration_agent = Agent(
    model=AzureOpenAI(
        id=DEPLOYMENT_NAME,
        api_key=API_KEY,
        azure_endpoint=ENDPOINT,
        azure_deployment=DEPLOYMENT_NAME,
        api_version=API_VERSION,
    ),
    memory=memory,
    enable_agentic_memory=True,
    enable_user_memories=True,
    storage=storage,
    add_history_to_messages=True,
    num_history_runs=3,
    markdown=True,
    tools=[query_neo4j, query_pg],
)

integration_agent.system_prompt = (
    "You are an assistant with access to user memory, a Neo4j knowledge graph, and a Postgres database. "
    "Use all available information to answer questions or perform tasks. "
    "You can recall user memories, run Cypher queries on Neo4j, and SQL queries on Postgres."
)

if __name__ == "__main__":
    print(f"Using user_id: {user_id}")  # <-- Add this line
    # memory.clear()
    print("Start chatting with the integration agent! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            print("Goodbye!")
            break
        if not user_input.strip():
            print("Please enter a message.")
            continue
        try:
            reply = integration_agent.run(
                user_input,
                user_id=user_id,
            )
            print("Agent:", reply.content)
            print("Memories about User:")
            pprint(memory.get_user_memories(user_id=user_id))
        except Exception as e:
            print(f"Error: {e}")