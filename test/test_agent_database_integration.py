import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from gpt_agent import RequirementAgent, TestAgent, query_postgres


@pytest.mark.integration
def test_full_pipeline():
    # Step 1: Query requirements from the database
    rows = query_postgres("SELECT id as story_number, title as user_story, description FROM requirements")
    raw_requirements = [
        {"story_number": row[0], "user_story": row[1], "description": row[2]}
        for row in rows
    ]
    assert raw_requirements, "No requirements found in the database!"

    # Step 2: Run requirement analysis (returns a parsed list directly)
    req_agent = RequirementAgent()
    req_output_list = req_agent.run(raw_requirements=raw_requirements)
    assert req_output_list, "RequirementAgent did not return valid output!"
    print("Requirement analysis output:", json.dumps(req_output_list, indent=2))

    # Step 3: Run test case generation
    test_agent = TestAgent()
    test_output = test_agent.run(raw_requirements=raw_requirements, req_analysis=req_output_list)
    assert test_output, "TestAgent did not return valid output!"
    print("Test case generation output:", json.dumps(test_output, indent=2))
