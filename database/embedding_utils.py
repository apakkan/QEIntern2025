import os
import openai

def get_embedding(text):
    """
    Generate an embedding for the given text using Azure OpenAI.
    Requires these environment variables:
      - OPENAI_EMBEDDING_API_KEY
      - OPENAI_EMBEDDING_API_BASE
      - OPENAI_EMBEDDING_API_VERSION
      - OPENAI_EMBEDDING_DEPLOYMENT
    """
    client = openai.AzureOpenAI(
        api_key=os.environ["OPENAI_EMBEDDING_API_KEY"],
        api_version=os.environ["OPENAI_EMBEDDING_API_VERSION"],
        azure_endpoint=os.environ["OPENAI_EMBEDDING_API_BASE"]
    )
    response = client.embeddings.create(
        input=[text],
        model=os.environ["OPENAI_EMBEDDING_DEPLOYMENT"]
    )
    return response.data[0].embedding
