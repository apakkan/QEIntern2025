import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from dotenv import load_dotenv
from tools.db_tools import query_postgres_tool
from init_db import main as init_db

load_dotenv()


@pytest.mark.integration
def test_agent_query():
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
    assert response is not None, "Agent returned no response"
    print(response)
