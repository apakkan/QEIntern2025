#!/bin/bash

# Setup signal handlers
trap 'kill -TERM $PID' TERM INT

# Install PostgreSQL client tools first
echo "Installing PostgreSQL client tools..."
apt-get update && apt-get install -y postgresql-client curl

# Wait for database to be ready with more verbose output
echo "Waiting for database..."
until PGPASSWORD=${POSTGRES_PASSWORD} pg_isready -h qeintern2025_db -U postgres -d ${POSTGRES_DB} -p 5432; do
    echo "Database is unavailable - sleeping"
    echo "Trying to connect to PostgreSQL at qeintern2025_db:5432 as postgres user"
    sleep 5
done

echo "Database is up - executing command"

# Initialize database
echo "Starting database initialization..."
python init_db.py

echo "Starting FastAPI server..."
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload &
PID=$!

wait $PID
exit $?