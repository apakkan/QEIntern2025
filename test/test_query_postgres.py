from init_db import main as init_db_main
from tools.db_tools import query_postgres

def main():
    # Initialize DB (create tables and insert sample data)
    init_db_main()

    sql = "SELECT id, title, status FROM requirements;" # USE LIMIT X to see X values
    results = query_postgres(sql)
    print("Results from query_postgres:")
    for row in results:
        print(row)

if __name__ == "__main__":
    main()