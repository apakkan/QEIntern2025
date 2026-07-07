"""Characterization tests for the Azure OpenAI -> Mistral provider migration (commit bbf200b).

The migrated code already exists, so these lock in the intended behavior (they would
fail against the old AzureOpenAI construction). LLM-free: building an openai.OpenAI
client makes no network call, so we only assert how the client is configured.
"""
import importlib

import openai

import gpt_agent
import database.embedding_utils as embedding_utils
import database.qtest_db as qtest_db


def test_gpt_agent_client_is_plain_openai_at_configured_endpoint(monkeypatch):
    monkeypatch.setenv("API_KEY", "chat-key-123")
    monkeypatch.setenv("ENDPOINT", "https://api.mistral.ai/v1")
    gpt_agent._get_client.cache_clear()
    try:
        client = gpt_agent._get_client()
        assert isinstance(client, openai.OpenAI)
        assert not isinstance(client, openai.AzureOpenAI)  # migrated off Azure
        assert client.api_key == "chat-key-123"
        assert str(client.base_url).rstrip("/") == "https://api.mistral.ai/v1"
    finally:
        gpt_agent._get_client.cache_clear()  # drop the test-configured client


def test_gpt_agent_client_is_cached():
    gpt_agent._get_client.cache_clear()
    try:
        assert gpt_agent._get_client() is gpt_agent._get_client()
    finally:
        gpt_agent._get_client.cache_clear()


def test_embedding_client_is_plain_openai_at_configured_base(monkeypatch):
    monkeypatch.setenv("OPENAI_EMBEDDING_API_KEY", "emb-key-9")
    monkeypatch.setenv("OPENAI_EMBEDDING_API_BASE", "https://api.mistral.ai/v1")
    embedding_utils._client = None
    try:
        client = embedding_utils.get_openai_client()
        assert isinstance(client, openai.OpenAI)
        assert not isinstance(client, openai.AzureOpenAI)
        assert client.api_key == "emb-key-9"
        assert str(client.base_url).rstrip("/") == "https://api.mistral.ai/v1"
        assert embedding_utils.get_openai_client() is client  # cached per process
    finally:
        embedding_utils._client = None  # force real client rebuild for other tests


def test_embedding_dim_is_env_configurable(monkeypatch):
    # Was hardcoded 1536 pre-migration; now int(os.getenv("OPENAI_EMBEDDING_DIM","1536")).
    monkeypatch.setenv("OPENAI_EMBEDDING_DIM", "768")
    try:
        importlib.reload(qtest_db)
        assert qtest_db.OPENAI_EMBEDDING_DIM == 768
    finally:
        monkeypatch.delenv("OPENAI_EMBEDDING_DIM", raising=False)
        importlib.reload(qtest_db)  # restore to the .env/default value
