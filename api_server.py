from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
import logging
from database.embedding_utils import get_embedding
from database.rag_utils import find_related_requirements
from init_db import create_tables
from gpt_agent import TestAgent, RelationAgent  # Add RelationAgent import

app = FastAPI()

# Set up logging at the top of the file
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#middle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://20.75.85.193:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],  # Add POST here
    allow_headers=["*"],
)

def get_pg_conn():
    try:
        conn = psycopg2.connect(
            database=os.environ.get("POSTGRES_DB", "mydb"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
            host=os.environ.get("POSTGRES_HOST", "qeintern2025_db"),
            port=os.environ.get("POSTGRES_PORT", "5432")
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

@app.get("/")
async def root():
    try:
        logger.info("Root endpoint called")
        conn = get_pg_conn()
        cur = conn.cursor()
        
        # Check if requirements table exists instead of refinedrequirements
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'requirements'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        logger.info(f"Table exists: {table_exists}")
        
        row_count = 0
        if table_exists:
            cur.execute("SELECT COUNT(*) FROM requirements")
            row_count = cur.fetchone()[0]
            logger.info(f"Row count: {row_count}")
            
        cur.close()
        conn.close()
        
        return {
            "status": "ok", 
            "database_initialized": table_exists,
            "requirement_count": row_count
        }
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

# Update the /requirements/ endpoint query
@app.get("/requirements/")
async def get_requirements():
    try:
        conn = get_pg_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                r.id,
                r.user_story,
                r.description,
                r.functionality,
                COALESCE(r.sprint, 'Not Set') as sprint,
                CASE
                    WHEN r.priority = 'High' THEN '10'
                    WHEN r.priority = 'Medium' THEN '5'
                    WHEN r.priority = 'Low' THEN '1'
                    ELSE 'Not Assessed'
                END as risk_score
            FROM requirements r
        """)
        
        rows = cur.fetchall()
        requirements = []
        for row in rows:
            risk_score = row[5]
            if risk_score.isdigit():
                risk_score = int(risk_score)
                
            requirement = {
                "id": row[0],
                "user_story": row[1] or "",
                "description": row[2] or "",
                "functionality": row[3] or "",
                "release": row[4], 
                "risk_score": risk_score,
                "model": "OpenAI",
                "project": "Project 1"
            }
            requirements.append(requirement)
        
        return requirements

    except Exception as e:
        logger.error(f"Error fetching requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.post("/requirements/")
async def create_requirement(requirement: dict):
    conn = get_pg_conn()
    cur = conn.cursor()
    try:
        # Align to the actual requirements schema: title (NOT NULL), user_story,
        # description, functionality, sprint, priority, status. The API's
        # "release" field maps to the real "sprint" column; "model"/"project"
        # have no columns and are not persisted.
        cur.execute("""
            INSERT INTO requirements
            (id, title, user_story, description, functionality, sprint, priority, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            requirement['id'],
            requirement.get('title') or requirement.get('user_story') or 'Untitled',
            requirement.get('user_story'),
            requirement.get('description'),
            requirement.get('functionality'),
            requirement.get('release') or requirement.get('sprint'),
            requirement.get('priority'),
            requirement.get('status'),
        ))
        requirement_id = cur.fetchone()[0]
        conn.commit()
        
        logger.info(f"Requirement created with ID: {requirement_id}")
        return {**requirement, "id": requirement_id}
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating requirement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/requirements/{requirement_id}")
async def get_requirement(requirement_id: int):
    try:
        conn = get_pg_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                r.id,
                r.user_story,
                r.description,
                r.functionality,
                COALESCE(r.sprint, 'Not Set') as release,
                CASE
                    WHEN r.priority = 'High' THEN '10'
                    WHEN r.priority = 'Medium' THEN '5'
                    WHEN r.priority = 'Low' THEN '1'
                    ELSE 'Not Assessed'
                END as risk_score
            FROM requirements r
            WHERE id = %s;
        """, (requirement_id,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Requirement not found")

        risk_score = row[5]
        if isinstance(risk_score, str) and risk_score.isdigit():
            risk_score = int(risk_score)

        requirement = {
            "id": row[0],
            "user_story": row[1] or "",
            "description": row[2] or "",
            "functionality": row[3] or "",
            "release": row[4] or "",
            "risk_score": risk_score,
            # model/project have no column in the schema; kept as constants to
            # preserve the API response shape the frontend expects.
            "model": "OpenAI",
            "project": "Project 1"
        }
        
        return requirement

    except Exception as e:
        logger.error(f"Error fetching requirement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.get("/requirements/{requirement_id}/related-stories")
async def get_related_stories(requirement_id: int):
    # Semantic similarity over the requirement embeddings (pgvector cosine) — returns
    # genuinely related tickets for ANY data. Replaces the old functionality/sprint
    # exact-match, which returned the same arbitrary rows because the functionality
    # column is left empty at ingest.
    try:
        conn = get_pg_conn()
        try:
            related_stories = find_related_requirements(conn, requirement_id, top_k=5)
        except LookupError:
            logger.error(f"Requirement {requirement_id} not found")
            raise HTTPException(status_code=404, detail="Requirement not found")
        logger.info(f"Found {len(related_stories)} related stories for {requirement_id}")
        return related_stories
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding related stories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()

@app.get("/requirements/{requirement_id}/test-cases")
async def get_test_cases(requirement_id: int):
    try:
        conn = get_pg_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_story, description, functionality
            FROM requirements
            WHERE id = %s
        """, (requirement_id,))
        row = cur.fetchone()
        if not row:
            logger.error(f"Requirement {requirement_id} not found")
            raise HTTPException(status_code=404, detail="Requirement not found")
        raw_requirement = [{
            "story_number": row[0],
            "user_story": row[1] or "",
            "description": row[2] or "",
            "functionality": row[3] or ""
        }]
        logger.info(f"Calling TestAgent for requirement: {raw_requirement}")
        test_agent = TestAgent()
        test_cases = test_agent.run(raw_requirements=raw_requirement)

        # Call RelationAgent to get coverage %
        relation_agent = RelationAgent()
        rel_output = relation_agent.run(user_stories=raw_requirement, test_cases=test_cases)
        test_case_relations = rel_output.get('test_case_to_story_relations', {})

        # Add coverage % and relationship % to each test case
        for tc in test_cases:
            tc_id = tc.get('test_case_id') or tc.get('id')
            tc['coverage'] = test_case_relations.get(tc_id, 0)
            # Add relationship % if available
            if 'relationship' not in tc:
                tc['relationship'] = test_case_relations.get(tc_id, 0)

        logger.info(f"Returning {len(test_cases)} test cases from TestAgent with coverage % and relationship %")
        return test_cases
    except Exception as e:
        logger.error(f"Error in get_test_cases: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# Initialize database tables when server starts
@app.on_event("startup")
async def startup_event():
    try:
        conn = get_pg_conn()
        create_tables(conn)
        conn.close()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")