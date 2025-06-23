import json
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import pandas as pd
from agno.agent import Agent
from agno.tools import tool
from agno import memory


load_dotenv()

API_KEY = os.getenv("API_KEY")
API_VERSION = os.getenv("API_VERSION")
ENDPOINT = os.getenv("ENDPOINT")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")

client = AzureOpenAI(
    api_version=API_VERSION,
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
)

def load_requirements(file_path="requirements.xlsx"):
    df = pd.read_excel(file_path)
    return df[['story_number', 'user_story','description']].dropna().to_dict(orient='records')


def refine_requirement(raw_requirement: list) -> list:
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
    formatted = "\n".join([
        f"{s['story_number']}: {s['user_story']} - {s['description']}"
        for s in raw_requirement
    ])
    messages = [
        {
            "role": "system",
            "content": ("You are a quality engineer and testing. For each story below, return:\n"
                        "- story_number: the story number\n"
                        "- test_cases: list of suggested test cases\n"
                        "- edge_cases: edge or tricky inputs\n"
                        "- testability: yes/no and explanation\n\n"
                        "Respond in JSON array format, one object per story, and include the story_number in each object.")
         },
        { "role": "user", "content": formatted }
    ]
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages
    )
    return response.choices[0].message.content


def save_to_excel(json_output, path="output.xlsx"):
    data = json.loads(json_output)
    df = pd.DataFrame(data)
    df.to_excel(path, index=False)
    print(f"Output saved to {path}")

class RequirementAgent(Agent):
    tools = [refine_requirement]
    memory = memory.Memory(memory="")

    def run(self, **kwargs):
        raw_requirements = kwargs["raw_requirements"]
        return refine_requirement(raw_requirements)


class TestAgent(Agent):
    tools = [generate_test_cases_tool]
    memory = memory.Memory(memory="")
    
    def run(self, **kwargs):
        raw_requirements = kwargs["raw_requirements"]
        return generate_test_cases_tool(raw_requirements)


if __name__ == "__main__":
    raw_requirements = load_requirements("requirements.xlsx")


    req_agent = RequirementAgent()
    req_output = req_agent.run(raw_requirements=raw_requirements)

    save_to_excel(req_output, "output_req.xlsx")
    parsed = json.loads(req_output)

    test_agent = TestAgent()
    test_output = test_agent.run(raw_requirements=raw_requirements)

    save_to_excel(test_output, "output_test.xlsx")
    parsed_test = json.loads(test_output)


    for story in parsed:
        print(f"Story #{story['story_number']}")
        print(f"  Functionality: {story['functionality']}")
        print(f"  Related stories: {story['related_stories']}")
        print("-" * 40)

    print("\nTest Cases Output:\n" + "="*40)
    for story in parsed_test:
        print(f"Story #{story.get('story_number')}")
        print(f"  Test cases: {story.get('test_cases', 'N/A')}")
        print(f"  Edge cases: {story.get('edge_cases', 'N/A')}")
        print(f"  Testability: {story.get('testability', 'N/A')}")
        print("-" * 40)