import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from dotenv import load_dotenv
from init_db import main as init_db_main
from tools.db_tools import vector_search_tool

load_dotenv()


@pytest.mark.integration
def test_vector_search():
    init_db_main()

    query = "Verify applicant identity using government id"
    top_k = 3
    results = vector_search_tool(query, top_k)
    assert results is not None, "vector_search_tool returned None"
    print("\nTest Vector Search Results:")
    for r in results:
        print(f"ID: {r['id']}, Title: {r['title']}, Distance: {r['distance']}")
