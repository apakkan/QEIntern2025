from agno.agent import Agent
from agno.models.azure import AzureOpenAI
import os
from dotenv import load_dotenv
from tools.db_tools import query_postgres_tool

# Import the init_db function
from init_db import main as init_db

load_dotenv()

# Initialize the database before running the agent
init_db()

azure_model = AzureOpenAI(
    id="gpt-4.1",
    api_key=os.getenv("API_KEY"),
    azure_endpoint=os.getenv("ENDPOINT"),
    azure_deployment=os.getenv("DEPLOYMENT_NAME"),
    api_version=os.getenv("API_VERSION"),
)

agent = Agent(
    tools=[query_postgres_tool],
    model=azure_model,
    markdown=True
)

response = agent.run("Show me the first 5 requirements from the database.")
print(response)