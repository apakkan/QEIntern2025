import psycopg2
import os
from dotenv import load_dotenv
import time

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        database=os.environ.get("POSTGRES_DB", "mydb"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        host=os.environ.get("POSTGRES_HOST", "maindb"),
        port=os.environ.get("POSTGRES_PORT", "5432")
    )

def create_tables(conn):
    with conn.cursor() as cur:
        print("Creating/checking tables...")
        
        # Create the requirements table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS requirements (
                id INTEGER PRIMARY KEY,
                user_story TEXT,
                description TEXT,
                functionality TEXT,
                release TEXT,
                priority TEXT,
                model TEXT,
                project TEXT
            );
        ''')
        print("Table structure created/verified")
        
        # Check if table is empty
        cur.execute('SELECT COUNT(*) FROM requirements')
        count = cur.fetchone()[0]
        print(f"Current requirement count: {count}")
        
        if count == 0:
            print("Table is empty, fetching qTest data...")
            from database.qtest_db import get_qtest_requirements
            
            requirements = get_qtest_requirements()
            if requirements:
                for req in requirements:
                    # Debug the requirement structure
                    print(f"Processing requirement: {req}")
                    
                    # Safely extract values using dict.get() with default values
                    try:
                        req_id = req[0] if isinstance(req, list) else req.get('id', None)
                        user_story = req[1] if isinstance(req, list) else req.get('name', '')
                        description = req[2] if isinstance(req, list) else req.get('description', '')
                        
                        # Handle properties differently based on data structure
                        properties = req[3] if isinstance(req, list) else req.get('properties', {})
                        if isinstance(properties, dict):
                            functionality = properties.get('Functionality', '')
                            release = properties.get('Release', '')
                            priority = properties.get('Business Priority', '')
                        else:
                            functionality = ''
                            release = ''
                            priority = ''
                        
                        if req_id is not None:
                            cur.execute('''
                                INSERT INTO requirements 
                                (id, user_story, description, functionality, release, priority)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            ''', (
                                req_id,
                                user_story,
                                description,
                                functionality,
                                release,
                                priority
                            ))
                            print(f"Inserted requirement ID: {req_id}")
                    except Exception as e:
                        print(f"Error processing requirement: {e}")
                        continue
                
                conn.commit()
                print("Database changes committed")

def main():
    print("Starting database initialization...")
    print(f"Database settings:")
    print(f"DB: {os.environ.get('POSTGRES_DB', 'mydb')}")
    print(f"Host: {os.environ.get('POSTGRES_HOST', 'maindb')}")
    print(f"Port: {os.environ.get('POSTGRES_PORT', '5432')}")

    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"\nAttempting database connection (attempt {attempt + 1}/{max_retries})...")
            conn = get_db_connection()
            print("Database connection successful!")
            create_tables(conn)
            print("Database initialization complete")
            conn.close()
            return
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                raise e

if __name__ == "__main__":
    main()