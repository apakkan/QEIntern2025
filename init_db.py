from database.qtest_db import (
    connect_db,
    create_tables,
    get_qtest_requirements,
    insert_requirement,
    map_qtest_requirement,
)

def main():
    conn = connect_db()
    if conn:
        create_tables(conn)
        requirements = get_qtest_requirements()
        if requirements:
            for req in requirements:
                # Real content (description/status/priority/sprint) lives in the
                # qTest item's properties[]; map_qtest_requirement extracts it so
                # we ingest usable requirements, not title-only shells.
                mapped = map_qtest_requirement(req)
                insert_requirement(
                    conn,
                    req_id=req["id"],
                    title=mapped["title"],
                    description=mapped["description"],
                    status=mapped["status"],
                    priority=mapped["priority"],
                    sprint=mapped["sprint"],
                )
        conn.close()

def init_db():
    main()

if __name__ == "__main__":
    main()