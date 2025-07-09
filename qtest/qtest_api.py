import os
import requests
from dotenv import load_dotenv

load_dotenv()

FIELD_ID_MAP = {
    "description": 12631987,
    "status": 12631994,
}

STATUS_VALUE_MAP = {
    "New": "911",
    "In Progress": "912",
    "Baselined": "913",
    "Approved": "914",
    "Rejected": "915",
}

def create_qtest_requirement(conn, title, description):
    url = os.environ["QTEST_API_URL"].replace("/test-cases", "/requirements")
    api_key = os.environ["QTEST_API_KEY"]
    parent_id = int(os.environ["QTEST_REQUIREMENTS_PARENT_ID"])
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "name": title,
        "description": description,
        "parent_id": parent_id
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in (200, 201):
        qtest_req = response.json()
        print("Requirement created in qTest:", qtest_req)
        # Extract description from response or fallback to input
        desc = qtest_req.get("description")
        if desc is None:
            # Try to find description in properties
            desc = ""
            for prop in qtest_req.get("properties", []):
                if prop.get("field_name", "").lower() == "description":
                    desc = prop.get("field_value_name") or prop.get("field_value") or ""
                    break
        # Insert into local DB with status "New"
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Requirements (id, title, description, status) VALUES (%s, %s, %s, %s)",
            (qtest_req["id"], qtest_req["name"], desc, "New")
        )
        conn.commit()
        cursor.close()
        print("Requirement inserted into local DB.")
        return qtest_req
    else:
        print(f"Failed to create requirement in qTest: {response.status_code} {response.text}")
        return None

def create_qtest_testcase(conn, name, description, requirement_id=None):
    url = os.environ["QTEST_API_URL"]
    api_key = os.environ["QTEST_API_KEY"]
    parent_id = int(os.environ["QTEST_TESTCASES_PARENT_ID"])
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "name": name,
        "description": description,
        "parent_id": parent_id
    }
    if requirement_id:
        payload["linked_requirements"] = [requirement_id]
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in (200, 201):
        qtest_tc = response.json()
        print("Test case created in qTest:", qtest_tc)
        # Insert into local DB (store qTest ID for reference)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO TestCases (id, requirement_id, title, description) VALUES (%s, %s, %s, %s)",
            (qtest_tc["id"], requirement_id or 1, qtest_tc["name"], qtest_tc["description"])
        )
        conn.commit()
        cursor.close()
        print("Test case inserted into local DB.")
        return qtest_tc
    else:
        print(f"Failed to create test case in qTest: {response.status_code} {response.text}")
        return None

def process_properties(user_story, properties):
    functionality = ""
    project = ""
    for prop in properties:
        field_name = prop.get('field_name', '')
        if field_name == 'Type':
            functionality_type = prop.get('field_value_name', '')
            # Map functionality based on user story content
            if 'application intake' in user_story.lower():
                functionality = 'Application Intake'
            elif 'eligibility' in user_story.lower():
                functionality = 'Eligibility Verification'
            elif 'document' in user_story.lower() or 'upload' in user_story.lower():
                functionality = 'Document Management'
            elif 'notification' in user_story.lower() or 'alert' in user_story.lower():
                functionality = 'Notifications'
            elif 'report' in user_story.lower():
                functionality = 'Reporting'
            elif 'case' in user_story.lower():
                functionality = 'Case Management'
            else:
                functionality = functionality_type
            print(f"Set functionality to: {functionality}")
        elif field_name == 'Project':  # Add this new section
            project_value = prop.get('field_value_name') or prop.get('field_value', '')
            if project_value:
                project = project_value.strip()
                print(f"Set project to: {project}")
            else:
                # Map project based on user story content or set default
                if 'CDSS' in user_story:
                    project = 'CDSS'
                elif 'CBMS' in user_story:
                    project = 'CBMS'
                else:
                    project = 'Core System'  # Default project
            print(f"Set project to: {project}")
    return functionality, project


