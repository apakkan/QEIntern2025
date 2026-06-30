import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from dotenv import load_dotenv
from init_db import main as init_db_main

load_dotenv()


@pytest.mark.integration
def test_api_db_init():
    init_db_main()
    # If init_db_main() raises, the test fails; reaching here means the DB
    # initialized without error.
    assert True, "DB initialization failed"
