from qtest_db import connect_db, create_tables, insert_requirement, get_qtest_data
from rag_utils import insert_refined_requirement

def main():
    conn = connect_db()
    create_tables(conn)

    # Load requirements from qTest
    requirements = get_qtest_data()
    if requirements:
        for req in requirements:
            insert_requirement(
                conn,
                req_id=req["id"],
                title=req.get("name", "Untitled"),
                description=req.get("description", ""),
                status=req.get("status", "New")
            )

    # Manually insert your own requirement (if needed)
    insert_requirement(
        conn,
        req_id=1,
        title="Upload a File",
        description="User can upload a file to the system.",
        status="In Progress"
    )
    print("Inserted Sample Requirement")

    # 2. Insert a refined version of that requirement
    insert_refined_requirement(
        conn,
        requirement_id=1,
        user_persona="QA Engineer",
        user_story="As a QA, I want to upload files...",
        functionality="File upload",
        refined_description="Detailed steps for file upload",
        release="v1.0",
        related_story="Story-123",
        business_priority="High",
        embedding=[0.1] * 1536  # Example embedding
    )
    print("Inserted Sample Refined Requirement")

    conn.close()

if __name__ == "__main__":
    main()