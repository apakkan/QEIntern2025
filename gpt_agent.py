# Imports and environment setup
import json
import os
from openai import AzureOpenAI as OpenAIAzureClient
from dotenv import load_dotenv
import pandas as pd
from agno.agent import Agent
from agno.tools import tool
from agno import memory
from agno.models.azure import AzureOpenAI as AgnoAzureModel
import sys
#sys.path.append('/home/azureuser/main/QEIntern2025')
from tools.db_tools import query_postgres, vector_search_tool, query_postgres_tool

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

def load_requirements(file_path="requirements.xlsx"):
    """Load requirements from Excel and return as list of dicts."""
    df = pd.read_excel(file_path)
    return df[['story_number', 'user_story','description']].dropna().to_dict(orient='records')

def load_requirement_analysis(file_path="output_req.xlsx"):
    """Load requirement analysis from Excel and return as list of dicts."""
    df = pd.read_excel(file_path)
    return df.to_dict(orient='records')

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
            "content": ("You are a quality engineer and testing. For each story below, return:\n"
                        "- story_number: the story number\n"
                        "- test_cases: list of suggested test cases\n"
                        "- edge_cases: edge or tricky inputs\n"
                        "- shared_tests: any tests that apply to its related stories\n"
                        "- regression_impact: feature/stories that should be retested if this changes\n\n"
                        "Make sure to analyze related stories and functionality groups. If multiple stories share functioality reflect that in shared_tests\n"
                        "Respond in JSON array format, one object per story, and include the story_number in each object."),
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

def save_to_excel(json_output, path="output.xlsx"):
    """Save a list/dict or JSON string to Excel."""
    if isinstance(json_output, str):
        try:
            data = json.loads(json_output)
        except Exception as e:
            print(f"Error parsing JSON: {e}\nInput: {json_output}")
            return
    else:
        data = json_output
    if not isinstance(data, (list, dict)):
        print(f"Output is not a list or dict: {type(data)}")
        return
    df = pd.DataFrame(data)
    df.to_excel(path, index=False)
    print(f"Output saved to {path}")

class RequirementAgent(Agent):
    tools = [refine_requirement]
    memory = memory.Memory(memory="")

    def run(self, **kwargs):
        """Run requirement analysis using the LLM."""
        raw_requirements = kwargs["raw_requirements"]
        return refine_requirement(raw_requirements)


class TestAgent(Agent):
    tools = [generate_test_cases_tool]
    memory = memory.Memory(memory="")

    def run(self, **kwargs):
        """Run test case generation in batches to avoid LLM truncation."""
        raw_requirements = kwargs["raw_requirements"]
        req_analysis = kwargs["req_analysis"]

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
            def strip_code_blocks(text):
                if text.strip().startswith('```'):
                    return '\n'.join(line for line in text.splitlines() if not line.strip().startswith('```'))
                return text
            cleaned = strip_code_blocks(llm_output)
            try:
                test_cases = json.loads(cleaned)
            except Exception as e:
                print(f"Error parsing LLM output: {e}\nOutput: {llm_output}")
                continue
            all_test_cases.extend(test_cases)

        return all_test_cases

if __name__ == "__main__":
    # Load requirements from Excel
    rows = query_postgres("SELECT id as story_number, title as user_story, description FROM requirements")
    raw_requirements = [
        {"story_number": row[0], "user_story": row[1], "description": row[2]}
        for row in rows
    ]

    # Run requirement analysis
    req_agent = RequirementAgent()
    req_output = req_agent.run(raw_requirements=raw_requirements)

    # Always parse and save as list of dicts
    req_output_clean = strip_code_blocks(req_output)
    try:
        req_output_list = json.loads(req_output_clean)
    except Exception as e:
        print(f"Error parsing requirement agent output: {e}\nOutput was: {req_output_clean}")
        req_output_list = []
    save_to_excel(req_output_list, "output_req.xlsx")
    print(json.dumps(req_output_list, indent=2))

    # Load requirement analysis from Excel
    req_analysis = load_requirement_analysis("output_req.xlsx")

    # Run test case generation (batched)
    test_agent = TestAgent()
    test_output = test_agent.run(raw_requirements=raw_requirements, req_analysis=req_analysis)
    save_to_excel(test_output, "output_test_cases.xlsx")
    print(json.dumps(test_output, indent=2))


    # Example agent with query_postgres_tool
    agent = Agent(
        tools=[query_postgres_tool],  # Register your tool
        model=azure_model,            # Use Azure OpenAI for agent reasoning
    )
    response = agent.run("Show me the first 5 requirements from the database.")
    print(response)

