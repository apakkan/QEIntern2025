import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from dotenv import load_dotenv
from init_db import main as init_db_main
from tools.db_tools import query_postgres

load_dotenv()


@pytest.mark.integration
def test_query_postgres():
    init_db_main()

    sql = "SELECT id, title, status FROM requirements;"
    results = query_postgres(sql)
    assert results is not None, "query_postgres returned None"
    print("Results from query_postgres:")
    for row in results:
        print(row)
