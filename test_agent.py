
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

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

user_story = input("Enter a user story to generate test cases: ")

# Generate test cases
def generate_test_cases(story_text):
    messages = [
        {
            "role": "system",
            "content": "You are a test case generator. Generate test cases based on the user story provided."
        },
        {
            "role": "user",
            "content": f"User Story: {story_text}n\nTest Cases:"

        }
    ]
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages
    )
    return response.choices[0].message.content

#Generate and print test cases
test_cases = generate_test_cases(user_story)
print("\nGenerated Test Cases:\n")
print(test_cases)

