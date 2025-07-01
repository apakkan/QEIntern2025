import json
import os
import sys

# Ensure the main app directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpt_agent import (
    RequirementAgent,
    TestAgent,
    query_postgres,
    load_requirement_analysis,
    save_to_excel,
    strip_code_blocks,
)

def test_full_pipeline():
    # Step 1: Query requirements from the database
    rows = query_postgres("SELECT id as story_number, title as user_story, description FROM requirements")
    raw_requirements = [
        {"story_number": row[0], "user_story": row[1], "description": row[2]}
        for row in rows
    ]
    assert raw_requirements, "No requirements found in the database!"

    # Step 2: Run requirement analysis
    req_agent = RequirementAgent()
    req_output = req_agent.run(raw_requirements=raw_requirements)
    req_output_clean = strip_code_blocks(req_output)
    try:
        req_output_list = json.loads(req_output_clean)
    except Exception as e:
        print(f"Error parsing requirement agent output: {e}\nOutput was: {req_output_clean}")
        req_output_list = []
    assert req_output_list, "RequirementAgent did not return valid output!"

    save_to_excel(req_output_list, "test_output_req.xlsx")
    print("Requirement analysis output:", json.dumps(req_output_list, indent=2))

    # Step 3: Load requirement analysis from Excel
    req_analysis = load_requirement_analysis("test_output_req.xlsx")

    # Step 4: Run test case generation
    test_agent = TestAgent()
    test_output = test_agent.run(raw_requirements=raw_requirements, req_analysis=req_analysis)
    save_to_excel(test_output, "test_output_test_cases.xlsx")
    print("Test case generation output:", json.dumps(test_output, indent=2))

if __name__ == "__main__":
    test_full_pipeline()