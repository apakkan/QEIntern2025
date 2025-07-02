from app.public.qtest_db import connect_db, create_tables, get_qtest_requirements, insert_requirement

def main():
    conn = connect_db()
    if conn:
        create_tables(conn)
        requirements = get_qtest_requirements()
        if requirements:
            for req in requirements:
                insert_requirement(
                    conn,
                    req_id=req["id"],
                    title=req.get("name", "Untitled"),
                    description=req.get("description", ""),
                    status=req.get("status", "New")
                )
        conn.close()

def init_db():
    main()

if __name__ == "__main__":
    main()