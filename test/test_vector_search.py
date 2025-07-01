from dotenv import load_dotenv
load_dotenv()

from init_db import main as init_db_main
from tools.db_tools import vector_search_tool

def main():
    # Initialize DB (create tables and insert sample data)
    init_db_main()

    query = "Verify applicant identity using government id"
    top_k = 3
    results = vector_search_tool(query, top_k)
    print("\nTest Vector Search Results:")
    for r in results:
        print(f"ID: {r['id']}, Title: {r['title']}, Distance: {r['distance']}")

if __name__ == "__main__":
    main()