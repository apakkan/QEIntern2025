import psycopg2
import os
from dotenv import load_dotenv
import time
import re

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        database=os.environ.get("POSTGRES_DB", "mydb"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        host=os.environ.get("POSTGRES_HOST", "qeintern2025_db"),
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
        
        # Drop the testcases table if it exists
        cur.execute('DROP TABLE IF EXISTS testcases;')
        
        # Create the testcases table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS testcases (
                id SERIAL PRIMARY KEY,
                requirement_id INTEGER REFERENCES requirements(id),
                title TEXT NOT NULL,
                description TEXT,
                steps TEXT,
                expected_result TEXT,
                coverage INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        print("Testcases table structure created/verified")
        
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
                    try:
                        # Extract basic fields
                        req_id = req.get('id')
                        user_story = req.get('name', '')
                        
                        # Extract properties from the properties list
                        properties = req.get('properties', [])
                        print("\nAll properties:")
                        for prop in properties:
                            print(f"Field: {prop.get('field_name')}, Value: {prop.get('field_value')}, Value Name: {prop.get('field_value_name')}")
                        
                        description = ''
                        functionality = ''
                        release = ''
                        priority = ''
                        project = ''  # Initialize project variable
                        
                        # Process each property in the list
                        for prop in properties:
                            field_name = prop.get('field_name')
                            print(f"\nProcessing field: {field_name}")
                            print(f"Raw property data: {prop}")
                            
                            if field_name == 'Description':
                                description = strip_html(prop.get('field_value', ''))
                            elif field_name == 'Type':
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
                            elif field_name == 'Sprint' or field_name == 'Release':
                                print(f"\nFound {field_name} field:")
                                print(f"Raw data: {prop}")
                                
                                # Try to get the value in this order:
                                # 1. field_value_name (display name)
                                # 2. field_value (actual value)
                                # 3. value (direct value)
                                release_value = None
                                
                                if prop.get('field_value_name'):
                                    release_value = prop.get('field_value_name')
                                    print(f"Using field_value_name: {release_value}")
                                elif prop.get('field_value'):
                                    release_value = prop.get('field_value')
                                    print(f"Using field_value: {release_value}")
                                elif prop.get('value'):
                                    release_value = prop.get('value')
                                    print(f"Using value: {release_value}")

                                if release_value and str(release_value).strip():
                                    release = str(release_value).strip()
                                    print(f"Set release to: {release}")
                                else:
                                    print(f"No valid release value found in property: {prop}")
                            elif field_name == 'Priority':
                                priority = prop.get('field_value_name', '')
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

                        print(f"\nFinal values for requirement {req_id}:")
                        print(f"User Story: {user_story[:100]}...")  # Show first 100 chars
                        print(f"Description: {description[:100]}...")
                        print(f"Functionality: {functionality}")
                        print(f"Release/Sprint: {release}")
                        print(f"Priority: {priority}")

                        if req_id is not None:
                            cur.execute('''
                                INSERT INTO requirements 
                                (id, user_story, description, functionality, release, priority, model, project)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (
                                req_id,
                                user_story,
                                description,
                                functionality,
                                release,
                                priority,
                                'OpenAI', 
                                project
                            ))
                            print(f"Inserted requirement ID: {req_id}")
                            print(f"Data: description={description}, functionality={functionality}, release={release}, priority={priority}")
                    except Exception as e:
                        print(f"Error processing requirement: {e}")
                        print(f"Raw requirement data: {req}")
                        continue
                
                conn.commit()
                print("Database changes committed")

def strip_html(text):
    return re.sub('<[^<]+?>', '', text) if text else text

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