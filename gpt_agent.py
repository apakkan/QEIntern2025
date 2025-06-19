import json
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import pandas as pd


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


def refine_requirement(raw_requirement):
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

def save_to_excel(json_output, path="output.xlsx"):
    data = json.loads(json_output)
    df = pd.DataFrame(data)
    df.to_excel(path, index=False)
    print(f"Output saved to {path}")




if __name__ == "__main__":
    requirements = load_requirements("requirements.xlsx")
    response_json = refine_requirement(requirements)
    print(response_json)
    save_to_excel(response_json, "output.xlsx")
