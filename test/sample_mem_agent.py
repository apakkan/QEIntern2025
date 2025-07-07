import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.azure import AzureOpenAI
from agno.storage.sqlite import SqliteStorage
from rich.pretty import pprint

# Load environment variables
load_dotenv()

DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")
API_KEY = os.getenv("OPENAI_API_KEY")
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_VERSION = os.getenv("OPENAI_API_VERSION")

user_id = "ava"
db_file = "tmp/agent.db"

# Make sure the tmp directory exists
os.makedirs("tmp", exist_ok=True)

# Initialize memory.v2 with Azure OpenAI
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

memory_agent = Agent(
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
)

if __name__ == "__main__":
    memory.clear()
    print("Start chatting with the memory agent! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            print("Goodbye!")
            break
        try:
            reply = memory_agent.run(
                user_input,
                user_id=user_id,
            )
            print("Agent:", reply)
            print("Memories about Ava:")
            pprint(memory.get_user_memories(user_id=user_id))
        except Exception as e:
            print(f"Error: {e}")