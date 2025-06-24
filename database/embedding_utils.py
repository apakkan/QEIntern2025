import os
import openai

# ==== Module-level cache for the OpenAI client ====
_client = None  # Ensures the client is only initialized once per process

def get_openai_client():
    """
    Lazily initialize and return a cached Azure OpenAI client.
    Uses environment variables for configuration.
    """
    global _client
    if _client is None:
        # Initialize the Azure OpenAI client with credentials from environment variables
        _client = openai.AzureOpenAI(
            api_key=os.environ["OPENAI_EMBEDDING_API_KEY"],
            api_version=os.environ["OPENAI_EMBEDDING_API_VERSION"],
            azure_endpoint=os.environ["OPENAI_EMBEDDING_API_BASE"]
        )
    return _client

def get_embedding(text):
    """
    Generate an embedding vector for the given text using Azure OpenAI.
    
    Args:
        text (str): The input text to embed.
    
    Returns:
        list[float]: The embedding vector for the input text.
    """
    client = get_openai_client()
    # Request embedding from Azure OpenAI deployment
    response = client.embeddings.create(
        input=[text],
        model=os.environ["OPENAI_EMBEDDING_DEPLOYMENT"]
    )
    # Return the embedding vector from the response
    return response.data[0].embedding
