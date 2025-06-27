from dotenv import load_dotenv
load_dotenv()

from init_db import main as init_db_main

def main():
    # Initialize DB (create tables and insert sample data)
    init_db_main()
    print("DB initialized. Add your API tests here.")

if __name__ == "__main__":
    main()