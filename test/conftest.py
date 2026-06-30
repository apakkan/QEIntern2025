import os
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: requires live infrastructure (PostgreSQL, Neo4j, Azure OpenAI)",
    )


def pytest_collection_modifyitems(config, items):
    infra_present = all([
        os.getenv("POSTGRES_HOST"),
        os.getenv("NEO4J_URI"),
        os.getenv("API_KEY"),
    ])
    if not infra_present:
        skip = pytest.mark.skip(
            reason="integration test skipped — set POSTGRES_HOST, NEO4J_URI, API_KEY to run"
        )
        for item in items:
            if item.get_closest_marker("integration"):
                item.add_marker(skip)
