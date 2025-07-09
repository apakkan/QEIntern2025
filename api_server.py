from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
import logging
from database.embedding_utils import get_embedding

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

@app.get("/requirements/")
async def get_requirements():
    try:
        conn = get_pg_conn()
        cur = conn.cursor()
        
        logger.info("Fetching requirements...")
        cur.execute("""
            SELECT 
                id,
                user_story,
                description,
                functionality,
                release,
                priority,
                model,
                project
            FROM requirements;
        """)
        
        rows = cur.fetchall()
        logger.info(f"Found {len(rows)} requirements")
        
        requirements = []
        for row in rows:
            requirement = {
                "id": row[0],
                "user_story": row[1] or "",
                "description": row[2] or "",
                "functionality": row[3] or "",
                "release": row[4] or "",
                "priority": row[5] or "",
                "model": row[6] or "",
                "project": row[7] or ""
            }
            logger.info(f"Requirement {requirement['id']} release value: {requirement['release']}")
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
        # Make sure to use the exact column names from your database schema
        cur.execute("""
            INSERT INTO requirements 
            (id, user_story, description, functionality, release, priority, model, project)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            requirement['id'],
            requirement['user_story'],
            requirement['description'],
            requirement['functionality'],
            requirement['release'],      # This matches the database column
            requirement['priority'],     # This matches the database column
            requirement['model'],
            requirement['project']
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
        
        logger.info(f"Fetching requirement with ID: {requirement_id}")
        cur.execute("""
            SELECT 
                id,
                user_story,
                description,
                functionality,
                release,
                priority,
                model,
                project
            FROM requirements
            WHERE id = %s;
        """, (requirement_id,))
        
        row = cur.fetchone()
        if not row:
            logger.error(f"Requirement not found with ID: {requirement_id}")
            raise HTTPException(status_code=404, detail="Requirement not found")
            
        requirement = {
            "id": row[0],
            "user_story": row[1] or "",
            "description": row[2] or "",
            "functionality": row[3] or "",
            "release": row[4] or "",
            "priority": row[5] or "",
            "model": row[6] or "",
            "project": row[7] or ""
        }
        
        logger.info(f"Found requirement: {requirement}")
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
    try:
        conn = get_pg_conn()
        cur = conn.cursor()
        
        # First verify the requirement exists and get its details
        cur.execute("""
            SELECT 
                user_story,
                description,
                COALESCE(functionality, '') as functionality,
                COALESCE(project, 'Core System') as project
            FROM requirements 
            WHERE id = %s
        """, (requirement_id,))
        
        current_req = cur.fetchone()
        if not current_req:
            logger.error(f"Requirement {requirement_id} not found")
            raise HTTPException(status_code=404, detail="Requirement not found")
        
        current_functionality = current_req[2]
        current_project = current_req[3]
        
        logger.info(f"Finding stories related to functionality '{current_functionality}' and project '{current_project}'")
        
        # Find related stories with NULL handling
        cur.execute("""
            SELECT 
                id,
                user_story,
                description,
                COALESCE(functionality, '') as functionality,
                COALESCE(project, 'Core System') as project
            FROM requirements 
            WHERE id != %s
            AND (
                COALESCE(functionality, '') = %s 
                OR COALESCE(project, 'Core System') = %s
            )
            LIMIT 5
        """, (requirement_id, current_functionality, current_project))
        
        related = cur.fetchall()
        related_stories = []
        
        for row in related:
            # Calculate relationship score
            relationship_score = 0
            if row[3] == current_functionality and current_functionality:
                relationship_score += 80
            if row[4] == current_project:
                relationship_score += 60
            
            relationship_score = min(relationship_score, 100)
            
            story = {
                "id": row[0],
                "name": row[1] or "Untitled",
                "description": row[2] or "No description",
                "relationship": relationship_score
            }
            related_stories.append(story)
        
        logger.info(f"Found {len(related_stories)} related stories")
        return related_stories
        
    except Exception as e:
        logger.error(f"Error finding related stories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()